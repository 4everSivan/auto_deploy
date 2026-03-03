# Auto Deploy 开发指南

本指南旨在帮助开发人员了解 Auto Deploy 的内部架构、修复错误或扩展其功能。

## 1. 架构概览

Auto Deploy 采用了模块化设计,职责分明:

- **配置 (Config, `deployer/config.py`)**: 负责使用 Pydantic 模型加载、解析和验证 YAML 配置文件。
- **任务管理器 (TaskManager, `deployer/task_manager.py`)**: 管理部署状态机。将配置转换为离散的 `Task` 对象并跟踪其生命周期。
- **部署执行引擎 (DeploymentExecutor, `deployer/executor.py`)**: 应用程序的核心。使用线程池编排跨节点的并发执行。
- **安装器 (Installers, `deployer/installers/`)**: 模块化组件,负责通过 Ansible 处理实际的软件安装逻辑。
- **检查器 (Checkers, `deployer/checker/`)**: 后台线程,执行预检和健康检查。
- **TUI (`deployer/tui/`)**: 基于 Textual 的界面,用于交互式监控和控制。

## 2. 核心组件

### `DeploymentExecutor`
执行器运行一个循环,选取待处理的任务并将其分配给特定于节点的线程。它处理:
- 并发控制。
- 回调执行（用于 UI 更新）。
- 清理和优雅闭。

### `AnsibleWrapper`
对 `ansible-runner` 的薄包装。它抽象了设置环境变量和处理运行器事件的复杂性。它支持 `cancel_callback` 以实现立即终止。

## 3. 扩展工具

### 添加新的安装器
1. 在 `deployer/installers/` 中创建新文件（例如 `mysql_installer.py`）。
2. 继承自 `BaseInstaller`。
3. 实现 `install()` 和 `verify()`:
   ```python
   def install(self) -> Dict[str, Any]:
       # 使用 self.ansible.run_playbook(...) 或 run_command(...)
       return {'status': 'success'}
   ```
4. 更新 `DeploymentExecutor._get_installer` 以识别新的软件名称。

### 添加新的检查器
1. 在 `deployer/checker/` 中创建一个继承自 `BaseChecker` 的新类。
2. 实现 `check()`:
   ```python
   def check(self) -> bool:
       # 如果检查通过则返回 True
       return True
   ```
3. 在 `CheckerManager` 中注册它。

## 4. 测试

### 运行测试
我们使用 `pytest` 进行各层级的测试:
```bash
# 运行所有测试
pytest

# 仅运行 TUI 测试
pytest tests/test_tui.py

# 仅运行集成测试
pytest tests/test_integration.py
```

### Mock 指南
- Mock `ansible_runner` 以避免真实的网络调用。
- 使用 `textual.test_client` 进行 UI 测试。
- 始终在与 TUI 相关的后台回调中检查 `self.app.is_running` 以避免 `RuntimeError`。

## 5. 编码标准
- 遵循 PEP 8 代码风格。
- 使用 Pydantic 进行数据验证。
- 所有新功能必须包含相应的单元测试。
- 为所有公共类和方法维护 Google 风格的文档字符串（docstrings）。
