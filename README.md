# Auto Deploy - 自动化部署工具

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

基于 Ansible 的多节点并发部署工具,提供现代化 TUI 界面和 CLI 模式。

## ✨ 特性

- 🚀 **多节点并发部署**: 支持最多 10 个节点同时部署,大幅提升效率
- 🎨 **现代化 TUI 界面**: 基于 Textual 框架的美观终端界面
- 💻 **CLI 模式**: 支持命令行模式,适合脚本化和自动化场景
- 🔍 **完善的安装前检查**: 连通性、软件状态、资源、依赖等全方位检查
- 🛡️ **错误隔离**: 单节点失败不影响其他节点继续执行
- 🔧 **易于扩展**: 基于抽象类设计,轻松添加新软件支持
- 🔐 **安全认证**: 支持 SSH 密钥和密码认证

## 📋 支持的软件

- ☕ Java (JDK 8/11/17)
- 🐍 Python (2.7/3.x)
- 🦓 Zookeeper (3.6+)
- 🔜 更多软件持续添加中...

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd auto_deploy

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 生成配置文件

```bash
python run.py generate-config > deploy.yml
```

### 编辑配置文件

编辑 `deploy.yml`,配置节点信息和要安装的软件:

```yaml
general:
  data_dir: './deploy_data'
  max_concurrent_nodes: 10

log:
  level: 'INFO'
  dir: './deploy_data/log'

nodes:
  - node_01:
      host: '192.168.1.1'
      port: 22
      owner_user: 'sivan'
      owner_key: '~/.ssh/id_rsa'
      super_user: 'root'
      super_pass: 'your_password'
      install:
        - java:
            version: '11'
            install_path: '/usr/local/java'
        - python:
            version: '3.9.0'
            install_path: '/usr/local/python'
```

### 执行部署

**TUI 模式** (推荐):
```bash
python run.py -c deploy.yml --tui
```

**CLI 模式**:
```bash
python run.py -c deploy.yml
```

**Dry-run 模式** (仅检查,不实际安装):
```bash
python run.py -c deploy.yml --dry-run
```

## 📚 文档

- [用户指南 (User Guide)](docs/USER_GUIDE.md) - **推荐阅读**: 详细的安装和使用教程
- [开发指南 (Developer Guide)](docs/DEVELOPER_GUIDE.md) - 架构解析和扩展指南
- [需求规格说明书](docs/requirements_specification.md)
- [技术设计文档](docs/technical_design.md)
- [实施计划](docs/implementation_plan.md)
- [开发任务清单](docs/task.md)

## 🏗️ 项目结构

```
auto_deploy/
├── deployer/           # 核心部署模块
│   ├── config.py      # 配置管理 (Pydantic 验证)
│   ├── ctl.py         # CLI 控制器
│   ├── executor.py    # 并发执行引擎
│   ├── task_manager.py # 状态管理
│   ├── ansible_wrapper.py # ansible-runner 封装
│   ├── checker/       # 预检查系统
│   └── installers/    # 软件安装器 (Java, Python, Zookeeper)
├── common/            # 公共模块 (日志, 异常, 工具)
├── playbook/          # Ansible Playbooks
├── tests/             # 单元及集成测试 (133 个测试用例)
└── docs/              # 项目文档
```

## 🧪 运行测试

```bash
# 运行所有单元测试和集成测试
pytest

# 生成覆盖率报告
pytest --cov=deployer --cov=common --cov-report=term-missing
```

## 🛠️ 开发状态

### ✅ 已完成

- [x] 项目结构 & 基础框架设计
- [x] 基于 Pydantic 的配置验证系统
- [x] 多线程并发执行引擎 (支持优先级控制)
- [x] 现代化 TUI 交互界面 (Textual)
- [x] Ansible 核心集成 (ansible-runner)
- [x] 软件安装器: Java, Python, Zookeeper
- [x] 完善的单元测试与集成测试 (133/133 通过)
- [x] 用户手册与开发者文档

### 📅 计划中 (v0.2.0)

- [ ] 更多软件支持 (MySQL, Redis, Nginx)
- [ ] 失败重试与断点续传机制
- [ ] 部署报告自动生成 (PDF/HTML)
- [ ] 容器化部署支持 (Docker)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📝 版本历史

- **v0.1.0** (2024-03)
  - 核心功能发布
  - 支持 Java, Python, Zookeeper 部署
  - 全新 TUI 界面支持

## 📄 许可证

MIT License

## 👥 作者

Sivan
