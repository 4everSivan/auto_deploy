# Auto Deploy 用户指南

Auto Deploy 是一个功能强大、由 TUI 驱动的工具,旨在利用底层的 Ansible 自动化地在多个远程服务器上部署软件（如 Java、Python 和 Zookeeper）。

## 1. 安装

### 前提条件
- Python 3.9+
- 控制节点已安装 Ansible
- 具有目标节点的 SSH 访问权限

### 安装步骤
1. 克隆仓库。
2. 创建并激活虚拟环境:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

## 2. 配置 (`deploy.yml`)

配置文件定义了部署环境和待安装的软件。

### 结构概览
```yaml
general:
  max_concurrent_nodes: 5  # 同时部署的最大节点数
  data_dir: "./deploy_data" # 数据存储目录

nodes:
  - node_name:          # 节点的唯一标识符
      host: 192.168.1.1 # 远程 IP 或主机名
      port: 22          # SSH 端口（默认: 22）
      owner_user: sivan # SSH 用户
      owner_pass: pass  # SSH 密码（或使用 owner_key）
      super_user: root  # Sudo 用户（默认: root）
      super_pass: pass  # Sudo 密码
      install:          # 待安装软件列表
        - java:
            version: "11"
            install_path: /opt/java
        - zookeeper:
            version: "3.7.0"
            install_path: /opt/zookeeper
```

### 软件特定选项
- **Java**: 支持标准版本字符串（如 "11"、"8"）。
- **Python**: 支持小版本字符串（如 "3.9"、"3.10"）。
- **Zookeeper**: 需要 `version` 和 `install_path`。

## 3. 命令行用法

通过 `run.py` 运行部署:

```bash
python run.py -c your_config.yml deploy [选项]
```

### 全局选项
- `-c`, `--config`: YAML 配置文件路径（必填）。
- `--debug`: 启用详细调试日志。

### 命令选项: `deploy`
- `--dry-run`: 验证配置和连通性,不实际进行安装。
- `--tui`: 启动交互式终端用户界面（推荐）。
- `--node <name>`: 仅部署到特定节点。

## 4. TUI 特性

使用 `--tui` 运行时,您将看到一个包含以下内容的仪表盘:
- **节点状态树**: 各节点及其任务的实时进度。
- **总体进度**: 全局完成百分比和已用时间。
- **任务详情**: 当前活动任务的详细视图。
- **实时日志**: 部署过程的流式输出。

### 快捷键
- `S`: 开始部署。
- `P`: 暂停执行。
- `R`: 继续执行。
- `Q`: 退出（优雅地停止活动任务）。

## 5. 故障排除

### 连接问题
- 确保 `owner_user` 具有主机的 SSH 访问权限。
- 确认已处理 `ANSIBLE_HOST_KEY_CHECKING`（Auto Deploy 默认将其设置为 `False`）。

### 安装失败
- 查看 TUI 中的 “实时日志” 以获取特定错误消息。
- 确保 `install_path` 对于 `super_user` 具有足够的权限。

### 应用挂起
- 如果 TUI 挂起,您可以在终端中按 `Ctrl+C` 强制退出,但首选使用 `Q` 进行清理。
