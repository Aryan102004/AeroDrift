import pytest

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.models.resources import (
    VPC,
    Subnet,
    EC2Instance,
    SecurityGroup,
)


@pytest.fixture
def collector():
    client = MockAWSClient()
    return AWSCollector(client)


@pytest.mark.asyncio
async def test_collect_vpcs(collector):
    vpcs = await collector.collect_vpcs()

    assert len(vpcs) == 1
    assert isinstance(vpcs[0], VPC)
    assert vpcs[0].vpc_id == "vpc-001"


@pytest.mark.asyncio
async def test_collect_subnets(collector):
    subnets = await collector.collect_subnets()

    assert len(subnets) == 2
    assert all(
        isinstance(subnet, Subnet)
        for subnet in subnets
    )


@pytest.mark.asyncio
async def test_collect_ec2_instances(collector):
    instances = await collector.collect_ec2_instances()

    assert len(instances) == 2
    assert all(
        isinstance(instance, EC2Instance)
        for instance in instances
    )


@pytest.mark.asyncio
async def test_collect_security_groups(collector):
    security_groups = await collector.collect_security_groups()

    assert len(security_groups) == 2
    assert all(
        isinstance(group, SecurityGroup)
        for group in security_groups
    )


@pytest.mark.asyncio
async def test_collect_all(collector):
    state = await collector.collect_all()

    assert "vpcs" in state
    assert "subnets" in state
    assert "ec2_instances" in state
    assert "security_groups" in state

    assert len(state["vpcs"]) == 1
    assert len(state["subnets"]) == 2
    assert len(state["ec2_instances"]) == 2
    assert len(state["security_groups"]) == 2