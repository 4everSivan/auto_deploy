"""
CLI UI module using rich for beautiful terminal output.
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from typing import Dict, List, Any

from deployer.task_manager import Task, TaskStatus, TaskManager # Added TaskManager import

class CLIUI:
    """Helper class for CLI terminal interface using rich."""
    
    def __init__(self, task_manager: TaskManager, dry_run: bool = False) -> None:
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )
        self.node_tasks: Dict[Any, Any] = {} # node_name -> rich_task_id
        self.task_manager = task_manager # Added from __init__ parameter
        self.dry_run = dry_run # Added from __init__ parameter
        
    def print_banner(self) -> None:
        """Print application banner."""
        self.console.print(Panel.fit(
            "[bold cyan]Auto-Deploy Engine[/bold cyan]\n"
            "[dim]A powerful multi-threaded deployment tool[/dim]",
            border_style="blue"
        ))
        
    def print_dry_run_warning(self) -> None:
        """Print dry-run warning."""
        self.console.print("[bold yellow]⚠️  DRY RUN MODE ENABLED. No changes will be made to remote systems.[/bold yellow]\n")

    def confirm_deployment(self, nodes: List[Any]) -> bool:
        """
        Ask for deployment confirmation.
        
        Args:
            nodes: List of node configurations
            
        Returns:
            True if confirmed
        """
        self.console.print("\n[bold]Planned Deployment:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Node", style="dim")
        table.add_column("Software")
        
        for node in nodes:
            software_list = ", ".join([f"{sw.name} ({sw.version})" for sw in node.install])
            table.add_row(node.name, software_list)
            
        self.console.print(table)
        
        from rich.prompt import Confirm
        return Confirm.ask("Do you want to proceed with the deployment?")

    def show_summary(self, statistics: Dict[str, int], total_duration: float) -> None:
        """
        Show final deployment summary.
        
        Args:
            statistics: Task statistics from TaskManager
            total_duration: Overall execution time
        """
        self.console.print("\n" + "="*40)
        self.console.print("[bold green]Deployment Summary[/bold green]")
        self.console.print(f"Total time: {total_duration:.2f}s")
        
        table = Table(show_header=False, box=None)
        table.add_row("Total Tasks:", str(statistics['total']))
        table.add_row("Completed:", f"[green]{statistics['completed']}[/green]")
        table.add_row("Failed:", f"[red]{statistics['failed']}[/red]" if statistics['failed'] > 0 else "0")
        table.add_row("Skipped:", f"[yellow]{statistics['skipped']}[/yellow]")
        
        self.console.print(table)
        self.console.print("="*40 + "\n")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")

    def update_status(self, live: Live) -> None: # New method
        """Update the live display with current task statuses."""
        for node_name, task_id in self.node_tasks.items():
            task_status = self.task_manager.get_node_status(node_name)
            if task_status:
                description = f"[bold]{node_name}[/bold]: {task_status.software_name}"
                self.progress.update(task_id, description=description, completed=task_status.progress)
                if task_status.status == TaskStatus.COMPLETED:
                    self.progress.update(task_id, description=f"[bold green]{node_name}[/bold green]: [green]Completed[/green]", completed=100)
                elif task_status.status == TaskStatus.FAILED:
                    self.progress.update(task_id, description=f"[bold red]{node_name}[/bold red]: [red]Failed[/red]", completed=100)
                elif task_status.status == TaskStatus.SKIPPED:
                    self.progress.update(task_id, description=f"[bold yellow]{node_name}[/bold yellow]: [yellow]Skipped[/yellow]", completed=100)
        live.update(self.progress) # Ensure live display is updated
