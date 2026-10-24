
"""Strictly validate and execute generated ingress rollback calls."""

import ast
import ipaddress


_ALLOWED_KEYWORDS = {"GroupId", "IpPermissions"}


def _validate_rollback_source(source: str) -> dict:
    """Accept exactly one literal revoke_security_group_ingress call."""

    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise ValueError("Invalid Python source.") from exc

    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
        raise ValueError("Only one expression is permitted.")

    call = tree.body[0].value

    if not isinstance(call, ast.Call):
        raise ValueError("Only a function call is permitted.")

    if not isinstance(call.func, ast.Attribute):
        raise ValueError("Only the approved client method is permitted.")

    if (
        not isinstance(call.func.value, ast.Name)
        or call.func.value.id != "client"
        or call.func.attr != "revoke_security_group_ingress"
    ):
        raise ValueError("Unapproved function call.")

    if call.args:
        raise ValueError("Positional arguments are not permitted.")

    keyword_names = [keyword.arg for keyword in call.keywords]
    if (
        any(name is None for name in keyword_names)
        or set(keyword_names) != _ALLOWED_KEYWORDS
        or len(keyword_names) != len(_ALLOWED_KEYWORDS)
    ):
        raise ValueError("Unexpected or missing keyword arguments.")

    try:
        values = {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in call.keywords
        }
    except (ValueError, TypeError, SyntaxError) as exc:
        raise ValueError("Arguments must contain literals only.") from exc

    group_id = values["GroupId"]
    permissions = values["IpPermissions"]

    if not isinstance(group_id, str) or not group_id.startswith("sg-"):
        raise ValueError("Invalid security group ID.")

    if not isinstance(permissions, list) or len(permissions) != 1:
        raise ValueError("Exactly one ingress permission is required.")

    permission = permissions[0]
    if not isinstance(permission, dict):
        raise ValueError("Invalid ingress permission.")

    if set(permission) != {"IpProtocol", "FromPort", "ToPort", "IpRanges"}:
        raise ValueError("Unexpected ingress permission fields.")

    protocol = permission["IpProtocol"]
    start_port = permission["FromPort"]
    end_port = permission["ToPort"]
    ranges = permission["IpRanges"]

    if protocol not in {"tcp", "udp"}:
        raise ValueError("Only TCP and UDP are permitted.")

    if (
        type(start_port) is not int
        or type(end_port) is not int
        or not 0 <= start_port <= end_port <= 65535
    ):
        raise ValueError("Invalid port range.")

    if not isinstance(ranges, list) or len(ranges) != 1:
        raise ValueError("Exactly one IPv4 CIDR range is required.")

    if not isinstance(ranges[0], dict) or set(ranges[0]) != {"CidrIp"}:
        raise ValueError("Invalid CIDR range structure.")

    try:
        network = ipaddress.ip_network(ranges[0]["CidrIp"], strict=False)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid IPv4 CIDR.") from exc

    if network.version != 4:
        raise ValueError("Only IPv4 CIDRs are permitted.")

    return values


def execute_rollback(source: str, client):
    """
    Validate generated source and execute its approved API call.

    The client must be explicitly supplied by the caller.
    Start with a mock client; do not pass a live AWS client.
    """
    _validate_rollback_source(source)

    # AST validation restricts source to one approved call with
    # literal arguments. No imports, built-ins, assignments,
    # attribute chains, or additional statements are accepted.
    namespace = {
        "__builtins__": {},
        "client": client,
    }

    exec(compile(source, "<aerodrift-rollback>", "exec"), namespace, {})
