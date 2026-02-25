"""
CLI UI module using rich for beautiful terminal output.
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from typing import Dict, List, Any

from deployer.task_manager import Task, TaskStatus

class CLIUI:
    """Helper class for CLI terminal interface using rich."""
    
    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )
        self.node_tasks = {} # node_name -> rich_task_id
        
    def print_banner(self):
        """Print application banner."""
        self.console.print(Panel.fit(
            "[bold cyan]Auto-Deploy Engine[/bold cyan]\n"
            "[dim]A powerful multi-threaded deployment tool[/dim]",
            border_style="blue"
        ))
        
    def print_dry_run_warning(self):
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

    def show_summary(self, statistics: Dict[str, int], total_duration: float):
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

    def print_error(self, message: str):
        """Print error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_info(self, message: str):
        """Print info message."""
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")

    def print_success(self, message: str):
        """Print success message."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")
