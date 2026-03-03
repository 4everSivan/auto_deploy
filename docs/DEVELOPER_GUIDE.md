# Auto Deploy Developer Guide

This guide is for developers looking to understand the internal architecture of Auto Deploy, fix bugs, or extend its functionality.

## 1. Architecture Overview

Auto Deploy follows a modular design with clear separation of concerns:

- **Config (`deployer/config.py`)**: Responsible for loading, parsing, and validating YAML configuration files using Pydantic models.
- **TaskManager (`deployer/task_manager.py`)**: Manages the deployment state machine. Converts configuration into discrete `Task` objects and tracks their lifecycle.
- **DeploymentExecutor (`deployer/executor.py`)**: The engine of the application. Orchestrates concurrent execution across nodes using a thread pool.
- **Installers (`deployer/installers/`)**: Modular components that handle the actual software installation logic via Ansible.
- **Checkers (`deployer/checker/`)**: Background threads that perform pre-flight and health checks.
- **TUI (`deployer/tui/`)**: A Textual-based interface for interactive monitoring and control.

## 2. Core Components

### `DeploymentExecutor`
The executor runs a loop that picks pending tasks and assigns them to node-specific threads. It handles:
- Concurrency control.
- Callback execution (for UI updates).
- Cleanup and graceful shutdown.

### `AnsibleWrapper`
A thin wrapper around `ansible-runner`. It abstracts the complexity of setting up environment variables and handling runner events. It supports a `cancel_callback` for immediate termination.

## 3. Extending the Tool

### Adding a New Installer
1. Create a new file in `deployer/installers/` (e.g., `mysql_installer.py`).
2. Inherit from `BaseInstaller`.
3. Implement `install()` and `verify()`:
   ```python
   def install(self) -> Dict[str, Any]:
       # Use self.ansible.run_playbook(...) or run_command(...)
       return {'status': 'success'}
   ```
4. Update `DeploymentExecutor._get_installer` to recognize the new software name.

### Adding a New Checker
1. Create a new class in `deployer/checker/` inheriting from `BaseChecker`.
2. Implement `check()`:
   ```python
   def check(self) -> bool:
       # Return True if check passes
       return True
   ```
3. Register it in `CheckerManager`.

## 4. Testing

### Running Tests
We use `pytest` for all levels of testing:
```bash
# Run all tests
pytest

# Run TUI tests only
pytest tests/test_tui.py

# Run integration tests only
pytest tests/test_integration.py
```

### Mocking Guidelines
- Mock `ansible_runner` to avoid real network calls.
- Use `textual.test_client` for UI testing.
- Always check `self.app.is_running` in TUI-related background callbacks to avoid `RuntimeError`.

## 5. Coding Standards
- Follow PEP 8 style guidelines.
- Use Pydantic for data validation.
- All new features MUST include corresponding unit tests.
- Maintain Google-style docstrings for all public classes and methods.
