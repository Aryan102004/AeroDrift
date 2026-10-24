
import pytest

from aerodrift.remediation.generator import (
    IngressRuleFinding,
    generate_rollback_code,
)


def make_finding(**overrides):
    values = {
        "group_id": "sg-web-001",
        "protocol": "tcp",
        "from_port": 8080,
        "to_port": 8080,
        "source": "0.0.0.0/0",
    }
    values.update(overrides)
    return IngressRuleFinding(**values)


def test_generates_correct_rollback_call():
    code = generate_rollback_code(make_finding())

    assert "client.revoke_security_group_ingress(" in code
    assert "GroupId='sg-web-001'" in code
    assert "'IpProtocol': 'tcp'" in code
    assert "'FromPort': 8080" in code
    assert "'ToPort': 8080" in code
    assert "'CidrIp': '0.0.0.0/0'" in code


def test_generates_specific_port_range():
    code = generate_rollback_code(
        make_finding(from_port=8000, to_port=8090)
    )

    assert "'FromPort': 8000" in code
    assert "'ToPort': 8090" in code


def test_rejects_invalid_security_group_id():
    with pytest.raises(ValueError, match="security group"):
        generate_rollback_code(
            make_finding(group_id="invalid-group")
        )


def test_rejects_unsupported_protocol():
    with pytest.raises(ValueError, match="TCP and UDP"):
        generate_rollback_code(
            make_finding(protocol="-1")
        )


def test_rejects_invalid_port_range():
    with pytest.raises(ValueError, match="port range"):
        generate_rollback_code(
            make_finding(from_port=9000, to_port=8000)
        )


def test_rejects_invalid_cidr():
    with pytest.raises(ValueError, match="IPv4 CIDR"):
        generate_rollback_code(
            make_finding(source="not-a-cidr")
        )


def test_rejects_ipv6_source():
    with pytest.raises(ValueError, match="IPv4 CIDR"):
        generate_rollback_code(
            make_finding(source="::/0")
        )
