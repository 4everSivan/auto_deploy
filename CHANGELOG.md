# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
并且本项目遵循 [语义化版本控制](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

### 新增

#### Stage 4: 检查器实现
- **检查器框架**:
  - 创建了抽象 `BaseChecker` 类，定义检查接口。
  - 实现了 `CheckerManager`，用于管理和运行多个检查器。
  - 定义了 `CheckStatus` 枚举（PASSED, WARNING, FAILED, SKIPPED）。
  - 实现了 `CheckResult` 类，用于封装检查结果。
- **具体检查器**:
  - `ConnectivityChecker`: SSH 连接测试。
  - `DiskSpaceChecker`: 磁盘空间验证（可配置最小空间要求）。
  - `MemoryChecker`: 内存可用性检查（可配置最小内存要求）。
  - `PortAvailabilityChecker`: 端口占用检测（检查指定端口是否可用）。
  - `SystemInfoChecker`: 系统信息收集（OS、内核、CPU、内存）。
  - `PackageManagerChecker`: 包管理器可用性检查（支持 apt-get 和 yum）。
  - `SudoPrivilegeChecker`: Sudo 权限测试（验证权限提升是否可用）。

#### Stage 3: Ansible 集成与安装器
- **AnsibleWrapper**:
  - 封装 `ansible_runner` 用于执行 playbook 和 ad-hoc 命令。
  - 实现了 SSH 连接测试和 inventory 生成。
  - 为 Ansible 任务添加了全面的错误处理和日志记录。
- **安装器**:
  - 创建了抽象 `BaseInstaller` 类，定义安装生命周期（预检查、安装、后配置、验证）。
  - 实现了 `JavaInstaller`，支持仓库、URL 和本地安装源。
  - 实现了 `PythonInstaller`，支持仓库和源码编译安装。
  - 实现了 `ZookeeperInstaller`，支持仓库和 URL 源，并自动生成 `zoo.cfg`。
  - 添加了 `InstallerRegistry`，用于基于工厂模式的安装器实例化。
- **Playbooks**:
  - 添加了基础连通性测试 playbook (`playbook/test_connection.yml`)。

#### Stage 2: 配置与任务管理
- **配置管理**:
  - 扩展 `Config` 类以支持详细的节点和软件配置。
  - 实现了 `NodeConfig` 和 `SoftwareConfig` 数据类，具有严格的类型检查和验证。
  - 添加了对 SSH 密钥认证和自定义 SSH 端口的支持。
  - 添加了对软件版本控制和安装源配置的支持。
  - 实现了 `max_concurrent_nodes`（最大并发节点数）配置。
- **验证**:
  - 添加了对 IP 地址、端口、文件权限和路径的全面验证。
  - 实现了严格的目录写权限检查。

#### Stage 1: 基础设施与核心
- **项目结构**:
  - 建立了标准的 Python 项目结构 (`deployer/`, `common/`, `tests/`, `docs/`)。
  - 配置了带有 fixtures 和覆盖率报告的 `pytest` 框架。
- **核心模块**:
  - `common.logger`: 具有轮转和敏感数据脱敏功能的集中式日志系统。
  - `common.exceptions`: 自定义异常体系 (`DeployException`, `ConfigException`, `AnsibleException` 等)。
  - `common.utils`: 用于路径扩展、格式化和系统检查的实用函数。
- **文档**:
  - 添加了包含项目概述和快速入门指南的 `README.md`。
  - 添加了详述 Textual TUI 架构的 `docs/tui_design.md`。
  - 添加了 `docs/technical_design.md` 和 `docs/requirements_specification.md`。

### 变更
- 更新了 `deploy.yml` 模板以反映新的配置结构（节点、软件、源）。
- 更新了 `.gitignore` 以包含项目特定的数据目录和 IDE 文件。

### 测试
- 实现了 100% 的通过率（所有单元测试）。
- 添加了全面的单元测试，涵盖：
  - 配置加载和验证
  - 实用函数和异常处理
  - 安装器逻辑（模拟 Ansible 执行）
  - 检查器系统（所有检查器类型）
