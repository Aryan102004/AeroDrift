import asyncio

from aerodrift.models.resources import (
    VPC,
    Subnet,
    EC2Instance,
    SecurityGroup,
    IngressRule,
)


class AWSCollector:
    """
    Asynchronous AWS state collector.

    The collector accepts a boto3-compatible client.
    Week 1 uses MockAWSClient so that the system can
    operate without real AWS credentials.
    """

    def __init__(self, client):
        self.client = client

    async def collect_vpcs(self) -> list[VPC]:
        response = await asyncio.to_thread(
            self.client.describe_vpcs
        )

        vpcs = []

        for vpc in response["Vpcs"]:
            name = vpc["VpcId"]

            for tag in vpc.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            vpcs.append(
                VPC(
                    vpc_id=vpc["VpcId"],
                    cidr_block=vpc["CidrBlock"],
                    name=name,
                )
            )

        return vpcs

    async def collect_subnets(self) -> list[Subnet]:
        response = await asyncio.to_thread(
            self.client.describe_subnets
        )

        subnets = []

        for subnet in response["Subnets"]:
            subnet_type = "unknown"

            for tag in subnet.get("Tags", []):
                if tag["Key"] == "Type":
                    subnet_type = tag["Value"]

            subnets.append(
                Subnet(
                    subnet_id=subnet["SubnetId"],
                    vpc_id=subnet["VpcId"],
                    cidr_block=subnet["CidrBlock"],
                    subnet_type=subnet_type,
                )
            )

        return subnets

    async def collect_ec2_instances(self) -> list[EC2Instance]:
        response = await asyncio.to_thread(
            self.client.describe_instances
        )

        instances = []

        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:

                name = instance["InstanceId"]

                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]

                security_group_ids = [
                    group["GroupId"]
                    for group in instance.get(
                        "SecurityGroups",
                        [],
                    )
                ]

                instances.append(
                    EC2Instance(
                        instance_id=instance["InstanceId"],
                        subnet_id=instance["SubnetId"],
                        private_ip=instance["PrivateIpAddress"],
                        name=name,
                        security_group_ids=security_group_ids,
                    )
                )

        return instances

    async def collect_security_groups(
        self,
    ) -> list[SecurityGroup]:

        response = await asyncio.to_thread(
            self.client.describe_security_groups
        )

        security_groups = []

        for group in response["SecurityGroups"]:

            ingress_rules = []

            for permission in group.get(
                "IpPermissions",
                [],
            ):

                protocol = permission["IpProtocol"]

                port = permission.get(
                    "FromPort",
                    0,
                )

                for ip_range in permission.get(
                    "IpRanges",
                    [],
                ):
                    ingress_rules.append(
                        IngressRule(
                            protocol=protocol,
                            port=port,
                            source=ip_range["CidrIp"],
                        )
                    )

            security_groups.append(
                SecurityGroup(
                    group_id=group["GroupId"],
                    vpc_id=group["VpcId"],
                    name=group["GroupName"],
                    ingress=ingress_rules,
                )
            )

        return security_groups

    async def collect_all(self) -> dict:
        """
        Collect all supported AWS resources concurrently.
        """

        (
            vpcs,
            subnets,
            ec2_instances,
            security_groups,
        ) = await asyncio.gather(
            self.collect_vpcs(),
            self.collect_subnets(),
            self.collect_ec2_instances(),
            self.collect_security_groups(),
        )

        return {
            "vpcs": vpcs,
            "subnets": subnets,
            "ec2_instances": ec2_instances,
            "security_groups": security_groups,
        }