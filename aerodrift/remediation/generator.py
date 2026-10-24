
"""Generate rollback code for explicitly identified ingress rules."""

from dataclasses import dataclass
import ipaddress


@dataclass(frozen=True)
class IngressRuleFinding:
    """A specific ingress rule identified as unauthorized."""

    group_id: str
    protocol: str
    from_port: int
    to_port: int
    source: str


def validate_ingress_finding(finding: IngressRuleFinding) -> None:
    """Reject incomplete or unsupported rollback parameters."""

    if not finding.group_id.startswith("sg-"):
        raise ValueError("Invalid security group ID.")

    if finding.protocol.lower() not in {"tcp", "udp"}:
        raise ValueError("Only TCP and UDP rules are supported.")

    if not (
        0 <= finding.from_port <= finding.to_port <= 65535
    ):
        raise ValueError("Invalid port range.")

    try:
        network = ipaddress.ip_network(finding.source, strict=False)
    except ValueError as exc:
        raise ValueError("Invalid IPv4 CIDR source.") from exc

    if network.version != 4:
        raise ValueError("Only IPv4 CIDR sources are supported.")


def generate_rollback_code(finding: IngressRuleFinding) -> str:
    """
    Generate code to revoke exactly one identified ingress rule.

    The generated code expects an explicitly supplied `client`
    object implementing revoke_security_group_ingress().
    It does not execute the code.
    """

    validate_ingress_finding(finding)

    # repr() safely quotes string values for Python source.
    group_id = repr(finding.group_id)
    protocol = repr(finding.protocol.lower())
    source = repr(
        str(ipaddress.ip_network(finding.source, strict=False))
    )

    return (
        "client.revoke_security_group_ingress(\n"
        f"    GroupId={group_id},\n"
        "    IpPermissions=[\n"
        "        {\n"
        f"            'IpProtocol': {protocol},\n"
        f"            'FromPort': {finding.from_port},\n"
        f"            'ToPort': {finding.to_port},\n"
        "            'IpRanges': [\n"
        f"                {{'CidrIp': {source}}}\n"
        "            ],\n"
        "        }\n"
        "    ],\n"
        ")\n"
    )
