from dataclasses import dataclass, field
from typing import List


@dataclass
class VPC:
    vpc_id: str
    cidr_block: str
    name: str


@dataclass
class Subnet:
    subnet_id: str
    vpc_id: str
    cidr_block: str
    subnet_type: str


@dataclass
class EC2Instance:
    instance_id: str
    subnet_id: str
    private_ip: str
    name: str


@dataclass
class IngressRule:
    protocol: str
    port: int
    source: str


@dataclass
class SecurityGroup:
    group_id: str
    vpc_id: str
    name: str
    ingress: List[IngressRule] = field(default_factory=list)