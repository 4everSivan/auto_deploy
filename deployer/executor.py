"""
Deployment execution engine.
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Callable, Optional, Any
import threading

from deployer.config import Config
from deployer.models import NodeConfig, SoftwareConfig
from deployer.task_manager import TaskManager, Task, TaskStatus
from deployer.ansible_wrapper import AnsibleWrapper
from common.logger import DeployLogger
from common.exceptions import DeployException


class DeploymentExecutor:
    """
    Deployment execution engine with multi-threaded node execution.
    """
    
    def __init__(
        self,
        config: Config,
        task_manager: TaskManager,
        logger: DeployLogger
    ):
        """
        Initialize deployment executor.
        
        Args:
            config: Configuration object
            task_manager: Task manager instance
            logger: Logger instance
        """
        self.config = config
        self.task_manager = task_manager
        self.logger = logger
        
        # Thread pool for concurrent node execution
        self.max_workers = config.get_max_concurrent_nodes()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures: Dict[str, Future] = {}
        
        # Ansible wrapper
        self.ansible = AnsibleWrapper(logger)
        
        # Control events
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {}
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event.
        
        Args:
            event: Event name (on_task_start, on_task_complete, etc.)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """
        Trigger callbacks for an event.
        
        Args:
            event: Event name
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback
        """
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f'Callback error for {event}: {e}')
    
    def execute_all(self) -> List[Future]:
        """
        Execute deployment for all nodes concurrently.
        
        Returns:
            List of futures for node executions
        """
        self.logger.info('Starting deployment execution')
        
        nodes = self.config.get_nodes()
        futures = []
        
        for node in nodes:
            if self.stop_event.is_set():
                self.logger.warning('Deployment stopped before all nodes started')
                break
            
            future = self.executor.submit(self._execute_node, node)
            self.futures[node.name] = future
            futures.append(future)
            
            self.logger.info(f'Submitted node {node.name} for execution')
        
        return futures
    
    def _execute_node(self, node: NodeConfig) -> None:
        """
        Execute deployment for a single node.
        
        Args:
            node: Node configuration
        """
        self.logger.info(f'Starting deployment for node {node.name}', node=node.name)
        
        tasks = self.task_manager.get_node_tasks(node.name)
        
        for task in tasks:
            # Check pause and stop events
            self.pause_event.wait()
            
            if self.stop_event.is_set():
                task.skip('Deployment stopped by user')
                self._trigger_callback('on_task_skip', task)
                self.logger.warning(
                    f'Task {task.task_id} skipped due to stop event',
                    node=node.name
                )
                continue
            
            try:
                # Start task
                task.start()
                self._trigger_callback('on_task_start', task)
                self.logger.info(
                    f'Starting task: {task.software_name} {task.software_version}',
                    node=node.name
                )
                
                # Get software configuration
                software_config = self._get_software_config(node, task.software_name)
                
                # Run pre-installation checks
                self.logger.info('Running pre-installation checks', node=node.name)
                check_results = self._run_checkers(node, software_config)
                
                if self._has_check_errors(check_results):
                    error_msg = f"Pre-installation checks failed: {check_results['failed']} errors"
                    task.fail(error_msg)
                    self._trigger_callback('on_task_fail', task, error_msg)
                    self.logger.error(error_msg, node=node.name)
                    break  # Stop this node's deployment
                
                # Get installer
                installer = self._get_installer(task.software_name, node, software_config)
                
                # Execute installation
                self.logger.info(
                    f'Installing {task.software_name} {task.software_version}',
                    node=node.name
                )
                
                install_result = installer.install()
                
                if install_result.get('status') == 'success':
                    # Post-configuration
                    self.logger.info('Running post-configuration', node=node.name)
                    installer.post_config()
                    
                    # Verification
                    self.logger.info('Verifying installation', node=node.name)
                    verify_result = installer.verify()
                    
                    if verify_result.get('status') == 'success':
                        task.complete()
                        self._trigger_callback('on_task_complete', task)
                        self.logger.info(
                            f'Task {task.task_id} completed successfully',
                            node=node.name
                        )
                    else:
                        error_msg = f"Verification failed: {verify_result.get('message', 'Unknown error')}"
                        task.fail(error_msg)
                        self._trigger_callback('on_task_fail', task, error_msg)
                        self.logger.error(error_msg, node=node.name)
                        break
                else:
                    error_msg = f"Installation failed: {install_result.get('message', 'Unknown error')}"
                    task.fail(error_msg)
                    self._trigger_callback('on_task_fail', task, error_msg)
                    self.logger.error(error_msg, node=node.name)
                    break  # Stop this node's deployment
                    
            except Exception as e:
                error_msg = f'Unexpected error: {str(e)}'
                task.fail(error_msg)
                self._trigger_callback('on_task_fail', task, error_msg)
                self.logger.exception(
                    f'Unexpected error in task {task.task_id}',
                    node=node.name
                )
                break  # Stop this node's deployment
        
        self.logger.info(f'Completed deployment for node {node.name}', node=node.name)
    
    def _run_checkers(self, node: NodeConfig, software: SoftwareConfig) -> Dict[str, Any]:
        """
        Run pre-installation checkers.
        
        Args:
            node: Node configuration
            software: Software configuration
            
        Returns:
            Check results dictionary
        """
        from deployer.checker import (
            CheckerManager,
            ConnectivityChecker,
            DiskSpaceChecker,
            MemoryChecker,
            SystemInfoChecker
        )
        
        checker_manager = CheckerManager(node, self.ansible, self.logger)
        
        # Add checkers
        checker_manager.add_checker(
            ConnectivityChecker(node, self.ansible, self.logger)
        )
        checker_manager.add_checker(
            DiskSpaceChecker(node, self.ansible, self.logger, min_space_mb=500)
        )
        checker_manager.add_checker(
            MemoryChecker(node, self.ansible, self.logger, min_memory_mb=512)
        )
        checker_manager.add_checker(
            SystemInfoChecker(node, self.ansible, self.logger)
        )
        
        return checker_manager.run_all()
    
    def _has_check_errors(self, check_results: Dict[str, Any]) -> bool:
        """
        Check if there are any check errors.
        
        Args:
            check_results: Check results from CheckerManager
            
        Returns:
            True if there are errors
        """
        return check_results.get('failed', 0) > 0
    
    def _get_installer(
        self,
        software_name: str,
        node: NodeConfig,
        software: SoftwareConfig
    ):
        """
        Get installer instance for software.
        
        Args:
            software_name: Software name
            node: Node configuration
            software: Software configuration
            
        Returns:
            Installer instance
        """
        from deployer.installers import get_installer
        
        installer_class = get_installer(software_name)
        return installer_class(node, software, self.ansible, self.logger)
    
    def _get_software_config(
        self,
        node: NodeConfig,
        software_name: str
    ) -> SoftwareConfig:
        """
        Get software configuration from node.
        
        Args:
            node: Node configuration
            software_name: Software name
            
        Returns:
            Software configuration
            
        Raises:
            ValueError: If software not found
        """
        for sw in node.install:
            if sw.name == software_name:
                return sw
        
        raise ValueError(
            f'Software {software_name} not found in node {node.name} configuration'
        )
    
    def pause(self) -> None:
        """Pause deployment execution."""
        self.logger.info('Pausing deployment')
        self.pause_event.clear()
        self._trigger_callback('on_pause')
    
    def resume(self) -> None:
        """Resume deployment execution."""
        self.logger.info('Resuming deployment')
        self.pause_event.set()
        self._trigger_callback('on_resume')
    
    def stop(self) -> None:
        """Stop deployment execution."""
        self.logger.info('Stopping deployment')
        self.stop_event.set()
        self.pause_event.set()  # Unpause if paused
        self.executor.shutdown(wait=False)
        self._trigger_callback('on_stop')
    
    def wait_completion(self, timeout: Optional[float] = None) -> None:
        """
        Wait for all tasks to complete.
        
        Args:
            timeout: Optional timeout in seconds
        """
        self.logger.info('Waiting for deployment completion')
        self.executor.shutdown(wait=True)
        self.logger.info('Deployment completed')
    
    def is_running(self) -> bool:
        """
        Check if deployment is currently running.
        
        Returns:
            True if running
        """
        stats = self.task_manager.get_statistics()
        return stats.get('running', 0) > 0
    
    def is_paused(self) -> bool:
        """
        Check if deployment is paused.
        
        Returns:
            True if paused
        """
        return not self.pause_event.is_set()
    
    def is_stopped(self) -> bool:
        """
        Check if deployment is stopped.
        
        Returns:
            True if stopped
        """
        return self.stop_event.is_set()
