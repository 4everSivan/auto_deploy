"""
Main TUI application for Auto Deploy.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.screen import ModalScreen

from deployer.tui.widgets import NodeStatusTree, ProgressPanel, TaskDetailsPanel, LogViewPanel
from deployer.executor import DeploymentExecutor
from deployer.task_manager import TaskStatus, Task

class AutoDeployApp(App):
    """Auto Deploy TUI Application."""
    
    CSS_PATH = "style.tcss"
    
    BINDINGS = [
        Binding("s", "start", "Start", show=True),
        Binding("p", "pause", "Pause", show=True),
        Binding("r", "resume", "Resume", show=True),
        Binding("f", "filter", "Filter", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("f1", "help", "Help", show=True),
        Binding("?", "help", "Help", show=False),
    ]
    
    def __init__(
        self,
        executor: DeploymentExecutor,
        config_name: str = "config.yml"
    ):
        super().__init__()
        self.executor = executor
        self.config_name = config_name
        self.title = f"Auto Deploy v0.1.0"
        self.sub_title = f"Config: {config_name}"
        self._register_executor_callbacks()

    def _register_executor_callbacks(self) -> None:
        """Register callbacks with the executor to update UI."""
        self.executor.register_callback('on_task_start', self._on_task_start)
        self.executor.register_callback('on_task_complete', self._on_task_complete)
        self.executor.register_callback('on_node_complete', self._on_node_complete)
        self.executor.register_callback('on_deployment_complete', self._on_deployment_complete)
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(id="main-layout"):
            with Horizontal():
                # Left Sidebar: Node Tree
                yield NodeStatusTree("Cluster", id="node-tree", classes="node-tree-container")
                
                # Right Column: Progress and Details
                with Vertical():
                    yield ProgressPanel(id="progress-panel")
                    yield TaskDetailsPanel(id="details-panel")
            
            # Bottom row: Logs
            yield LogViewPanel(id="log-viewer")
        
        yield Footer()

    def on_mount(self) -> None:
        """Initialize UI after mounting components."""
        self._update_node_tree()
        self._update_progress()

    def _update_node_tree(self) -> None:
        """Update the node status tree."""
        tree = self.query_one(NodeStatusTree)
        tree.populate(self.executor.config.get_nodes(), self.executor.task_manager)

    def _update_progress(self) -> None:
        """Update global progress bars and stats."""
        stats = self.executor.task_manager.get_stats()
        panel = self.query_one(ProgressPanel)
        panel.update_stats(
            nodes_done=stats['nodes_completed'],
            total_nodes=stats['total_nodes'],
            tasks_done=stats['tasks_completed'],
            total_tasks=stats['total_tasks']
        )
        panel.progress = stats['percent_complete']

    # --- Callback Handlers (Run in executor threads) ---

    def _on_task_start(self, task: Task) -> None:
        """Called when a task starts."""
        self.call_from_thread(self._handle_task_start, task)

    def _on_task_complete(self, task: Task) -> None:
        """Called when a task completes."""
        self.call_from_thread(self._handle_task_complete, task)

    def _on_node_complete(self, node_name: str) -> None:
        """Called when all tasks for a node are complete."""
        self.call_from_thread(self._handle_node_complete, node_name)

    def _on_deployment_complete(self, stats: Dict[str, Any]) -> None:
        """Called when the entire deployment is complete."""
        self.call_from_thread(self._handle_deployment_complete, stats)

    # --- Main Thread UI Updates ---

    def _handle_task_start(self, task: Task) -> None:
        self.query_one(TaskDetailsPanel).current_task = task
        self.query_one(LogViewPanel).log_info(f"Started: {task.node_name} - {task.software_name}")
        self._update_node_tree()
        self._update_progress()

    def _handle_task_complete(self, task: Task) -> None:
        log_panel = self.query_one(LogViewPanel)
        if task.status == TaskStatus.COMPLETED:
            log_panel.log_success(f"Completed: {task.node_name} - {task.software_name}")
        elif task.status == TaskStatus.FAILED:
            log_panel.log_error(f"Failed: {task.node_name} - {task.software_name}: {task.error_message}")
        
        self._update_node_tree()
        self._update_progress()

    def _handle_node_complete(self, node_name: str) -> None:
        self.query_one(LogViewPanel).log_info(f"Node complete: {node_name}")
        self._update_node_tree()
        self._update_progress()

    def _handle_deployment_complete(self, stats: Dict[str, Any]) -> None:
        self.query_one(LogViewPanel).log_success("All deployments finished!")
        self.notify("Deployment Complete", severity="information")
        self._update_progress()

    async def action_start(self) -> None:
        """Start deployment."""
        if self.executor.is_running():
            self.notify("Deployment already running", severity="warning")
            return
            
        self.notify("Deployment started")
        # Run executor in a separate thread so it doesn't block the UI
        import threading
        self.execution_thread = threading.Thread(target=self.executor.execute_all)
        self.execution_thread.start()
        
    async def action_pause(self) -> None:
        """Pause deployment."""
        self.executor.pause()
        self.notify("Deployment paused")
        
    async def action_resume(self) -> None:
        """Resume deployment."""
        self.executor.resume()
        self.notify("Deployment resumed")
        
    async def action_filter(self) -> None:
        """Filter logs."""
        self.notify("Log filtering not implemented in this version", severity="warning")

    async def action_help(self) -> None:
        """Show help modal."""
        self.push_screen(HelpScreen())
        
    async def action_quit(self) -> None:
        """Quit application."""
        self.executor.stop()
        self.exit()

class HelpScreen(ModalScreen):
    """Screen with a dialog to show help."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Auto Deploy TUI Help", id="help-title"),
            Static(
                "S - Start deployment\n"
                "P - Pause deployment\n"
                "R - Resume deployment\n"
                "F - Filter logs (coming soon)\n"
                "Q - Quit application\n"
                "F1 or ? - Show this help",
                id="help-text"
            ),
            Static("Press any key to close", id="help-footer"),
            id="help-dialog"
        )

    def on_key(self) -> None:
        self.dismiss()

if __name__ == "__main__":
    # For quick testing of UI only
    from unittest.mock import Mock
    mock_executor = Mock(spec=DeploymentExecutor)
    app = AutoDeployApp(mock_executor)
    app.run()
