"""
Logging system for the auto-deploy project.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict
from common.utils import ensure_dir, sanitize_log_message


class DeployLogger:
    """Deployment logger manager with support for main and per-node logging."""
    
    def __init__(self, log_dir: str, log_level: str = "INFO"):
        """
        Initialize logger manager.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = ensure_dir(log_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Main logger
        self.main_logger = self._create_logger(
            "deploy",
            self.log_dir / "deploy.log"
        )
        
        # Node loggers cache
        self.node_loggers: Dict[str, logging.Logger] = {}
    
    def _create_logger(self, name: str, log_file: Path) -> logging.Logger:
        """
        Create a logger with file handler and rotation.
        
        Args:
            name: Logger name
            log_file: Path to log file
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler with rotation (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_node_logger(self, node_name: str) -> logging.Logger:
        """
        Get or create a logger for a specific node.
        
        Args:
            node_name: Name of the node
            
        Returns:
            Logger for the node
        """
        if node_name not in self.node_loggers:
            log_file = self.log_dir / f"{node_name}.log"
            self.node_loggers[node_name] = self._create_logger(
                f"deploy.{node_name}",
                log_file
            )
        return self.node_loggers[node_name]
    
    def log(self, level: str, message: str, node: Optional[str] = None, 
            sanitize: bool = True) -> None:
        """
        Log a message.
        
        Args:
            level: Log level (debug, info, warning, error)
            message: Log message
            node: Optional node name for node-specific logging
            sanitize: Whether to sanitize sensitive information
        """
        if sanitize:
            message = sanitize_log_message(message)
        
        logger = self.main_logger
        if node:
            logger = self.get_node_logger(node)
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message)
    
    def debug(self, message: str, node: Optional[str] = None) -> None:
        """Log debug message."""
        self.log('debug', message, node)
    
    def info(self, message: str, node: Optional[str] = None) -> None:
        """Log info message."""
        self.log('info', message, node)
    
    def warning(self, message: str, node: Optional[str] = None) -> None:
        """Log warning message."""
        self.log('warning', message, node)
    
    def error(self, message: str, node: Optional[str] = None) -> None:
        """Log error message."""
        self.log('error', message, node)
    
    def exception(self, message: str, node: Optional[str] = None) -> None:
        """Log exception with traceback."""
        logger = self.main_logger if not node else self.get_node_logger(node)
        logger.exception(sanitize_log_message(message))
