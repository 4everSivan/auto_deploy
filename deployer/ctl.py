import click
import importlib.resources
import time
from typing import Optional

from deployer.version import __version__
from deployer.config import Config
from deployer.task_manager import TaskManager
from deployer.executor import DeploymentExecutor
from deployer.cli_ui import CLIUI
from common.logger import DeployLogger


@click.group(cls=click.Group, help='auto-deploy command-lines')
@click.option('--config-file', '-c', help='Configuration file', default=None)
@click.pass_context
def ctl(ctx: click.Context, config_file: Optional[str]) -> None:
    try:
        # version 命令不做任何处理
        if ctx.invoked_subcommand in ['version', 'generate-config']:
            return

        config = Config(config_file)

        # 设置命令上下文
        ctx.obj = {
            '__config': config,
        }
    except Exception as e:
        click.echo(e)
        raise click.Abort()


@ctl.command('version', help='Output version information')
def version() -> None:
    click.echo(f'Auto-deploy version: {__version__}')


@ctl.command('deploy', help='Execute deployment')
@click.option('--node', '-n', multiple=True, help='Filter by node name(s)')
@click.option('--software', '-s', multiple=True, help='Filter by software name(s)')
@click.option('--dry-run', is_flag=True, help='Preview deployment without applying changes')
@click.option('--yes', '-y', is_flag=True, help='Automatically confirm deployment')
@click.pass_context
def deploy(ctx: click.Context, node: tuple, software: tuple, dry_run: bool, yes: bool) -> None:
    config = ctx.obj['__config']
    ui = CLIUI()
    
    # Setup logger
    log_dir = config.get_log_dir()
    log_level = config.get_log_level()
    logger = DeployLogger(log_dir, log_level)
    
    ui.print_banner()
    if dry_run:
        ui.print_dry_run_warning()
    
    # Task Manager
    task_manager = TaskManager(config)
    task_manager.create_tasks()
    
    # Filter nodes if specified
    all_nodes = config.get_nodes()
    target_nodes = all_nodes
    if node:
        target_nodes = [n for n in all_nodes if n.name in node]
        if not target_nodes:
            ui.print_error(f"No nodes found matching: {node}")
            return

    # Confirmation
    if not yes and not dry_run:
        if not ui.confirm_deployment(target_nodes):
            ui.print_info("Deployment cancelled by user.")
            return

    # Executor
    executor = DeploymentExecutor(config, task_manager, logger, dry_run=dry_run)
    
    # Progress display using rich.Live
    from rich.live import Live
    
    start_time = time.time()
    
    with Live(ui.progress, refresh_per_second=4, console=ui.console):
        # Register callbacks to update progress
        node_tasks = {}
        
        def on_task_start(task):
            if task.node_name not in node_tasks:
                node_tasks[task.node_name] = ui.progress.add_task(
                    f"[cyan]{task.node_name}[/cyan]: {task.software_name}", 
                    total=100
                )
            else:
                ui.progress.update(
                    node_tasks[task.node_name], 
                    description=f"[cyan]{task.node_name}[/cyan]: {task.software_name}",
                    completed=0
                )
        
        def on_task_complete(task):
            if task.node_name in node_tasks:
                ui.progress.update(node_tasks[task.node_name], completed=100)
                
        def on_task_fail(task, error):
            if task.node_name in node_tasks:
                ui.progress.update(
                    node_tasks[task.node_name], 
                    description=f"[red]{task.node_name}[/red]: {task.software_name} [bold red]FAILED[/bold red]"
                )

        executor.register_callback('on_task_start', on_task_start)
        executor.register_callback('on_task_complete', on_task_complete)
        executor.register_callback('on_task_fail', on_task_fail)
        
        # Start execution
        executor.execute_all()
        executor.wait_completion()
        
    duration = time.time() - start_time
    stats = task_manager.get_statistics()
    ui.show_summary(stats, duration)
    
    if stats['failed'] > 0:
        ui.print_error("Deployment finished with errors.")
        raise click.Abort()
    else:
        ui.print_success("Deployment completed successfully!")


@ctl.command('generate-config', help='Generate configuration file')
def generate_config() -> None:
    try:
        # 尝试使用 importlib.resources 读取包内资源
        content = importlib.resources.read_text('deployer.template', 'deploy.yml', encoding='utf-8')
        # 输出到控制台
        click.echo(content)
    except Exception as e:
        click.echo(f"Error reading template file: {e}")
        raise click.Abort()


def main() -> None:
    ctl()
