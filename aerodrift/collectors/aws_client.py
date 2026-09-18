from abc import ABC, abstractmethod
from typing import Any


class AWSClient(ABC):
    """
    Interface for AWS API clients.

    Both the real boto3 client and the mock client
    can implement this interface.
    """

    @abstractmethod
    def describe_vpcs(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def describe_subnets(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def describe_instances(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def describe_security_groups(self) -> dict[str, Any]:
        pass