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

- [需求规格说明书](docs/requirements_specification.md)
- [技术设计文档](docs/technical_design.md)
- [实施计划](docs/implementation_plan.md)
- [开发任务清单](docs/task.md)

## 🏗️ 项目结构

```
auto_deploy/
├── deployer/           # 核心部署模块
│   ├── config.py      # 配置管理
│   ├── ctl.py         # CLI 控制器
│   ├── executor.py    # 执行引擎
│   ├── task_manager.py # 任务管理器
│   ├── ansible_wrapper.py # Ansible 封装
│   ├── checker.py     # 安装前检查
│   └── installers/    # 软件安装器
├── tui/               # TUI 界面模块
│   ├── screens/       # 界面屏幕
│   └── widgets/       # 自定义组件
├── common/            # 公共模块
│   ├── logger.py      # 日志系统
│   ├── exceptions.py  # 异常定义
│   └── utils.py       # 工具函数
├── playbook/          # Ansible Playbooks
├── tests/             # 单元测试
└── docs/              # 项目文档
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=deployer --cov=common --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 🛠️ 开发状态

### ✅ 已完成

- [x] 项目结构搭建
- [x] 异常定义和工具函数
- [x] 日志系统
- [x] 单元测试框架 (20/20 测试通过)

### 🚧 进行中

- [ ] 配置管理扩展
- [ ] 任务管理器
- [ ] Ansible 集成
- [ ] 安装前检查器
- [ ] 执行引擎
- [ ] TUI 界面

### 📅 计划中

- [ ] 更多软件支持 (MySQL, Redis, Nginx, Tomcat)
- [ ] 自定义 Playbook 支持
- [ ] 失败重试机制
- [ ] 部署报告导出

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📝 版本历史

- **v0.1.0** (开发中)
  - 初始版本
  - 支持 Java, Python, Zookeeper 部署
  - TUI 和 CLI 双模式

## 📄 许可证

MIT License

## 👥 作者

Sivan

---

**注意**: 本项目目前处于开发阶段,部分功能尚未完成。
