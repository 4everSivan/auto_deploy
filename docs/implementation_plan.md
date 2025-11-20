# Auto Deploy 项目实施计划

**版本**: 1.0  
**日期**: 2025-11-20  
**项目**: Auto Deploy - 自动化部署工具

---

## 1. 项目概述

本实施计划基于需求规格说明书和技术设计文档,详细规划 Auto Deploy 项目的开发任务、优先级、时间线和测试策略。

### 1.1 开发目标
- 实现基于 Ansible 的多节点并发部署
- 提供现代化 TUI 界面和 CLI 模式
- 支持 Java、Python、Zookeeper 三种软件的自动化安装
- 实现完善的安装前检查和错误处理机制

### 1.2 开发周期
- **预计时间**: 2-3 周
- **团队规模**: 1-2 人
- **开发模式**: 迭代开发,核心功能优先

---

## 2. 项目结构重组

### 2.1 目标结构

```
auto_deploy/
├── deployer/                    # 核心部署模块
│   ├── __init__.py
│   ├── config.py               # ✅ 已有,需扩展
│   ├── ctl.py                  # ✅ 已有,需扩展
│   ├── version.py              # ✅ 已有
│   ├── executor.py             # 🆕 执行引擎
│   ├── task_manager.py         # 🆕 任务管理器
│   ├── ansible_wrapper.py      # 🆕 Ansible 封装
│   ├── checker.py              # 🆕 安装前检查
│   ├── installers/             # 🆕 安装器模块
│   │   ├── __init__.py
│   │   ├── base_installer.py  # 基类
│   │   ├── java_installer.py
│   │   ├── python_installer.py
│   │   └── zookeeper_installer.py
│   └── template/
│       └── deploy.yml          # ✅ 已有,需扩展
├── tui/                         # TUI 界面模块
│   ├── __init__.py             # ✅ 已有,需重写
│   ├── screens/                # 🆕 界面屏幕
│   │   └── main_screen.py
│   ├── widgets/                # 🆕 自定义组件
│   │   ├── __init__.py
│   │   ├── node_tree.py       # 节点树
│   │   ├── progress_panel.py  # 进度面板
│   │   └── log_viewer.py      # 日志查看器
│   └── css/
│       └── main.tcss           # 🆕 样式文件
├── common/                      # 公共模块
│   ├── __init__.py             # ✅ 已有
│   ├── logger.py               # 🆕 日志系统
│   ├── exceptions.py           # 🆕 异常定义
│   └── utils.py                # 🆕 工具函数
├── playbook/                    # Ansible Playbooks
│   ├── install_java.yml        # 🆕 Java 安装
│   ├── install_python.yml      # 🆕 Python 安装
│   ├── install_zookeeper.yml   # 🆕 Zookeeper 安装
│   └── check_connection.yml    # 🆕 连接检查
├── tests/                       # 测试模块
│   ├── __init__.py             # ✅ 已有
│   ├── test_config.py          # 🆕 配置测试
│   ├── test_executor.py        # 🆕 执行器测试
│   ├── test_checker.py         # 🆕 检查器测试
│   ├── test_task_manager.py    # 🆕 任务管理器测试
│   └── fixtures/               # 🆕 测试数据
│       └── test_config.yml
├── docs/                        # 🆕 文档目录
│   ├── requirements.md         # 需求文档
│   ├── design.md               # 设计文档
│   ├── user_guide.md           # 用户手册
│   └── developer_guide.md      # 开发者指南
├── examples/                    # 🆕 示例配置
│   ├── simple_deploy.yml
│   └── multi_node_deploy.yml
├── run.py                       # ✅ 已有
├── requirements.txt             # ✅ 已有,需更新
├── setup.py                     # 🆕 安装脚本
├── README.md                    # 🆕 项目说明
└── .gitignore                   # ✅ 已有,需完善
```

### 2.2 文件变更清单

#### 需要扩展的文件
1. `deployer/config.py`: 添加节点配置解析、SSH 配置支持
2. `deployer/ctl.py`: 添加 `--tui` 和 `--dry-run` 参数
3. `deployer/template/deploy.yml`: 添加 port、SSH key 等配置项
4. `requirements.txt`: 添加新依赖

#### 需要新建的文件
- 核心模块: 7 个文件
- TUI 模块: 6 个文件
- 公共模块: 3 个文件
- Playbook: 4 个文件
- 测试: 5 个文件
- 文档: 4 个文件
- **总计**: 约 29 个新文件

---

## 3. 开发任务分解

### 3.1 任务优先级定义

| 优先级 | 说明 | 开发顺序 |
|--------|------|----------|
| **P0** | 核心功能,必须实现 | 第 1 周 |
| **P1** | 重要功能,应该实现 | 第 2 周 |
| **P2** | 可选功能,时间允许时实现 | 第 3 周或后续迭代 |

### 3.2 任务列表

#### 阶段 1: 基础设施搭建（第 1 周前半）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T1.1 | 完善项目结构,创建目录和空文件 | P0 | 0.5h | - |
| T1.2 | 更新 requirements.txt | P0 | 0.5h | - |
| T1.3 | 实现异常定义 (exceptions.py) | P0 | 1h | - |
| T1.4 | 实现工具函数 (utils.py) | P0 | 2h | - |
| T1.5 | 实现日志系统 (logger.py) | P0 | 3h | T1.3 |
| T1.6 | 编写单元测试框架 | P0 | 2h | - |

**小计**: 9 小时

#### 阶段 2: 配置和任务管理（第 1 周后半）

| 任务 ID | 任务名称 |优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T2.1 | 扩展 Config 类,支持新配置项 | P0 | 4h | T1.3 |
| T2.2 | 实现 NodeConfig 和 SoftwareConfig | P0 | 2h | T2.1 |
| T2.3 | 实现配置验证逻辑 | P0 | 3h | T2.1 |
| T2.4 | 更新配置模板 (deploy.yml) | P0 | 1h | T2.1 |
| T2.5 | 实现 TaskManager | P0 | 4h | T2.2 |
| T2.6 | 编写配置和任务管理测试 | P0 | 3h | T2.5 |

**小计**: 17 小时

#### 阶段 3: Ansible 集成（第 2 周前半）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T3.1 | 实现 AnsibleWrapper | P0 | 4h | T1.5 |
| T3.2 | 实现 BaseInstaller 基类 | P0 | 3h | T3.1 |
| T3.3 | 编写 Java Playbook | P0 | 4h | - |
| T3.4 | 实现 JavaInstaller | P0 | 4h | T3.2, T3.3 |
| T3.5 | 编写 Python Playbook | P0 | 3h | - |
| T3.6 | 实现 PythonInstaller | P0 | 3h | T3.2, T3.5 |
| T3.7 | 编写 Zookeeper Playbook | P0 | 4h | - |
| T3.8 | 实现 ZookeeperInstaller | P0 | 4h | T3.2, T3.7 |
| T3.9 | 编写 Ansible 集成测试 | P1 | 4h | T3.8 |

**小计**: 33 小时

#### 阶段 4: 检查器实现（第 2 周中）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T4.1 | 实现 BaseChecker 基类 | P0 | 2h | T1.3 |
| T4.2 | 实现 ConnectivityChecker | P0 | 3h | T4.1, T3.1 |
| T4.3 | 实现 SoftwareStatusChecker | P0 | 3h | T4.1, T3.1 |
| T4.4 | 实现 SystemCompatibilityChecker | P1 | 3h | T4.1 |
| T4.5 | 实现 ResourceChecker | P1 | 3h | T4.1 |
| T4.6 | 实现 DependencyChecker | P1 | 3h | T4.1 |
| T4.7 | 实现 PreCheckManager | P0 | 2h | T4.6 |
| T4.8 | 编写检查器测试 | P1 | 3h | T4.7 |

**小计**: 22 小时

#### 阶段 5: 执行引擎（第 2 周后半）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T5.1 | 实现 DeploymentExecutor 核心逻辑 | P0 | 6h | T2.5, T4.7 |
| T5.2 | 实现多线程并发控制 | P0 | 4h | T5.1 |
| T5.3 | 实现暂停/恢复/停止功能 | P1 | 3h | T5.2 |
| T5.4 | 实现回调机制 | P0 | 2h | T5.1 |
| T5.5 | 集成 Installer 和 Checker | P0 | 3h | T5.1, T3.8, T4.7 |
| T5.6 | 实现错误处理和隔离 | P0 | 4h | T5.5 |
| T5.7 | 编写执行器测试 | P0 | 4h | T5.6 |

**小计**: 26 小时

#### 阶段 6: CLI 界面（第 2 周末）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T6.1 | 扩展 ctl.py,添加新命令参数 | P0 | 2h | T5.6 |
| T6.2 | 实现 CLI 模式部署流程 | P0 | 3h | T6.1 |
| T6.3 | 实现 --dry-run 模式 | P1 | 2h | T6.2 |
| T6.4 | 使用 Rich 美化 CLI 输出 | P1 | 3h | T6.2 |
| T6.5 | 实现进度显示和统计 | P1 | 2h | T6.4 |

**小计**: 12 小时

#### 阶段 7: TUI 界面（第 3 周前半）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T7.1 | 实现 NodeTree 组件 | P0 | 4h | - |
| T7.2 | 实现 ProgressPanel 组件 | P0 | 3h | - |
| T7.3 | 实现 LogViewer 组件 | P0 | 4h | - |
| T7.4 | 实现 MainScreen 布局 | P0 | 3h | T7.1, T7.2, T7.3 |
| T7.5 | 实现 DeployApp 主应用 | P0 | 4h | T7.4 |
| T7.6 | 集成 Executor 回调 | P0 | 3h | T7.5, T5.4 |
| T7.7 | 实现快捷键交互 | P1 | 2h | T7.5 |
| T7.8 | 编写 CSS 样式 | P1 | 3h | T7.5 |
| T7.9 | 实现日志过滤功能 | P2 | 2h | T7.3 |
| T7.10 | 实现主题切换 | P2 | 2h | T7.8 |

**小计**: 30 小时

#### 阶段 8: 测试和文档（第 3 周后半）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T8.1 | 补充单元测试,达到 80% 覆盖率 | P0 | 8h | 所有模块 |
| T8.2 | 编写集成测试 | P1 | 6h | 所有模块 |
| T8.3 | 端到端测试（真实环境） | P0 | 4h | 所有模块 |
| T8.4 | 编写 README.md | P0 | 2h | - |
| T8.5 | 编写用户手册 | P0 | 4h | - |
| T8.6 | 编写开发者指南 | P1 | 3h | - |
| T8.7 | 代码审查和重构 | P1 | 4h | - |
| T8.8 | 性能测试和优化 | P1 | 3h | T8.3 |

**小计**: 34 小时

#### 阶段 9: 打包和发布（第 3 周末）

| 任务 ID | 任务名称 | 优先级 | 预计工时 | 依赖 |
|---------|----------|--------|----------|------|
| T9.1 | 编写 setup.py | P0 | 2h | - |
| T9.2 | 创建示例配置文件 | P0 | 1h | - |
| T9.3 | 完善 .gitignore | P0 | 0.5h | - |
| T9.4 | 准备发布版本 | P0 | 1h | T9.1 |
| T9.5 | 编写 CHANGELOG | P1 | 1h | - |

**小计**: 5.5 小时

---

### 3.3 工时统计

| 阶段 | P0 任务工时 | P1 任务工时 | P2 任务工时 | 总计 |
|------|-------------|-------------|-------------|------|
| 阶段 1 | 9h | 0h | 0h | 9h |
| 阶段 2 | 17h | 0h | 0h | 17h |
| 阶段 3 | 29h | 4h | 0h | 33h |
| 阶段 4 | 13h | 9h | 0h | 22h |
| 阶段 5 | 23h | 3h | 0h | 26h |
| 阶段 6 | 5h | 7h | 0h | 12h |
| 阶段 7 | 21h | 5h | 4h | 30h |
| 阶段 8 | 18h | 16h | 0h | 34h |
| 阶段 9 | 4.5h | 1h | 0h | 5.5h |
| **总计** | **139.5h** | **45h** | **4h** | **188.5h** |

**换算**:
- P0 任务: 139.5h ≈ **17.4 工作日**（按 8h/天）
- P0 + P1 任务: 184.5h ≈ **23 工作日**
- 全部任务: 188.5h ≈ **23.6 工作日**

---

## 4. 开发时间线

### 4.1 三周开发计划

#### 第 1 周: 基础设施和核心模块

| 日期 | 任务 | 目标 |
|------|------|------|
| Day 1-2 | T1.1 - T1.6 | 完成基础设施搭建 |
| Day 3-4 | T2.1 - T2.6 | 完成配置和任务管理 |
| Day 5 | T3.1 - T3.2 | 完成 Ansible 封装和基类 |

**里程碑 1**: 配置管理和任务管理模块可用

#### 第 2 周: Ansible 集成和执行引擎

| 日期 | 任务 | 目标 |
|------|------|------|
| Day 1-2 | T3.3 - T3.8 | 完成三个安装器 |
| Day 3 | T4.1 - T4.7 | 完成检查器 |
| Day 4-5 | T5.1 - T5.7 | 完成执行引擎 |

**里程碑 2**: 核心部署功能可用（CLI 模式）

#### 第 3 周: TUI 界面和测试

| 日期 | 任务 | 目标 |
|------|------|------|
| Day 1 | T6.1 - T6.5 | 完成 CLI 界面 |
| Day 2-3 | T7.1 - T7.8 | 完成 TUI 界面 |
| Day 4 | T8.1 - T8.3 | 完成测试 |
| Day 5 | T8.4 - T9.4 | 完成文档和打包 |

**里程碑 3**: 项目完成,可发布

### 4.2 弹性调整

- 如果时间紧张,可以推迟 P2 任务到后续迭代
- 如果进度超前,可以提前实现 P2 任务或增加测试覆盖率

---

## 5. 测试策略

### 5.1 单元测试

#### 测试覆盖目标
- **总体覆盖率**: ≥ 80%
- **核心模块覆盖率**: ≥ 90%

#### 测试框架
- 使用 `pytest` 作为测试框架
- 使用 `pytest-cov` 生成覆盖率报告
- 使用 `pytest-mock` 进行 Mock

#### 测试清单

| 模块 | 测试文件 | 测试内容 |
|------|----------|----------|
| config.py | test_config.py | 配置解析、验证、错误处理 |
| task_manager.py | test_task_manager.py | 任务创建、状态更新、统计 |
| checker.py | test_checker.py | 各检查器逻辑、结果判断 |
| executor.py | test_executor.py | 并发控制、错误隔离、回调 |
| ansible_wrapper.py | test_ansible_wrapper.py | Playbook 执行、连接检查 |
| installers/ | test_installers.py | 各安装器的安装逻辑 |
| logger.py | test_logger.py | 日志记录、文件轮转 |
| utils.py | test_utils.py | 工具函数 |

### 5.2 集成测试

#### 测试场景
1. **配置加载 → 任务创建 → 执行器初始化**
2. **检查器 → 安装器 → Ansible 执行**
3. **执行器 → TUI 回调 → 界面更新**

#### 测试环境
- 使用 Docker 容器模拟目标节点
- 使用 Mock 服务器模拟软件下载

### 5.3 端到端测试

#### 测试用例
1. **单节点单软件部署**
   - 配置: 1 个节点,安装 Java
   - 预期: 成功安装,TUI 显示正常

2. **多节点多软件部署**
   - 配置: 3 个节点,每个安装 Java + Python
   - 预期: 并发执行,全部成功

3. **错误场景测试**
   - 场景 1: SSH 连接失败
   - 场景 2: 磁盘空间不足
   - 场景 3: 软件已安装
   - 预期: 正确处理错误,不影响其他节点

4. **暂停/恢复测试**
   - 操作: 部署过程中暂停,然后恢复
   - 预期: 正确暂停和恢复

### 5.4 性能测试

#### 测试指标
- **并发性能**: 10 个节点并发部署,总耗时 < 单节点串行的 30%
- **TUI 响应**: 界面刷新率 ≥ 10 FPS
- **内存占用**: < 500MB（10 个节点）

---

## 6. 依赖管理

### 6.1 Python 依赖

更新 `requirements.txt`:

```txt
# 已有依赖
ansible_runner<=2.3.6
ansible<=8.5.0
click<=8.1.8
textual<=0.47.0
pyyaml<=6.0.3

# 新增依赖
rich>=13.0.0           # CLI 美化输出
pytest>=7.4.0          # 测试框架
pytest-cov>=4.1.0      # 覆盖率
pytest-mock>=3.11.1    # Mock
paramiko>=3.3.0        # SSH 连接（Ansible 依赖）
```

### 6.2 系统依赖

控制端需要:
- Python 3.8+
- SSH 客户端
- Ansible（通过 pip 安装）

目标节点需要:
- Python 2.7+ 或 3.x（Ansible 要求）
- SSH 服务

---

## 7. 风险管理

### 7.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Ansible Runner 兼容性问题 | 高 | 中 | 提前测试,准备降级方案 |
| Textual 学习曲线陡峭 | 中 | 高 | 先实现简单 TUI,逐步完善 |
| 多线程并发 Bug | 高 | 中 | 充分测试,使用成熟的并发库 |
| Playbook 编写复杂 | 中 | 中 | 参考官方文档,使用简单任务 |

### 7.2 进度风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 工时估算不准确 | 中 | 高 | 预留 20% 缓冲时间 |
| 需求变更 | 高 | 中 | 锁定核心需求,扩展功能后置 |
| 测试环境搭建困难 | 中 | 中 | 使用 Docker,简化环境 |

### 7.3 质量风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 测试覆盖率不足 | 高 | 中 | 强制要求 80% 覆盖率 |
| 代码质量差 | 中 | 中 | 使用 Pylint,定期 Code Review |
| 文档不完善 | 中 | 高 | 边开发边写文档 |

---

## 8. 交付物清单

### 8.1 代码交付物
- [ ] 完整的源代码（约 30 个模块文件）
- [ ] 单元测试（覆盖率 ≥ 80%）
- [ ] 集成测试
- [ ] 端到端测试

### 8.2 Playbook 交付物
- [ ] install_java.yml
- [ ] install_python.yml
- [ ] install_zookeeper.yml
- [ ] check_connection.yml

### 8.3 文档交付物
- [ ] README.md（项目说明）
- [ ] 用户手册（如何使用）
- [ ] 开发者指南（如何扩展）
- [ ] API 文档（自动生成）
- [ ] CHANGELOG（版本记录）

### 8.4 配置交付物
- [ ] 配置模板（deploy.yml）
- [ ] 示例配置（examples/）
- [ ] setup.py（安装脚本）

---

## 9. 验收标准

### 9.1 功能验收

#### 必须通过（P0）
- [x] 配置文件正确解析,支持 SSH 端口和密钥
- [ ] 成功部署 Java、Python、Zookeeper
- [ ] 支持 10 个节点并发部署
- [ ] 安装前检查正常工作
- [ ] 单节点失败不影响其他节点
- [ ] TUI 界面正常显示和更新
- [ ] CLI 模式正常工作

#### 应该通过（P1）
- [ ] Dry-run 模式正常工作
- [ ] 日志文件正确记录
- [ ] 暂停/恢复功能正常
- [ ] 错误提示清晰

### 9.2 性能验收
- [ ] 10 个节点并发,总耗时 < 单节点串行的 30%
- [ ] TUI 界面流畅,无卡顿
- [ ] 内存占用 < 500MB

### 9.3 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] Pylint 评分 ≥ 8.0
- [ ] 无严重 Bug
- [ ] 文档完整

---

## 10. 后续迭代计划

### 10.1 版本 0.2.0（未来 1-2 个月）
- [ ] 支持更多软件（MySQL、Redis、Nginx、Tomcat）
- [ ] 支持自定义 Playbook
- [ ] 支持失败重试机制
- [ ] 支持部署报告导出（HTML、PDF）

### 10.2 版本 0.3.0（未来 3-6 个月）
- [ ] 支持配置文件加密
- [ ] 支持断点续传
- [ ] 支持 Web 界面
- [ ] 支持插件机制

---

## 11. 附录

### 11.1 开发环境配置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ --cov=deployer --cov-report=html

# 代码检查
pylint deployer/
```

### 11.2 Git 工作流

- **主分支**: `main`（稳定版本）
- **开发分支**: `develop`（开发版本）
- **功能分支**: `feature/xxx`（新功能）
- **修复分支**: `bugfix/xxx`（Bug 修复）

### 11.3 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `style`: 代码格式

**示例**:
```
feat(executor): implement multi-threaded deployment

- Add ThreadPoolExecutor for concurrent execution
- Implement pause/resume/stop functionality
- Add callback mechanism for TUI integration

Closes #123
```

---

**文档结束**
