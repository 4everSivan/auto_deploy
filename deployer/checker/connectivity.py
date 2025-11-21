"""
SSH connectivity checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus
from common.exceptions import ConnectionException


class ConnectivityChecker(BaseChecker):
    """Check SSH connectivity to the node."""
    
    def check(self) -> CheckResult:
        """Check if SSH connection can be established."""
        try:
            self.logger.debug(
                f'Testing SSH connectivity to {self.node_config.host}:{self.node_config.port}',
                node=self.node_config.name
            )
            
            # Test connection
            self.ansible.test_connection(
                host=self.node_config.host,
                user=self.node_config.owner_user,
                password=self.node_config.owner_pass,
                ssh_key=self.node_config.owner_key,
                port=self.node_config.port,
                node_name=self.node_config.name
            )
            
            return CheckResult(
                name='SSH Connectivity',
                status=CheckStatus.PASSED,
                message=f'Successfully connected to {self.node_config.host}:{self.node_config.port}',
                details={
                    'host': self.node_config.host,
                    'port': self.node_config.port,
                    'user': self.node_config.owner_user
                }
            )
            
        except ConnectionException as e:
            return CheckResult(
                name='SSH Connectivity',
                status=CheckStatus.FAILED,
                message=f'Failed to connect: {e}',
                details={'error': str(e)}
            )
        except Exception as e:
            return CheckResult(
                name='SSH Connectivity',
                status=CheckStatus.FAILED,
                message=f'Unexpected error: {e}',
                details={'error': str(e)}
            )
