"""
Intelligent Scanner Module - Advanced rule-based endpoint discovery
Optimizes scan performance by intelligently expanding wordlists based on discovered paths
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class EndpointRule:
    """Rule for intelligent endpoint expansion"""
    pattern: str  # Regex pattern to match discovered paths
    priority: int  # Higher priority = scan first
    keywords: List[str]  # Keywords to add to wordlist
    extensions: List[str] = field(default_factory=list)  # Specific extensions to try
    recursive: bool = True  # Whether to scan recursively
    description: str = ""  # Rule description


class IntelligentScanner:
    """Advanced rule-based scanner for optimized endpoint discovery"""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.discovered_patterns = set()
        self.priority_queue = []
        
    def _initialize_rules(self) -> Dict[str, EndpointRule]:
        """Initialize comprehensive rule set for intelligent scanning"""
        return {
            # Admin endpoints - HIGHEST PRIORITY
            'admin': EndpointRule(
                pattern=r'/(admin|administrator|administration|manage|manager|control|cpanel)',
                priority=100,
                keywords=[
                    'login', 'dashboard', 'panel', 'config', 'users', 'settings',
                    'backup', 'db', 'database', 'cpanel', 'phpmyadmin', 'adminer',
                    'console', 'portal', 'system', 'index', 'home', 'main',
                    'users/list', 'users/add', 'users/edit', 'users/delete',
                    'settings/general', 'settings/security', 'settings/backup',
                    'logs', 'audit', 'reports', 'analytics', 'stats'
                ],
                extensions=['php', 'asp', 'aspx', 'jsp', 'do', 'action'],
                description="Administrative interfaces - critical priority"
            ),
            
            # API endpoints - HIGH PRIORITY
            'api': EndpointRule(
                pattern=r'/(api|rest|graphql|endpoint|service|v\d+)',
                priority=90,
                keywords=[
                    'swagger.json', 'openapi.yaml', 'openapi.json', 'api-docs',
                    'v1', 'v2', 'v3', 'latest', 'users', 'auth', 'authentication',
                    'token', 'tokens', 'refresh', 'login', 'logout', 'register',
                    'graphql', 'query', 'mutation', 'subscription', 'schema',
                    'docs', 'documentation', 'health', 'healthcheck', 'status',
                    'metrics', 'info', 'version', 'ping', 'heartbeat',
                    'users/me', 'users/profile', 'users/list', 'users/search',
                    'auth/login', 'auth/refresh', 'auth/verify', 'auth/forgot',
                    'search', 'filter', 'sort', 'paginate', 'export', 'import'
                ],
                extensions=['json', 'yaml', 'yml', 'xml'],
                description="API endpoints - REST/GraphQL/SOAP"
            ),
            
            # Development/Debug - HIGH PRIORITY
            'dev': EndpointRule(
                pattern=r'/(dev|development|debug|test|testing|stage|staging|beta|alpha)',
                priority=85,
                keywords=[
                    'test', 'staging', 'beta', 'debug', 'dev.zip', 'backup.zip',
                    '.git', '.svn', '.hg', '.bzr', 'composer.json', 'package.json',
                    'phpinfo.php', 'info.php', 'test.php', 'debug.php', 'env.php',
                    'config.php', 'configuration.php', 'settings.php', 'setup.php',
                    'install', 'installer', 'setup', 'migration', 'update',
                    'console', 'shell', 'terminal', 'cmd', 'exec', 'eval',
                    'logs', 'log', 'error_log', 'debug.log', 'app.log',
                    'stacktrace', 'trace', 'dump', 'var_dump', 'print_r'
                ],
                extensions=['php', 'log', 'txt', 'zip', 'tar', 'gz', 'sql'],
                description="Development and debug endpoints"
            ),
            
            # Backup files - HIGH PRIORITY
            'backup': EndpointRule(
                pattern=r'/(backup|bak|back|save|old|archive|dump)',
                priority=85,
                keywords=[
                    'db.sql', 'database.sql', 'dump.sql', 'backup.sql',
                    'site.zip', 'website.zip', 'www.zip', 'public_html.zip',
                    'site.tar.gz', 'backup.tar.gz', 'archive.tar.gz',
                    'backup.tar', 'backup.rar', 'backup.7z',
                    'code-old', 'site-old', 'www-old', 'admin-old',
                    'wp-backup.zip', 'wordpress.zip', 'joomla.zip',
                    '.bak', '.old', '.save', '.orig', '.original',
                    'yesterday', 'latest', 'current', 'previous',
                    '2023', '2024', '2025', 'backup_2024', 'backup_2025'
                ],
                extensions=['sql', 'zip', 'tar', 'gz', 'rar', '7z', 'bak', 'old'],
                description="Backup and archive files"
            ),
            
            # Version control - HIGH PRIORITY
            'vcs': EndpointRule(
                pattern=r'/(\\.git|\\.svn|\\.hg|CVS|\\.bzr|_darcs)',
                priority=80,
                keywords=[
                    'HEAD', 'config', 'index', 'objects', 'refs', 'logs',
                    'COMMIT_EDITMSG', 'description', 'hooks', 'info',
                    'branches', 'tags', 'master', 'main', 'develop',
                    '.gitignore', '.gitmodules', '.gitattributes',
                    'entries', 'all-wcprops', 'props', 'text-base',
                    'prop-base', 'pristine', 'wc.db', 'format'
                ],
                extensions=[],
                description="Version control system files"
            ),
            
            # Authentication endpoints
            'auth': EndpointRule(
                pattern=r'/(login|signin|auth|authenticate|sso|oauth|saml)',
                priority=75,
                keywords=[
                    'auth', 'authenticate', 'authorization', 'reset', 'forgot',
                    'forgot-password', 'reset-password', 'change-password',
                    '2fa', 'two-factor', 'mfa', 'verify', 'verification',
                    'otp', 'one-time', 'check', 'validate', 'token',
                    'callback', 'redirect', 'return', 'success', 'failure',
                    'register', 'signup', 'create-account', 'join',
                    'logout', 'signout', 'exit', 'disconnect',
                    'session', 'cookie', 'remember', 'persistent'
                ],
                extensions=['php', 'asp', 'aspx', 'jsp', 'html'],
                description="Authentication and session endpoints"
            ),
            
            # CMS Detection
            'cms': EndpointRule(
                pattern=r'/(wordpress|wp|joomla|drupal|typo3|magento|prestashop|opencart)',
                priority=70,
                keywords=[
                    'wp-admin', 'wp-login.php', 'wp-content', 'wp-includes',
                    'wp-json', 'xmlrpc.php', 'wp-cron.php', 'wp-config.php',
                    'administrator', 'admin.php', 'configuration.php',
                    'components', 'modules', 'plugins', 'templates',
                    'sites/default', 'user/login', 'admin/config',
                    'index.php/admin', 'backend', 'adminhtml',
                    'media', 'var', 'pub/static', 'setup'
                ],
                extensions=['php'],
                description="Content Management System paths"
            ),
            
            # Configuration files
            'config': EndpointRule(
                pattern=r'/(config|configuration|settings|setup|install)',
                priority=75,
                keywords=[
                    'config.php', 'configuration.php', 'settings.php',
                    'config.json', 'settings.json', 'parameters.json',
                    'config.yml', 'config.yaml', 'application.yml',
                    '.env', '.env.local', '.env.production', '.env.development',
                    'database.ini', 'db.ini', 'database.php', 'database.yml',
                    'local.settings.php', 'settings.local.php',
                    'app.config', 'web.config', 'machine.config',
                    'parameters.yml', 'parameters.ini', 'secrets.yml'
                ],
                extensions=['php', 'json', 'yml', 'yaml', 'ini', 'xml', 'conf'],
                description="Configuration and settings files"
            ),
            
            # Upload directories
            'uploads': EndpointRule(
                pattern=r'/(upload|uploads|files|media|static|assets|content|resources)',
                priority=65,
                keywords=[
                    'test.jpg', 'test.png', 'test.txt', 'test.pdf',
                    'shell.php', 'cmd.php', 'c99.php', 'r57.php',
                    'old.zip', 'backup.zip', 'files.zip', 'data.zip',
                    '.env', '.htaccess', '.htpasswd', 'web.config',
                    'logs', 'error.log', 'access.log', 'debug.log',
                    'temp', 'tmp', 'cache', 'sessions',
                    'images', 'documents', 'downloads', 'attachments',
                    'avatar', 'profile', 'user_uploads'
                ],
                extensions=['jpg', 'png', 'gif', 'pdf', 'zip', 'txt', 'log'],
                description="Upload and static file directories"
            ),
            
            # Monitoring/Metrics
            'monitoring': EndpointRule(
                pattern=r'/(monitor|monitoring|metrics|status|health|stats|statistics)',
                priority=60,
                keywords=[
                    'metrics', 'prometheus', 'grafana', 'status', 'health',
                    'healthcheck', 'health-check', 'alive', 'ready', 'live',
                    'debug/pprof', 'debug/vars', 'debug/requests',
                    'actuator', 'actuator/health', 'actuator/metrics',
                    'actuator/info', 'actuator/env', 'actuator/beans',
                    '_stats', '_cluster/health', '_nodes', '_status',
                    'server-status', 'nginx_status', 'php-fpm/status',
                    'apm', 'trace', 'profiler', 'performance'
                ],
                extensions=['json', 'xml', 'yml'],
                description="Monitoring and metrics endpoints"
            ),
            
            # GraphQL specific
            'graphql': EndpointRule(
                pattern=r'/graphql',
                priority=80,
                keywords=[
                    'playground', 'graphiql', 'console', 'explorer',
                    'schema', 'introspection', 'query', 'mutation',
                    'subscription', 'websocket', 'ws', 'altair',
                    'voyager', 'docs', 'reference'
                ],
                extensions=['json'],
                recursive=False,
                description="GraphQL endpoints and tools"
            ),
            
            # Package managers
            'packages': EndpointRule(
                pattern=r'/(vendor|node_modules|bower_components|packages)',
                priority=70,
                keywords=[
                    'composer.json', 'composer.lock', 'installed.json',
                    'package.json', 'package-lock.json', 'yarn.lock',
                    'requirements.txt', 'Pipfile', 'Pipfile.lock',
                    'Gemfile', 'Gemfile.lock', 'bower.json',
                    '.npmrc', '.yarnrc', 'lerna.json',
                    'autoload.php', 'bootstrap.php'
                ],
                extensions=['json', 'lock', 'txt'],
                description="Package manager files and dependencies"
            ),
            
            # Database interfaces
            'database': EndpointRule(
                pattern=r'/(phpmyadmin|adminer|pgadmin|mongodb|redis|elasticsearch)',
                priority=85,
                keywords=[
                    'index.php', 'login.php', 'db.php', 'sql.php',
                    'import.php', 'export.php', 'query.php',
                    'setup', 'install', 'config', 'upgrade',
                    'console', 'shell', 'cli', 'terminal'
                ],
                extensions=['php'],
                description="Database management interfaces"
            ),
            
            # Hidden/Sensitive files
            'hidden': EndpointRule(
                pattern=r'/\\.',
                priority=75,
                keywords=[
                    '.env', '.env.local', '.env.prod', '.env.dev',
                    '.git/config', '.gitignore', '.dockerignore',
                    '.htaccess', '.htpasswd', '.user.ini',
                    '.aws/credentials', '.ssh/id_rsa', '.ssh/known_hosts',
                    '.docker/config.json', '.kube/config',
                    '.npmrc', '.pypirc', '.netrc', '.bashrc'
                ],
                extensions=[],
                description="Hidden and sensitive files"
            )
        }
    
    def analyze_path(self, path: str, status_code: int) -> List[Tuple[str, EndpointRule]]:
        """
        Analyze a discovered path and return applicable rules
        
        Args:
            path: The discovered path
            status_code: HTTP status code
            
        Returns:
            List of tuples (rule_name, rule) sorted by priority
        """
        applicable_rules = []
        
        for rule_name, rule in self.rules.items():
            if re.search(rule.pattern, path, re.IGNORECASE):
                applicable_rules.append((rule_name, rule))
        
        # Sort by priority (higher first)
        applicable_rules.sort(key=lambda x: x[1].priority, reverse=True)
        
        return applicable_rules
    
    def get_expansion_keywords(self, path: str) -> Set[str]:
        """
        Get keywords to expand wordlist based on discovered path
        
        Args:
            path: The discovered path
            
        Returns:
            Set of keywords to add to wordlist
        """
        keywords = set()
        applicable_rules = self.analyze_path(path, 200)
        
        for rule_name, rule in applicable_rules:
            keywords.update(rule.keywords)
            
            # Add variations based on the specific path
            if '/' in path:
                base = path.split('/')[-1]
                if base:
                    # Add variations
                    keywords.add(f"{base}/")
                    keywords.add(f"{base}/index")
                    keywords.add(f"{base}/admin")
                    keywords.add(f"{base}/api")
                    keywords.add(f"{base}/config")
        
        return keywords
    
    def get_priority_paths(self, discovered_paths: List[str]) -> List[str]:
        """
        Reorder paths based on priority rules
        
        Args:
            discovered_paths: List of discovered paths
            
        Returns:
            Reordered list with high-priority paths first
        """
        path_priorities = []
        
        for path in discovered_paths:
            max_priority = 0
            rules = self.analyze_path(path, 200)
            
            if rules:
                max_priority = rules[0][1].priority
            
            path_priorities.append((path, max_priority))
        
        # Sort by priority (higher first)
        path_priorities.sort(key=lambda x: x[1], reverse=True)
        
        return [path for path, _ in path_priorities]
    
    def should_deep_scan(self, path: str) -> bool:
        """
        Determine if a path should be scanned recursively with expanded wordlist
        
        Args:
            path: The discovered path
            
        Returns:
            True if deep scan is recommended
        """
        rules = self.analyze_path(path, 200)
        
        # High priority paths should be deep scanned
        for rule_name, rule in rules:
            if rule.priority >= 70 and rule.recursive:
                return True
        
        return False
    
    def get_smart_extensions(self, path: str) -> List[str]:
        """
        Get intelligent extension list based on discovered path
        
        Args:
            path: The discovered path
            
        Returns:
            List of extensions to try
        """
        extensions = set()
        rules = self.analyze_path(path, 200)
        
        for rule_name, rule in rules:
            extensions.update(rule.extensions)
        
        # Add common extensions if none specified
        if not extensions:
            extensions = {'php', 'html', 'js', 'json', 'txt'}
        
        return list(extensions)
    
    def get_scan_strategy(self, base_url: str, discovered_paths: List[Dict]) -> Dict:
        """
        Generate optimized scan strategy based on discoveries
        
        Args:
            base_url: The target base URL
            discovered_paths: List of discovered path info
            
        Returns:
            Scan strategy with prioritized paths and keywords
        """
        strategy = {
            'priority_paths': [],
            'expansion_keywords': set(),
            'deep_scan_paths': [],
            'custom_wordlists': {},
            'recommended_extensions': set()
        }
        
        # Analyze all discovered paths
        for path_info in discovered_paths:
            path = path_info.get('path', '')
            status = path_info.get('status', 0)
            
            # Get applicable rules
            rules = self.analyze_path(path, status)
            
            if rules:
                # High priority path
                if rules[0][1].priority >= 80:
                    strategy['priority_paths'].append(path)
                
                # Collect expansion keywords
                keywords = self.get_expansion_keywords(path)
                strategy['expansion_keywords'].update(keywords)
                
                # Check for deep scan
                if self.should_deep_scan(path):
                    strategy['deep_scan_paths'].append(path)
                
                # Collect extensions
                extensions = self.get_smart_extensions(path)
                strategy['recommended_extensions'].update(extensions)
                
                # Generate custom wordlist for specific path types
                rule_name, rule = rules[0]
                if rule_name not in strategy['custom_wordlists']:
                    strategy['custom_wordlists'][rule_name] = []
                strategy['custom_wordlists'][rule_name].extend(rule.keywords)
        
        # Convert sets to lists for JSON serialization
        strategy['expansion_keywords'] = list(strategy['expansion_keywords'])
        strategy['recommended_extensions'] = list(strategy['recommended_extensions'])
        
        return strategy
    
    def generate_smart_wordlist(self, context: Dict) -> List[str]:
        """
        Generate context-aware wordlist based on discoveries
        
        Args:
            context: Context information (discovered paths, technologies, etc.)
            
        Returns:
            Optimized wordlist
        """
        wordlist = set()
        
        # Add keywords from applicable rules
        if 'technologies' in context:
            for tech in context['technologies']:
                tech_lower = tech.lower()
                for rule_name, rule in self.rules.items():
                    if tech_lower in rule.pattern.lower():
                        wordlist.update(rule.keywords)
        
        # Add keywords based on discovered paths
        if 'paths' in context:
            for path in context['paths']:
                keywords = self.get_expansion_keywords(path)
                wordlist.update(keywords)
        
        # Add high-priority keywords
        priority_keywords = set()
        for rule_name, rule in self.rules.items():
            if rule.priority >= 80:
                priority_keywords.update(rule.keywords[:10])  # Top 10 from each
        
        wordlist.update(priority_keywords)
        
        return sorted(list(wordlist))
    
    def export_rules(self, filename: str):
        """Export rules to JSON file"""
        rules_dict = {}
        for name, rule in self.rules.items():
            rules_dict[name] = {
                'pattern': rule.pattern,
                'priority': rule.priority,
                'keywords': rule.keywords,
                'extensions': rule.extensions,
                'recursive': rule.recursive,
                'description': rule.description
            }
        
        with open(filename, 'w') as f:
            json.dump(rules_dict, f, indent=2)
    
    def import_rules(self, filename: str):
        """Import rules from JSON file"""
        with open(filename, 'r') as f:
            rules_dict = json.load(f)
        
        self.rules = {}
        for name, rule_data in rules_dict.items():
            self.rules[name] = EndpointRule(**rule_data)