import asyncio

from aerodrift.collectors.aws_collector import AWSCollector
from aerodrift.collectors.mock_aws_client import MockAWSClient
from aerodrift.topology.graph import CloudTopology


async def main():
    print("=" * 50)
    print("             AERODRIFT - WEEK 1")
    print("=" * 50)

    print("\n[1] AWS INGESTION")

    client = MockAWSClient()

    collector = AWSCollector(client)

    state = await collector.collect_all()

    print(f"✓ VPCs collected: {len(state['vpcs'])}")
    print(f"✓ Subnets collected: {len(state['subnets'])}")
    print(f"✓ EC2 instances collected: {len(state['ec2_instances'])}")
    print(f"✓ Security groups collected: {len(state['security_groups'])}")

    print("\n[2] TOPOLOGY ENGINE")

    topology = CloudTopology()

    graph = topology.build(state)

    print(f"✓ Graph nodes: {topology.node_count()}")
    print(f"✓ Graph edges: {topology.edge_count()}")

    print("\n[3] GRAPH NODES")

    for node, attributes in graph.nodes(data=True):
        print(
            f"  {node} "
            f"({attributes.get('resource_type')})"
        )

    print("\n[4] GRAPH EDGES")

    for source, target, attributes in graph.edges(data=True):
        print(
            f"  {source} -> {target} "
            f"[{attributes.get('relationship')}]"
        )

    

    print("\n[5] NETWORK PATH ANALYSIS")

    if topology.has_path("internet", "i-web-001"):
        path = topology.get_path(
            "internet",
            "i-web-001",
        )

        print("✓ Internet path detected:")
        print("  " + " -> ".join(path))
    else:
        print("✗ No Internet path to web server.")

    if topology.has_path("internet", "i-app-001"):
        path = topology.get_path(
            "internet",
            "i-app-001",
        )

        print("⚠ Internet path detected to app server:")
        print("  " + " -> ".join(path))
    else:
        print("✓ No Internet path to private app server.")    
    print("\nAeroDrift Week 1 pipeline completed successfully.")
if __name__ == "__main__":
    asyncio.run(main())