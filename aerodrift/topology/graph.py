import networkx as nx


class CloudTopology:
    """
    Directed graph representing AWS cloud topology
    and basic network pathways.
    """

    INTERNET_NODE = "internet"

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_vpc(self, vpc):
        self.graph.add_node(
            vpc.vpc_id,
            resource_type="vpc",
            name=vpc.name,
            cidr_block=vpc.cidr_block,
        )

    def add_subnet(self, subnet):
        self.graph.add_node(
            subnet.subnet_id,
            resource_type="subnet",
            subnet_type=subnet.subnet_type,
            cidr_block=subnet.cidr_block,
        )

        self.graph.add_edge(
            subnet.vpc_id,
            subnet.subnet_id,
            relationship="contains",
        )

        # Public subnets represent an externally reachable
        # network boundary in our Week 1 topology model.
        if subnet.subnet_type.lower() == "public":
            self.graph.add_edge(
                self.INTERNET_NODE,
                subnet.subnet_id,
                relationship="network_access",
            )

    def add_ec2(self, instance):
        self.graph.add_node(
            instance.instance_id,
            resource_type="ec2",
            name=instance.name,
            private_ip=instance.private_ip,
        )

        self.graph.add_edge(
            instance.subnet_id,
            instance.instance_id,
            relationship="network_path",
        )

        # Represent the Security Groups attached to the EC2.
        for security_group_id in instance.security_group_ids:
            self.graph.add_edge(
                security_group_id,
                instance.instance_id,
                relationship="security_control",
            )

    def add_security_group(self, security_group):
        self.graph.add_node(
            security_group.group_id,
            resource_type="security_group",
            name=security_group.name,
        )

        self.graph.add_edge(
            security_group.vpc_id,
            security_group.group_id,
            relationship="contains",
        )

    def build(self, state: dict):
        # External boundary
        self.graph.add_node(
            self.INTERNET_NODE,
            resource_type="external",
            name="Internet",
        )

        for vpc in state["vpcs"]:
            self.add_vpc(vpc)

        for subnet in state["subnets"]:
            self.add_subnet(subnet)

        for security_group in state["security_groups"]:
            self.add_security_group(security_group)

        for instance in state["ec2_instances"]:
            self.add_ec2(instance)

        return self.graph

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def has_path(self, source: str, target: str) -> bool:
        """
        Check whether a directed path exists between two resources.
        """
        return nx.has_path(
            self.graph,
            source,
            target,
        )

    def get_path(self, source: str, target: str) -> list[str]:
        """
        Return the shortest directed path between resources.
        """
        return nx.shortest_path(
            self.graph,
            source,
            target,
        )