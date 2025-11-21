"""
Base classes for pre-installation checkers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

from deployer.models import NodeConfig
from deployer.ansible_wrapper import AnsibleWrapper
from common.logger import DeployLogger


class CheckStatus(Enum):
    """Check result status."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckResult:
    """Result of a single check."""
    
    def __init__(
        self,
        name: str,
        status: CheckStatus,
        message: str,
        details: Dict[str, Any] = None
    ):
        """
        Initialize check result.
        
        Args:
            name: Check name
            status: Check status
            message: Result message
            details: Additional details
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'details': self.details
        }
    
    def __repr__(self) -> str:
        return f"CheckResult(name={self.name}, status={self.status.value}, message={self.message})"


class BaseChecker(ABC):
    """Abstract base class for pre-installation checkers."""
    
    def __init__(
        self,
        node_config: NodeConfig,
        ansible_wrapper: AnsibleWrapper,
        logger: DeployLogger
    ):
        """
        Initialize checker.
        
        Args:
            node_config: Node configuration
            ansible_wrapper: Ansible wrapper instance
            logger: Logger instance
        """
        self.node_config = node_config
        self.ansible = ansible_wrapper
        self.logger = logger
    
    @abstractmethod
    def check(self) -> CheckResult:
        """
        Perform the check.
        
        Returns:
            CheckResult object
        """
        pass
    
    def run_command(self, command: str, become: bool = False) -> Dict[str, Any]:
        """
        Run a command on the node.
        
        Args:
            command: Command to execute
            become: Whether to use privilege escalation
            
        Returns:
            Command execution results
        """
        return self.ansible.run_command(
            host=self.node_config.host,
            command=command,
            user=self.node_config.owner_user,
            password=self.node_config.owner_pass,
            ssh_key=self.node_config.owner_key,
            port=self.node_config.port,
            become=become,
            become_user=self.node_config.super_user,
            become_password=self.node_config.super_pass,
            node_name=self.node_config.name
        )


class CheckerManager:
    """Manager for running multiple checkers."""
    
    def __init__(
        self,
        node_config: NodeConfig,
        ansible_wrapper: AnsibleWrapper,
        logger: DeployLogger
    ):
        """
        Initialize checker manager.
        
        Args:
            node_config: Node configuration
            ansible_wrapper: Ansible wrapper instance
            logger: Logger instance
        """
        self.node_config = node_config
        self.ansible = ansible_wrapper
        self.logger = logger
        self.checkers: List[BaseChecker] = []
    
    def add_checker(self, checker: BaseChecker) -> None:
        """
        Add a checker to the manager.
        
        Args:
            checker: Checker instance
        """
        self.checkers.append(checker)
    
    def run_all(self) -> Dict[str, Any]:
        """
        Run all registered checkers.
        
        Returns:
            Dictionary with all check results
        """
        self.logger.info(
            f'Running {len(self.checkers)} pre-installation checks',
            node=self.node_config.name
        )
        
        results = []
        passed = 0
        warnings = 0
        failed = 0
        skipped = 0
        
        for checker in self.checkers:
            try:
                result = checker.check()
                results.append(result.to_dict())
                
                if result.status == CheckStatus.PASSED:
                    passed += 1
                    self.logger.info(
                        f'✓ {result.name}: {result.message}',
                        node=self.node_config.name
                    )
                elif result.status == CheckStatus.WARNING:
                    warnings += 1
                    self.logger.warning(
                        f'⚠ {result.name}: {result.message}',
                        node=self.node_config.name
                    )
                elif result.status == CheckStatus.FAILED:
                    failed += 1
                    self.logger.error(
                        f'✗ {result.name}: {result.message}',
                        node=self.node_config.name
                    )
                else:  # SKIPPED
                    skipped += 1
                    self.logger.debug(
                        f'- {result.name}: {result.message}',
                        node=self.node_config.name
                    )
                    
            except Exception as e:
                self.logger.exception(
                    f'Error running checker {checker.__class__.__name__}: {e}',
                    node=self.node_config.name
                )
                results.append({
                    'name': checker.__class__.__name__,
                    'status': CheckStatus.FAILED.value,
                    'message': f'Check failed with error: {e}',
                    'details': {}
                })
                failed += 1
        
        summary = {
            'total': len(self.checkers),
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'skipped': skipped,
            'results': results
        }
        
        self.logger.info(
            f'Checks completed: {passed} passed, {warnings} warnings, {failed} failed, {skipped} skipped',
            node=self.node_config.name
        )
        
        return summary
