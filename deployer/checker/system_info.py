"""
System information checker.
"""

from deployer.checker.base import BaseChecker, CheckResult, CheckStatus


class SystemInfoChecker(BaseChecker):
    """Gather system information."""
    
    def check(self) -> CheckResult:
        """Gather basic system information."""
        try:
            info = {}
            
            # Get OS info
            result = self.run_command('cat /etc/os-release', become=False)
            if result['rc'] == 0:
                for line in result['stdout'].split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        info[key.lower()] = value.strip('"')
            
            # Get kernel version
            result = self.run_command('uname -r', become=False)
            if result['rc'] == 0:
                info['kernel'] = result['stdout'].strip()
            
            # Get CPU info
            result = self.run_command('nproc', become=False)
            if result['rc'] == 0:
                info['cpu_cores'] = int(result['stdout'].strip())
            
            # Get total memory
            result = self.run_command("free -m | grep Mem | awk '{print $2}'", become=False)
            if result['rc'] == 0:
                info['total_memory_mb'] = int(result['stdout'].strip())
            
            return CheckResult(
                name='System Info',
                status=CheckStatus.PASSED,
                message=f"System: {info.get('pretty_name', 'Unknown')}, Kernel: {info.get('kernel', 'Unknown')}",
                details=info
            )
            
        except Exception as e:
            return CheckResult(
                name='System Info',
                status=CheckStatus.WARNING,
                message=f'Could not gather full system info: {e}',
                details={'error': str(e)}
            )
