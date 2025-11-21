"""
Memory checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class MemoryChecker(BaseChecker):
    """Check available memory."""
    
    def __init__(self, *args, min_memory_mb: int = 512, **kwargs):
        """
        Initialize memory checker.
        
        Args:
            min_memory_mb: Minimum required memory in MB
        """
        super().__init__(*args, **kwargs)
        self.min_memory_mb = min_memory_mb
    
    def check(self) -> CheckResult:
        """Check if sufficient memory is available."""
        try:
            # Check available memory
            result = self.run_command(
                "free -m | grep Mem | awk '{print $7}'",
                become=False
            )
            
            if result['rc'] != 0:
                return CheckResult(
                    name='Memory',
                    status=CheckStatus.FAILED,
                    message='Failed to check memory',
                    details={'error': result.get('stderr', 'Unknown error')}
                )
            
            # Parse available memory
            available_mb = int(result['stdout'].strip())
            
            if available_mb >= self.min_memory_mb:
                return CheckResult(
                    name='Memory',
                    status=CheckStatus.PASSED,
                    message=f'Sufficient memory: {available_mb}MB available (required: {self.min_memory_mb}MB)',
                    details={
                        'available_mb': available_mb,
                        'required_mb': self.min_memory_mb
                    }
                )
            else:
                return CheckResult(
                    name='Memory',
                    status=CheckStatus.WARNING,
                    message=f'Low memory: {available_mb}MB available (recommended: {self.min_memory_mb}MB)',
                    details={
                        'available_mb': available_mb,
                        'required_mb': self.min_memory_mb
                    }
                )
                
        except Exception as e:
            return CheckResult(
                name='Memory',
                status=CheckStatus.FAILED,
                message=f'Error checking memory: {e}',
                details={'error': str(e)}
            )
