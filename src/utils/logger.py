import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import colorama
from colorama import Fore, Back, Style
import sys
import time
from threading import Lock


colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        # Add color to the log level
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        
        # Add color to specific message types
        if hasattr(record, 'msg_type'):
            if record.msg_type == 'success':
                record.msg = f"{Fore.GREEN} {record.msg}{Style.RESET_ALL}"
            elif record.msg_type == 'progress':
                record.msg = f"{Fore.BLUE}▶ {record.msg}{Style.RESET_ALL}"
            elif record.msg_type == 'decision':
                record.msg = f"{Fore.MAGENTA}🎯 {record.msg}{Style.RESET_ALL}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'pathname', 'process', 
                          'processName', 'relativeCreated', 'thread', 
                          'threadName', 'getMessage']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class ProgressLogger:
    """Handle progress indicators and animations"""
    
    def __init__(self):
        self.active_tasks = {}
        self.lock = Lock()
        
    def start_progress(self, task_id: str, description: str):
        """Start a progress indicator"""
        with self.lock:
            self.active_tasks[task_id] = {
                'description': description,
                'start_time': time.time(),
                'updates': 0
            }
            print(f"{Fore.BLUE}[START] {description}{Style.RESET_ALL}")
    
    def update_progress(self, task_id: str, current: int, total: int, suffix: str = ''):
        """Update progress with percentage"""
        with self.lock:
            if task_id not in self.active_tasks:
                return
            
            percent = (current / total) * 100 if total > 0 else 0
            filled = int(percent // 2)
            bar = '�' * filled + '�' * (50 - filled)
            
            elapsed = time.time() - self.active_tasks[task_id]['start_time']
            
            # Clear line and print progress
            sys.stdout.write('\r')
            sys.stdout.write(f"{Fore.BLUE}[{bar}] {percent:.1f}% - {suffix} ({elapsed:.1f}s){Style.RESET_ALL}")
            sys.stdout.flush()
    
    def end_progress(self, task_id: str, status: str = 'COMPLETED'):
        """End a progress indicator"""
        with self.lock:
            if task_id not in self.active_tasks:
                return
            
            task = self.active_tasks[task_id]
            elapsed = time.time() - task['start_time']
            
            # Clear line
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            
            if status == 'COMPLETED':
                print(f"{Fore.GREEN}[] {task['description']} - Completed in {elapsed:.1f}s{Style.RESET_ALL}")
            elif status == 'FAILED':
                print(f"{Fore.RED}[] {task['description']} - Failed after {elapsed:.1f}s{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] {task['description']} - {status} ({elapsed:.1f}s){Style.RESET_ALL}")
            
            del self.active_tasks[task_id]


class LoggerSetup:
    """Centralized logger setup and management"""
    
    _instance = None
    _loggers = {}
    _log_dir = None
    _progress_logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerSetup, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._progress_logger = ProgressLogger()
    
    @classmethod
    def initialize(cls, log_dir: str = "log"):
        """Initialize logging system"""
        instance = cls()
        instance._log_dir = Path(log_dir)
        instance._log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ['mcp', 'scan', 'performance', 'errors']:
            (instance._log_dir / subdir).mkdir(exist_ok=True)
    
    @classmethod
    def get_logger(cls, name: str, log_type: str = 'general') -> logging.Logger:
        """Get or create a logger instance"""
        instance = cls()
        
        if name in instance._loggers:
            return instance._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.handlers = []  # Clear existing handlers
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handlers based on log type
        if instance._log_dir:
            # Main log file for the type
            if log_type == 'mcp':
                log_file = instance._log_dir / 'mcp' / 'mcp_decisions.log'
            elif log_type == 'scan':
                log_file = instance._log_dir / 'scan' / 'scan_activities.log'
            elif log_type == 'performance':
                log_file = instance._log_dir / 'performance' / 'performance.log'
            elif log_type == 'error':
                log_file = instance._log_dir / 'errors' / 'errors.log'
            else:
                safe_name = name if name else 'default'
                log_file = instance._log_dir / f'{safe_name.replace(".", "_")}.log'
            
            # Regular file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # JSON file handler for structured logs
            json_file = log_file.with_suffix('.json')
            json_handler = logging.handlers.RotatingFileHandler(
                json_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(StructuredFormatter())
            logger.addHandler(json_handler)
            
            # Error file handler (captures all errors)
            if log_type != 'error':
                error_file = instance._log_dir / 'errors' / 'all_errors.log'
                error_handler = logging.handlers.RotatingFileHandler(
                    error_file,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(file_formatter)
                logger.addHandler(error_handler)
        
        instance._loggers[name] = logger
        return logger
    
    @classmethod
    def get_mcp_logger(cls) -> logging.Logger:
        """Get logger for MCP decisions"""
        return cls.get_logger('mcp.coordinator', 'mcp')
    
    @classmethod
    def get_scan_logger(cls) -> logging.Logger:
        """Get logger for scan activities"""
        return cls.get_logger('scan.engine', 'scan')
    
    @classmethod
    def get_performance_logger(cls) -> logging.Logger:
        """Get logger for performance metrics"""
        return cls.get_logger('performance.metrics', 'performance')
    
    @classmethod
    def get_error_logger(cls) -> logging.Logger:
        """Get logger for error tracking"""
        return cls.get_logger('error.tracker', 'error')
    
    @classmethod
    def get_progress_logger(cls) -> ProgressLogger:
        """Get progress logger instance"""
        instance = cls()
        return instance._progress_logger
    
    @classmethod
    def log_mcp_decision(cls, decision_type: str, context: Dict[str, Any], 
                        decision: str, confidence: float = 1.0):
        """Log MCP coordinator decision"""
        logger = cls.get_mcp_logger()
        logger.info(
            f"MCP Decision: {decision_type}",
            extra={
                'msg_type': 'decision',
                'decision_type': decision_type,
                'context': context,
                'decision': decision,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    @classmethod
    def log_performance_metric(cls, metric_name: str, value: float, 
                             unit: str = '', context: Dict[str, Any] = None):
        """Log performance metric"""
        logger = cls.get_performance_logger()
        logger.info(
            f"Performance: {metric_name} = {value} {unit}",
            extra={
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }
        )
    
    @classmethod
    def cleanup_old_logs(cls, days: int = 30):
        """Clean up logs older than specified days"""
        instance = cls()
        if not instance._log_dir:
            return
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for log_file in instance._log_dir.rglob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    print(f"Deleted old log file: {log_file}")
                except Exception as e:
                    print(f"Error deleting {log_file}: {e}")


class LogContext:
    """Context manager for structured logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(
            f"Starting: {self.operation}",
            extra={
                'operation': self.operation,
                'phase': 'start',
                **self.context
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(
                f"Completed: {self.operation} ({elapsed:.2f}s)",
                extra={
                    'operation': self.operation,
                    'phase': 'complete',
                    'elapsed_time': elapsed,
                    **self.context
                }
            )
        else:
            self.logger.error(
                f"Failed: {self.operation} ({elapsed:.2f}s) - {exc_val}",
                extra={
                    'operation': self.operation,
                    'phase': 'error',
                    'elapsed_time': elapsed,
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val),
                    **self.context
                }
            )
    
    def update(self, **kwargs):
        """Update context during operation"""
        self.context.update(kwargs)


# Initialize logging on import
LoggerSetup.initialize()