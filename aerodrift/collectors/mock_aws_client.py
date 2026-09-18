import json
from pathlib import Path


class MockAWSClient:
    """
    Mock implementation of common boto3 EC2 API calls.

    This allows AeroDrift to develop and test its
    ingestion pipeline without requiring AWS credentials.
    """

    def __init__(self, mock_file: str = "mock_data/aws_state.json"):
        self.mock_file = Path(mock_file)

        with self.mock_file.open("r", encoding="utf-8") as file:
            self.state = json.load(file)

    def describe_vpcs(self) -> dict:
        return {
            "Vpcs": [
                {
                    "VpcId": vpc["vpc_id"],
                    "CidrBlock": vpc["cidr_block"],
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": vpc["name"],
                        }
                    ],
                }
                for vpc in self.state["vpcs"]
            ]
        }

    def describe_subnets(self) -> dict:
        return {
            "Subnets": [
                {
                    "SubnetId": subnet["subnet_id"],
                    "VpcId": subnet["vpc_id"],
                    "CidrBlock": subnet["cidr_block"],
                    "Tags": [
                        {
                            "Key": "Type",
                            "Value": subnet["type"],
                        }
                    ],
                }
                for subnet in self.state["subnets"]
            ]
        }

    def describe_instances(self) -> dict:
        return {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": instance["instance_id"],
                            "SubnetId": instance["subnet_id"],
                            "PrivateIpAddress": instance["private_ip"],
                            "Tags": [
                                {
                                    "Key": "Name",
                                    "Value": instance["name"],
                                }
                            ],
                        }
                        for instance in self.state["ec2_instances"]
                    ]
                }
            ]
        }

    def describe_security_groups(self) -> dict:
        return {
            "SecurityGroups": [
                {
                    "GroupId": group["group_id"],
                    "VpcId": group["vpc_id"],
                    "GroupName": group["name"],
                    "IpPermissions": [
                        {
                            "IpProtocol": rule["protocol"],
                            "FromPort": rule["port"],
                            "ToPort": rule["port"],
                            "IpRanges": [
                                {
                                    "CidrIp": rule["source"],
                                }
                            ],
                        }
                        for rule in group["ingress"]
                    ],
                }
                for group in self.state["security_groups"]
            ]
        }