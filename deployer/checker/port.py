"""
Port availability checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class PortAvailabilityChecker(BaseChecker):
    """Check if required ports are available."""
    
    def __init__(self, *args, ports: list = None, **kwargs):
        """
        Initialize port availability checker.
        
        Args:
            ports: List of ports to check
        """
        super().__init__(*args, **kwargs)
        self.ports = ports or []
    
    def check(self) -> CheckResult:
        """Check if required ports are available."""
        if not self.ports:
            return CheckResult(
                name='Port Availability',
                status=CheckStatus.SKIPPED,
                message='No ports to check',
                details={}
            )
        
        try:
            occupied_ports = []
            
            for port in self.ports:
                # Check if port is in use
                result = self.run_command(
                    f"netstat -tuln | grep ':{port} ' || echo 'free'",
                    become=True
                )
                
                if result['rc'] == 0 and 'free' not in result['stdout']:
                    occupied_ports.append(port)
            
            if not occupied_ports:
                return CheckResult(
                    name='Port Availability',
                    status=CheckStatus.PASSED,
                    message=f'All required ports are available: {self.ports}',
                    details={'ports': self.ports, 'occupied': []}
                )
            else:
                return CheckResult(
                    name='Port Availability',
                    status=CheckStatus.WARNING,
                    message=f'Some ports are occupied: {occupied_ports}',
                    details={'ports': self.ports, 'occupied': occupied_ports}
                )
                
        except Exception as e:
            return CheckResult(
                name='Port Availability',
                status=CheckStatus.FAILED,
                message=f'Error checking ports: {e}',
                details={'error': str(e)}
            )
