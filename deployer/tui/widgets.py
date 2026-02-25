"""
Custom widgets for Auto Deploy TUI.
"""

from typing import Dict, Any, List, Optional
from textual.widgets import Static, Tree, ProgressBar, RichLog, Label
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.message import Message

from deployer.task_manager import TaskStatus, Task

class NodeStatusTree(Tree):
    """Tree widget showing nodes and their tasks."""
    
    def populate(self, nodes_config: List[Any], task_manager: Any) -> None:
        """Populate tree with nodes and tasks."""
        self.clear()
        self.root.expand()
        
        for node in nodes_config:
            node_node = self.root.add(f"📦 {node.name} ({node.host})", expand=True, data={'type': 'node', 'name': node.name})
            tasks = task_manager.get_node_tasks(node.name)
            for task in tasks:
                icon = self._get_status_icon(task.status)
                node_node.add_leaf(f"{icon} {task.software_name} [{task.status.value}]", data={'type': 'task', 'id': task.id})

    def _get_status_icon(self, status: TaskStatus) -> str:
        icons = {
            TaskStatus.PENDING: "⏸",
            TaskStatus.RUNNING: "⏳",
            TaskStatus.COMPLETED: "✓",
            TaskStatus.FAILED: "✗",
            TaskStatus.SKIPPED: "⊘"
        }
        return icons.get(status, "?")

class ProgressPanel(Vertical):
    """Panel showing overall deployment progress."""
    
    progress = reactive(0.0)
    nodes_done = reactive(0)
    total_nodes = reactive(0)
    tasks_done = reactive(0)
    total_tasks = reactive(0)
    
    def compose(self):
        yield Label("Overall Progress", id="progress-title")
        yield ProgressBar(total=100, show_percentage=True, id="total-progress-bar")
        yield Label("Stats:", id="stats-label")
        yield Static(id="stats-content")

    def watch_progress(self, progress: float) -> None:
        self.query_one(ProgressBar).progress = progress

    def update_stats(self, nodes_done: int, total_nodes: int, tasks_done: int, total_tasks: int):
        self.nodes_done = nodes_done
        self.total_nodes = total_nodes
        self.tasks_done = tasks_done
        self.total_tasks = total_tasks
        
        content = (
            f"Nodes: {nodes_done}/{total_nodes} completed\n"
            f"Tasks: {tasks_done}/{total_tasks} completed"
        )
        self.query_one("#stats-content").update(content)

class TaskDetailsPanel(Vertical):
    """Panel showing details of the current task."""
    
    current_task = reactive(None)
    
    def compose(self):
        yield Label("Task Details", id="details-title")
        yield Static("No active task", id="details-content")

    def watch_current_task(self, task: Optional[Task]) -> None:
        if task:
            content = (
                f"Node: {task.node_name}\n"
                f"Software: {task.software_name}\n"
                f"Status: {task.status.value}\n"
                f"Message: {task.message or 'N/A'}"
            )
            self.query_one("#details-content").update(content)
        else:
            self.query_one("#details-content").update("No active task")

class LogViewPanel(RichLog):
    """Panel showing live logs."""
    
    def __init__(self, **kwargs):
        super().__init__(highlight=True, markup=True, **kwargs)

    def log_info(self, message: str):
        self.write(f"[white]INFO[/white]: {message}")

    def log_success(self, message: str):
        self.write(f"[green]SUCCESS[/green]: {message}")

    def log_warning(self, message: str):
        self.write(f"[yellow]WARNING[/yellow]: {message}")

    def log_error(self, message: str):
        self.write(f"[red]ERROR[/red]: {message}")
