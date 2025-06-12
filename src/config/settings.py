"""
Configuration settings for Dirsearch MCP
"""
from typing import Dict, Any, Optional
from pathlib import Path
import os
import json


class Settings:
    """Application settings and configuration"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Default configuration
        self.default_scan_config = {
            'threads': 10,
            'timeout': 10,
            'delay': 0,
            'user_agent': 'Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)',
            'follow_redirects': True,
            'retry_attempts': 3,
            'exclude_status': '404',
            'include_status': None,
            'batch_size': 50
        }
        
        # AI configuration
        self.ai_config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY', ''),
            'openai_model': 'gpt-3.5-turbo',
            'deepseek_model': 'deepseek-chat',
            'enable_ai': True
        }
        
        # Paths configuration
        self.paths = {
            'wordlists': str(Path(__file__).parent.parent.parent / 'wordlists'),
            'reports': str(Path(__file__).parent.parent.parent / 'report'),
            'logs': str(Path(__file__).parent.parent.parent / 'log'),
            'cache': str(Path(__file__).parent.parent.parent / '.cache')
        }
        
        # Performance settings
        self.performance = {
            'max_concurrent_requests': 100,
            'connection_pool_size': 100,
            'request_queue_size': 1000,
            'progress_update_interval': 0.5
        }
        
        # MCP settings
        self.mcp_config = {
            'mode': 'auto',  # auto, local, ai
            'confidence_threshold': 0.7,
            'enable_learning': True,
            'cache_ai_responses': True,
            'ai_timeout': 30
        }
        
        # Load from config file if provided
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            # Update configurations
            if 'scan' in config_data:
                self.default_scan_config.update(config_data['scan'])
            if 'ai' in config_data:
                self.ai_config.update(config_data['ai'])
            if 'paths' in config_data:
                self.paths.update(config_data['paths'])
            if 'performance' in config_data:
                self.performance.update(config_data['performance'])
            if 'mcp' in config_data:
                self.mcp_config.update(config_data['mcp'])
                
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file"""
        config_data = {
            'scan': self.default_scan_config,
            'ai': self.ai_config,
            'paths': self.paths,
            'performance': self.performance,
            'mcp': self.mcp_config
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        # Split key by dots
        parts = key.split('.')
        
        # Navigate through nested config
        value = self.__dict__
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key"""
        # Split key by dots
        parts = key.split('.')
        
        # Navigate to parent
        parent = self.__dict__
        for part in parts[:-1]:
            if isinstance(parent, dict):
                if part not in parent:
                    parent[part] = {}
                parent = parent[part]
            else:
                parent = getattr(parent, part)
        
        # Set value
        if isinstance(parent, dict):
            parent[parts[-1]] = value
        else:
            setattr(parent, parts[-1], value)
    
    def ensure_directories(self):
        """Ensure all configured directories exist"""
        for path_key, path_value in self.paths.items():
            Path(path_value).mkdir(parents=True, exist_ok=True)


# For backward compatibility
Config = Settings