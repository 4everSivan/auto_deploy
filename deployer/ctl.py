import click
import importlib.resources

from typing import Optional

from deployer.version import __version__
from deployer.config import Config


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
