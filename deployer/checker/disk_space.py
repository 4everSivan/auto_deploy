"""
Disk space checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class DiskSpaceChecker(BaseChecker):
    """Check available disk space."""
    
    def __init__(self, *args, min_space_mb: int = 1024, **kwargs):
        """
        Initialize disk space checker.
        
        Args:
            min_space_mb: Minimum required space in MB
        """
        super().__init__(*args, **kwargs)
        self.min_space_mb = min_space_mb
    
    def check(self) -> CheckResult:
        """Check if sufficient disk space is available."""
        try:
            # Check disk space on root partition
            result = self.run_command(
                "df -BM / | tail -1 | awk '{print $4}'",
                become=False
            )
            
            if result['rc'] != 0:
                return CheckResult(
                    name='Disk Space',
                    status=CheckStatus.FAILED,
                    message='Failed to check disk space',
                    details={'error': result.get('stderr', 'Unknown error')}
                )
            
            # Parse available space
            available_str = result['stdout'].strip().replace('M', '')
            available_mb = int(available_str)
            
            if available_mb >= self.min_space_mb:
                return CheckResult(
                    name='Disk Space',
                    status=CheckStatus.PASSED,
                    message=f'Sufficient disk space: {available_mb}MB available (required: {self.min_space_mb}MB)',
                    details={
                        'available_mb': available_mb,
                        'required_mb': self.min_space_mb
                    }
                )
            else:
                return CheckResult(
                    name='Disk Space',
                    status=CheckStatus.FAILED,
                    message=f'Insufficient disk space: {available_mb}MB available (required: {self.min_space_mb}MB)',
                    details={
                        'available_mb': available_mb,
                        'required_mb': self.min_space_mb
                    }
                )
                
        except Exception as e:
            return CheckResult(
                name='Disk Space',
                status=CheckStatus.FAILED,
                message=f'Error checking disk space: {e}',
                details={'error': str(e)}
            )
