"""
Task management module for deployment tasks.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from deployer.config import Config
from deployer.models import NodeConfig


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Deployment task definition."""
    task_id: str
    node_name: str
    software_name: str
    software_version: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.start_time = time.time()
        self.progress = 0.0
    
    def complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.end_time = time.time()
    
    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.end_time = time.time()
        self.error_message = error
    
    def skip(self, reason: str) -> None:
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.error_message = reason
    
    def update_progress(self, progress: float) -> None:
        """Update task progress."""
        self.progress = min(100.0, max(0.0, progress))
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'node_name': self.node_name,
            'software_name': self.software_name,
            'software_version': self.software_version,
            'status': self.status.value,
            'progress': self.progress,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration(),
            'error_message': self.error_message
        }


class TaskManager:
    """Manager for deployment tasks."""
    
    def __init__(self, config: Config):
        """
        Initialize task manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.tasks: Dict[str, Task] = {}
        self.node_tasks: Dict[str, List[str]] = {}  # node_name -> task_ids
    
    def create_tasks(self) -> None:
        """Create all tasks based on configuration."""
        nodes = self.config.get_nodes()
        
        for node in nodes:
            task_ids = []
            
            for software in node.install:
                task_id = f"{node.name}_{software.name}_{software.version}"
                
                task = Task(
                    task_id=task_id,
                    node_name=node.name,
                    software_name=software.name,
                    software_version=software.version
                )
                
                self.tasks[task_id] = task
                task_ids.append(task_id)
            
            self.node_tasks[node.name] = task_ids
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None
        """
        return self.tasks.get(task_id)
    
    def get_node_tasks(self, node_name: str) -> List[Task]:
        """
        Get all tasks for a specific node.
        
        Args:
            node_name: Node name
            
        Returns:
            List of tasks
        """
        task_ids = self.node_tasks.get(node_name, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]
    
    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List of all tasks
        """
        return list(self.tasks.values())
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get task statistics.
        
        Returns:
            Dictionary with task counts by status
        """
        stats = {
            'total': len(self.tasks),
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for task in self.tasks.values():
            stats[task.status.value] += 1
        
        return stats
    
    def get_progress(self) -> float:
        """
        Get overall progress percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if not self.tasks:
            return 0.0
        
        total_progress = sum(task.progress for task in self.tasks.values())
        return total_progress / len(self.tasks)
    
    def reset(self) -> None:
        """Reset all tasks to pending state."""
        for task in self.tasks.values():
            task.status = TaskStatus.PENDING
            task.progress = 0.0
            task.start_time = None
            task.end_time = None
            task.error_message = None
