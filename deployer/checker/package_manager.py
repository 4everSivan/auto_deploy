"""
Package manager checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class PackageManagerChecker(BaseChecker):
    """Check if package manager is available and working."""
    
    def check(self) -> CheckResult:
        """Check package manager availability."""
        try:
            # Try apt (Debian/Ubuntu)
            result = self.run_command('which apt-get', become=False)
            if result['rc'] == 0:
                # Test apt-get
                result = self.run_command('apt-get --version', become=True)
                if result['rc'] == 0:
                    return CheckResult(
                        name='Package Manager',
                        status=CheckStatus.PASSED,
                        message='apt-get is available and working',
                        details={'manager': 'apt-get'}
                    )
            
            # Try yum (CentOS/RHEL)
            result = self.run_command('which yum', become=False)
            if result['rc'] == 0:
                result = self.run_command('yum --version', become=True)
                if result['rc'] == 0:
                    return CheckResult(
                        name='Package Manager',
                        status=CheckStatus.PASSED,
                        message='yum is available and working',
                        details={'manager': 'yum'}
                    )
            
            return CheckResult(
                name='Package Manager',
                status=CheckStatus.WARNING,
                message='No supported package manager found (apt-get, yum)',
                details={}
            )
            
        except Exception as e:
            return CheckResult(
                name='Package Manager',
                status=CheckStatus.FAILED,
                message=f'Error checking package manager: {e}',
                details={'error': str(e)}
            )
