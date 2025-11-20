"""Textual TUI 应用入口。

定义部署过程的终端界面应用类，后续可扩展为节点列表、任务进度与日志视图。
"""
from textual.app import App


class DeployApp(App):
    """部署 TUI 应用。

    当前为空实现，作为 Textual 应用占位；后续可通过 ``compose``/``on_*`` 方法
    构建界面与交互逻辑，将部署进度与日志实时呈现。
    """
    pass
