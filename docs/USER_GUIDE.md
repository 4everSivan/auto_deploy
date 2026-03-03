# Auto Deploy User Guide

Auto Deploy is a powerful, TUI-driven tool designed to automate the deployment of software (like Java, Python, and Zookeeper) across multiple remote servers using Ansible under the hood.

## 1. Installation

### Prerequisites
- Python 3.9+
- Ansible installed on the control node
- SSH access to target nodes

### Setup
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Configuration (`config.yml`)

The configuration file defines the deployment environment and the software to be installed.

### Schema Overview
```yaml
max_concurrent_nodes: 5  # Number of nodes to deploy to simultaneously

nodes:
  - node_name:          # Unique identifier for the node
      host: 192.168.1.1 # remote IP or hostname
      port: 22          # SSH port (default: 22)
      owner_user: sivan # SSH user
      owner_pass: pass  # SSH password (or use owner_key)
      super_user: root  # Sudo user (default: root)
      super_pass: pass  # Sudo password
      install:          # List of software to install
        - java:
            version: "11"
            install_path: /opt/java
        - zookeeper:
            version: "3.7.0"
            install_path: /opt/zookeeper
```

### Software-Specific Options
- **Java**: Supports standard version strings (e.g., "11", "8").
- **Python**: Supports minor version strings (e.g., "3.9", "3.10").
- **Zookeeper**: Requires `version` and `install_path`.

## 3. CLI Usage

Run the deployment via `run.py`:

```bash
python run.py -c your_config.yml deploy [options]
```

### Global Options
- `-c`, `--config`: Path to your YAML configuration file (Required).
- `--debug`: Enable verbose debug logging.

### Command Options: `deploy`
- `--dry-run`: Validate configuration and connectivity without actually installing.
- `--tui`: Launch the interactive Terminal User Interface (Recommended).
- `--node <name>`: Deploy to a specific node only.

## 4. TUI Features

When running with `--tui`, you'll see a dashboard with:
- **Node Status Tree**: Real-time progress of each node and its tasks.
- **Overall Progress**: Global completion percentage and elapsed time.
- **Task Details**: Detailed view of the currently active task.
- **Live Logs**: Streaming output from the deployment process.

### Keyboard Shortcuts
- `S`: Start deployment.
- `P`: Pause execution.
- `R`: Resume execution.
- `Q`: Quit (gracefully stops active tasks).

## 5. Troubleshooting

### Connection Issues
- Ensure `owner_user` has SSH access to the host.
- Verify that `ANSIBLE_HOST_KEY_CHECKING` is handled (Auto Deploy sets this to `False` by default).

### Installation Failures
- Check the "Live Logs" in the TUI for specific error messages.
- Ensure the `install_path` has sufficient permissions for the `super_user`.

### App Hanging
- If the TUI hangs, you can press `Ctrl+C` in the terminal to force exit, but using `Q` is preferred for clean-up.
