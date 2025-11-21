"""
Sudo privilege checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class SudoPrivilegeChecker(BaseChecker):
    """Check if user has sudo privileges."""
    
    def check(self) -> CheckResult:
        """Check sudo privileges."""
        try:
            # Try to run a simple command with sudo
            result = self.run_command('whoami', become=True)
            
            if result['rc'] == 0:
                sudo_user = result['stdout'].strip()
                if sudo_user == self.node_config.super_user:
                    return CheckResult(
                        name='Sudo Privileges',
                        status=CheckStatus.PASSED,
                        message=f'Sudo privileges confirmed (running as {sudo_user})',
                        details={'sudo_user': sudo_user}
                    )
                else:
                    return CheckResult(
                        name='Sudo Privileges',
                        status=CheckStatus.WARNING,
                        message=f'Sudo works but running as {sudo_user} instead of {self.node_config.super_user}',
                        details={'sudo_user': sudo_user, 'expected': self.node_config.super_user}
                    )
            else:
                return CheckResult(
                    name='Sudo Privileges',
                    status=CheckStatus.FAILED,
                    message='Failed to execute command with sudo',
                    details={'error': result.get('stderr', 'Unknown error')}
                )
                
        except Exception as e:
            return CheckResult(
                name='Sudo Privileges',
                status=CheckStatus.FAILED,
                message=f'Error checking sudo privileges: {e}',
                details={'error': str(e)}
            )
