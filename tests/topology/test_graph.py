import pytest
import pytest_asyncio

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.topology.graph import CloudTopology


@pytest_asyncio.fixture
async def aws_state():
    client = MockAWSClient()
    collector = AWSCollector(client)

    return await collector.collect_all()


@pytest.mark.asyncio
async def test_graph_nodes(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.number_of_nodes() == 8


@pytest.mark.asyncio
async def test_graph_edges(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.number_of_edges() == 9


@pytest.mark.asyncio
async def test_vpc_subnet_relationship(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.has_edge(
        "vpc-001",
        "subnet-public-001",
    )

    assert graph.has_edge(
        "vpc-001",
        "subnet-private-001",
    )


@pytest.mark.asyncio
async def test_subnet_ec2_relationship(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.has_edge(
        "subnet-public-001",
        "i-web-001",
    )

    assert graph.has_edge(
        "subnet-private-001",
        "i-app-001",
    )


@pytest.mark.asyncio
async def test_vpc_security_group_relationship(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.has_edge(
        "vpc-001",
        "sg-web-001",
    )

    assert graph.has_edge(
        "vpc-001",
        "sg-app-001",
    )


@pytest.mark.asyncio
async def test_internet_public_subnet_relationship(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.has_edge(
        "internet",
        "subnet-public-001",
    )


@pytest.mark.asyncio
async def test_security_group_ec2_relationship(aws_state):
    topology = CloudTopology()
    graph = topology.build(aws_state)

    assert graph.has_edge(
        "sg-web-001",
        "i-web-001",
    )

    assert graph.has_edge(
        "sg-app-001",
        "i-app-001",
    )


@pytest.mark.asyncio
async def test_internet_to_web_path(aws_state):
    topology = CloudTopology()
    topology.build(aws_state)

    assert topology.has_path(
        "internet",
        "i-web-001",
    )


@pytest.mark.asyncio
async def test_internet_to_private_app_path(aws_state):
    topology = CloudTopology()
    topology.build(aws_state)

    assert not topology.has_path(
        "internet",
        "i-app-001",
    )


@pytest.mark.asyncio
async def test_get_internet_to_web_path(aws_state):
    topology = CloudTopology()
    topology.build(aws_state)

    path = topology.get_path(
        "internet",
        "i-web-001",
    )

    assert path == [
        "internet",
        "subnet-public-001",
        "i-web-001",
    ]