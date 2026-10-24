
import pytest

from aerodrift.remediation.generator import (
    IngressRuleFinding,
    generate_rollback_code,
)
from aerodrift.remediation.executor import execute_rollback


class MockRollbackClient:
    def __init__(self):
        self.calls = []

    def revoke_security_group_ingress(self, **kwargs):
        self.calls.append(kwargs)
        return {"Return": True}


def valid_source():
    finding = IngressRuleFinding(
        group_id="sg-web-001",
        protocol="tcp",
        from_port=8080,
        to_port=8080,
        source="0.0.0.0/0",
    )
    return generate_rollback_code(finding)


def test_executes_approved_call_using_mock_client():
    client = MockRollbackClient()

    execute_rollback(valid_source(), client)

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["GroupId"] == "sg-web-001"

    permission = call["IpPermissions"][0]
    assert permission["IpProtocol"] == "tcp"
    assert permission["FromPort"] == 8080
    assert permission["ToPort"] == 8080
    assert permission["IpRanges"] == [{"CidrIp": "0.0.0.0/0"}]


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "print('unexpected')",
        "client.delete_security_group(GroupId='sg-web-001')",
        "client.revoke_security_group_ingress(GroupId='sg-web-001')",
        "client.revoke_security_group_ingress("
        "GroupId='sg-web-001', "
        "IpPermissions=[], "
        "Extra=True)",
        "client.revoke_security_group_ingress("
        "GroupId=__import__('os').getcwd(), "
        "IpPermissions=[])",
    ],
)
def test_rejects_unapproved_source(source):
    client = MockRollbackClient()

    with pytest.raises(ValueError):
        execute_rollback(source, client)

    assert client.calls == []


def test_rejects_multiple_statements():
    client = MockRollbackClient()
    source = valid_source() + "\nclient.delete_security_group(GroupId='sg-x')"

    with pytest.raises(ValueError):
        execute_rollback(source, client)

    assert client.calls == []
