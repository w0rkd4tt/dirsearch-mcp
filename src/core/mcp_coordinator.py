import os
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from collections import defaultdict
import re
from urllib.parse import urlparse

from src.utils.logger import LoggerSetup
from src.config.settings import Settings


@dataclass
class TargetInfo:
    url: str
    domain: str
    server_type: Optional[str] = None
    technology_stack: List[str] = None
    response_patterns: Dict[str, Any] = None
    security_headers: Dict[str, str] = None
    detected_cms: Optional[str] = None
    
    def __post_init__(self):
        if self.technology_stack is None:
            self.technology_stack = []
        if self.response_patterns is None:
            self.response_patterns = {}
        if self.security_headers is None:
            self.security_headers = {}


@dataclass
class ScanTask:
    task_id: str
    task_type: str
    priority: int
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ScanResult:
    task_id: str
    status: str
    findings: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: str


class AIAgentConnector:
    """Connector for AI agents (ChatGPT/DeepSeek)"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.logger = LoggerSetup.get_logger(__name__)
        self.cache = {}
        self.rate_limiter = {
            'openai': {'requests': 0, 'reset_time': time.time()},
            'deepseek': {'requests': 0, 'reset_time': time.time()}
        }
        
    async def detect_ai_availability(self) -> Tuple[bool, str]:
        """Check if AI agent is available"""
        providers = []
        
        # Check OpenAI
        if self.config.ai_config.get('openai_api_key'):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f"Bearer {self.config.ai_config['openai_api_key']}",
                        'Content-Type': 'application/json'
                    }
                    async with session.get(
                        'https://api.openai.com/v1/models',
                        headers=headers,
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            providers.append('openai')
            except Exception as e:
                self.logger.debug(f"OpenAI API check failed: {e}")
        
        # Check DeepSeek
        if self.config.ai_config.get('deepseek_api_key'):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f"Bearer {self.config.ai_config['deepseek_api_key']}",
                        'Content-Type': 'application/json'
                    }
                    async with session.post(
                        'https://api.deepseek.com/v1/chat/completions',
                        headers=headers,
                        json={'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': 'test'}]},
                        timeout=5
                    ) as response:
                        if response.status in [200, 400]:  # 400 means auth works but request invalid
                            providers.append('deepseek')
            except Exception as e:
                self.logger.debug(f"DeepSeek API check failed: {e}")
        
        if providers:
            return True, providers[0]
        return False, None
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Check if rate limit allows request"""
        limits = {
            'openai': {'max_requests': 60, 'window': 60},
            'deepseek': {'max_requests': 100, 'window': 60}
        }
        
        current_time = time.time()
        limiter = self.rate_limiter[provider]
        
        # Reset counter if window passed
        if current_time - limiter['reset_time'] > limits[provider]['window']:
            limiter['requests'] = 0
            limiter['reset_time'] = current_time
        
        # Check limit
        if limiter['requests'] >= limits[provider]['max_requests']:
            return False
        
        limiter['requests'] += 1
        return True
    
    def _get_cache_key(self, context: str, question: str) -> str:
        """Generate cache key for AI queries"""
        content = f"{context}:{question}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def query_ai_agent(self, context: str, question: str, provider: str = None) -> Optional[str]:
        """Query AI agent with context and question"""
        # Check cache
        cache_key = self._get_cache_key(context, question)
        if cache_key in self.cache:
            self.logger.debug("Returning cached AI response")
            return self.cache[cache_key]
        
        # Auto-detect provider if not specified
        if not provider:
            available, provider = await self.detect_ai_availability()
            if not available:
                return None
        
        # Check rate limit
        if not self._check_rate_limit(provider):
            self.logger.warning(f"Rate limit exceeded for {provider}")
            return None
        
        try:
            if provider == 'openai':
                response = await self._query_openai(context, question)
            elif provider == 'deepseek':
                response = await self._query_deepseek(context, question)
            else:
                return None
            
            # Cache response
            if response:
                self.cache[cache_key] = response
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI query failed: {e}")
            return None
    
    async def _query_openai(self, context: str, question: str) -> Optional[str]:
        """Query OpenAI API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f"Bearer {self.config.ai_config['openai_api_key']}",
                'Content-Type': 'application/json'
            }
            
            prompt = self._build_prompt(context, question)
            
            payload = {
                'model': self.config.ai_config.get('openai_model', 'gpt-3.5-turbo'),
                'messages': [
                    {'role': 'system', 'content': 'You are a web security expert specializing in directory enumeration and vulnerability assessment.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    self.logger.error(f"OpenAI API error: {response.status}")
                    return None
    
    async def _query_deepseek(self, context: str, question: str) -> Optional[str]:
        """Query DeepSeek API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f"Bearer {self.config.ai_config['deepseek_api_key']}",
                'Content-Type': 'application/json'
            }
            
            prompt = self._build_prompt(context, question)
            
            payload = {
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': 'You are a web security expert specializing in directory enumeration and vulnerability assessment.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            async with session.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    self.logger.error(f"DeepSeek API error: {response.status}")
                    return None
    
    def _build_prompt(self, context: str, question: str) -> str:
        """Build structured prompt for AI agent"""
        return f"""Context:
{context}

Question: {question}

Please provide a concise, actionable response focusing on:
1. Specific recommendations based on the context
2. Priority order if multiple options exist
3. Any security considerations
4. Expected effectiveness

Keep the response under 300 words and use bullet points where appropriate."""


class MCPCoordinator:
    """Intelligent MCP Coordinator with AI agent integration"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.logger = LoggerSetup.get_logger(__name__)
        self.ai_connector = AIAgentConnector(config)
        self.intelligence_mode = 'LOCAL'
        self.scan_history = []
        self.learning_data = defaultdict(list)
        
    async def initialize(self):
        """Initialize coordinator and detect AI availability"""
        available, provider = await self.ai_connector.detect_ai_availability()
        if available:
            self.intelligence_mode = 'AI_AGENT'
            self.logger.info(f"AI Agent mode enabled with {provider}")
        else:
            self.logger.info("Running in LOCAL mode (rule-based)")
    
    async def analyze_target(self, url: str) -> TargetInfo:
        """Analyze target with intelligent detection"""
        self.logger.info(f"Analyzing target: {url}")
        
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
            
        parsed_url = urlparse(url)
        target_info = TargetInfo(
            url=url,
            domain=parsed_url.netloc if parsed_url.netloc else url.replace('http://', '').replace('https://', '').split('/')[0]
        )
        
        # Basic HTTP analysis
        try:
            # Create session with custom settings for better compatibility
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            connector = aiohttp.TCPConnector(ssl=False, force_close=True)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                # Add headers to avoid being blocked
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    headers = dict(response.headers)
                    
                    # Server detection
                    target_info.server_type = headers.get('Server', 'Unknown')
                    
                    # Security headers
                    security_headers = {}
                    for header in ['X-Frame-Options', 'X-Content-Type-Options', 
                                 'Strict-Transport-Security', 'Content-Security-Policy']:
                        if header in headers:
                            security_headers[header] = headers[header]
                    target_info.security_headers = security_headers
                    
                    # Technology detection from headers
                    tech_stack = []
                    if 'X-Powered-By' in headers:
                        tech_stack.append(headers['X-Powered-By'])
                    if 'X-AspNet-Version' in headers:
                        tech_stack.append('ASP.NET')
                    target_info.technology_stack = tech_stack
                    
                    # Response patterns
                    content = await response.text()
                    target_info.response_patterns = {
                        'status_code': response.status,
                        'content_length': len(content),
                        'has_title': bool(re.search(r'<title>.*?</title>', content)),
                        'has_forms': bool(re.search(r'<form.*?>', content))
                    }
                    
                    # CMS detection
                    target_info.detected_cms = self._detect_cms(content, headers)
                    
        except aiohttp.ClientError as e:
            self.logger.warning(f"HTTP error analyzing target {url}: {e}")
            # Continue with limited analysis
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout analyzing target {url}")
            # Continue with limited analysis
        except Exception as e:
            self.logger.error(f"Unexpected error analyzing target {url}: {type(e).__name__}: {e}")
            # Continue with limited analysis
        
        # AI-enhanced analysis
        if self.intelligence_mode == 'AI_AGENT':
            ai_insights = await self._get_ai_target_analysis(target_info)
            if ai_insights:
                self._merge_ai_insights(target_info, ai_insights)
        
        return target_info
    
    def _detect_cms(self, content: str, headers: Dict[str, str]) -> Optional[str]:
        """Detect CMS from response"""
        cms_patterns = {
            'WordPress': [r'wp-content', r'wp-includes', r'WordPress'],
            'Joomla': [r'Joomla', r'/components/', r'/modules/'],
            'Drupal': [r'Drupal', r'/sites/default/', r'/modules/'],
            'Django': [r'csrfmiddlewaretoken', r'django'],
            'Laravel': [r'laravel_session', r'Laravel'],
            'Magento': [r'Magento', r'/skin/frontend/', r'/js/mage/']
        }
        
        for cms, patterns in cms_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return cms
                    
        return None
    
    async def _get_ai_target_analysis(self, target_info: TargetInfo) -> Optional[Dict[str, Any]]:
        """Get AI analysis of target"""
        context = f"""Target URL: {target_info.url}
Server: {target_info.server_type}
Technologies: {', '.join(target_info.technology_stack)}
CMS: {target_info.detected_cms or 'None detected'}
Security Headers: {json.dumps(target_info.security_headers, indent=2)}
Response Patterns: {json.dumps(target_info.response_patterns, indent=2)}"""
        
        question = """Based on this target analysis, provide:
1. Additional technology stack components that might be present
2. Recommended wordlists for this specific stack
3. Optimal scan parameters (threads, timeout, delay)
4. Potential vulnerabilities to focus on
5. Any special considerations for this target"""
        
        response = await self.ai_connector.query_ai_agent(context, question)
        
        if response:
            # Parse AI response
            try:
                # Simple parsing - in production, use structured output
                insights = {
                    'additional_tech': [],
                    'recommended_wordlists': [],
                    'scan_parameters': {},
                    'focus_areas': [],
                    'considerations': []
                }
                
                # Extract recommendations from AI response
                lines = response.strip().split('\n')
                current_section = None
                
                for line in lines:
                    if '1.' in line:
                        current_section = 'additional_tech'
                    elif '2.' in line:
                        current_section = 'recommended_wordlists'
                    elif '3.' in line:
                        current_section = 'scan_parameters'
                    elif '4.' in line:
                        current_section = 'focus_areas'
                    elif '5.' in line:
                        current_section = 'considerations'
                    elif current_section and line.strip():
                        if current_section == 'scan_parameters':
                            # Parse parameters
                            if 'threads' in line.lower():
                                match = re.search(r'(\d+)', line)
                                if match:
                                    insights['scan_parameters']['threads'] = int(match.group(1))
                            elif 'timeout' in line.lower():
                                match = re.search(r'(\d+)', line)
                                if match:
                                    insights['scan_parameters']['timeout'] = int(match.group(1))
                        else:
                            # Add to appropriate list
                            cleaned_line = line.strip(' -"*')
                            if cleaned_line:
                                insights[current_section].append(cleaned_line)
                
                return insights
                
            except Exception as e:
                self.logger.error(f"Failed to parse AI response: {e}")
                return None
        
        return None
    
    def _merge_ai_insights(self, target_info: TargetInfo, ai_insights: Dict[str, Any]):
        """Merge AI insights into target info"""
        if 'additional_tech' in ai_insights:
            target_info.technology_stack.extend(ai_insights['additional_tech'])
            target_info.technology_stack = list(set(target_info.technology_stack))
    
    async def generate_scan_plan(self, target_info: TargetInfo) -> List[ScanTask]:
        """Generate intelligent scan plan"""
        self.logger.info("Generating scan plan")
        
        scan_tasks = []
        
        if self.intelligence_mode == 'AI_AGENT':
            # Get AI recommendations
            ai_plan = await self._get_ai_scan_plan(target_info)
            if ai_plan:
                scan_tasks.extend(ai_plan)
        
        # Fallback or complement with local rules
        if not scan_tasks:
            scan_tasks = self._generate_local_scan_plan(target_info)
        
        # Prioritize tasks
        scan_tasks.sort(key=lambda x: x.priority, reverse=True)
        
        return scan_tasks
    
    def _generate_local_scan_plan(self, target_info: TargetInfo) -> List[ScanTask]:
        """Generate scan plan using local rules"""
        tasks = []
        
        # Base scan task with enhanced wordlist selection
        primary_wordlist, additional_wordlists = self._select_wordlist(target_info)
        base_params = {
            'wordlist_type': primary_wordlist,
            'additional_wordlists': additional_wordlists,
            'extensions': self._select_extensions(target_info),
            'threads': self._calculate_threads(target_info),
            'timeout': 10,
            'delay': 0,
            'recursive': True,
            'recursion_depth': 3
        }
        
        tasks.append(ScanTask(
            task_id='base_scan',
            task_type='directory_enumeration',
            priority=100,
            parameters=base_params
        ))
        
        # Technology-specific tasks
        if 'WordPress' in (target_info.detected_cms or ''):
            tasks.append(ScanTask(
                task_id='wp_scan',
                task_type='cms_specific',
                priority=90,
                parameters={
                    'wordlist': 'wordpress.txt',
                    'paths': ['/wp-admin/', '/wp-content/', '/wp-includes/'],
                    'extensions': ['php'],
                    'threads': 10
                }
            ))
        
        # Add backup file scan
        tasks.append(ScanTask(
            task_id='backup_scan',
            task_type='backup_files',
            priority=80,
            parameters={
                'extensions': ['bak', 'old', 'backup', 'zip', 'tar.gz'],
                'patterns': ['backup', 'old', 'copy', 'bkp'],
                'threads': 5
            }
        ))
        
        return tasks
    
    def _select_wordlist(self, target_info: TargetInfo) -> Tuple[str, List[str]]:
        """Select appropriate wordlist based on target
        
        Returns:
            Tuple of (primary_wordlist_type, additional_wordlists)
        """
        additional_wordlists = []
        primary_type = 'enhanced'  # Default to enhanced wordlist
        
        # Check if URL contains API patterns
        url_lower = target_info.url.lower()
        if any(pattern in url_lower for pattern in ['/api', '/v1', '/v2', '/rest', '/graphql']):
            primary_type = 'api'
            additional_wordlists.append('wordlists/hidden-files.txt')
            
        # CMS-specific wordlists
        if target_info.detected_cms:
            cms_wordlists = {
                'WordPress': 'wordpress.txt',
                'Joomla': 'joomla.txt',
                'Drupal': 'drupal.txt'
            }
            if target_info.detected_cms in cms_wordlists:
                additional_wordlists.append(f'wordlists/{cms_wordlists[target_info.detected_cms]}')
        
        # Technology-specific
        tech_stack = ' '.join(target_info.technology_stack).lower()
        if 'php' in tech_stack:
            additional_wordlists.append('wordlists/php_common.txt')
        elif 'asp' in tech_stack or '.net' in tech_stack:
            additional_wordlists.append('wordlists/aspnet_common.txt')
        elif 'java' in tech_stack:
            additional_wordlists.append('wordlists/java_common.txt')
        
        # Always include hidden files for comprehensive scanning
        if 'wordlists/hidden-files.txt' not in additional_wordlists:
            additional_wordlists.append('wordlists/hidden-files.txt')
        
        return primary_type, additional_wordlists
    
    def _select_extensions(self, target_info: TargetInfo) -> List[str]:
        """Select file extensions based on technology"""
        extensions = []
        
        tech_stack = ' '.join(target_info.technology_stack).lower()
        
        if 'php' in tech_stack or target_info.detected_cms in ['WordPress', 'Joomla', 'Drupal']:
            extensions.extend(['php', 'php3', 'php4', 'php5', 'phtml'])
        if 'asp' in tech_stack or '.net' in tech_stack:
            extensions.extend(['asp', 'aspx', 'asmx', 'ashx'])
        if 'java' in tech_stack:
            extensions.extend(['jsp', 'jsf', 'do', 'action'])
        if 'python' in tech_stack:
            extensions.extend(['py'])
        
        # Always include common extensions
        extensions.extend(['html', 'htm', 'txt', 'xml', 'json'])
        
        return list(set(extensions))
    
    def _calculate_threads(self, target_info: TargetInfo) -> int:
        """Calculate optimal thread count"""
        # Check if target has rate limiting
        if 'Retry-After' in target_info.security_headers:
            return 2
        
        # Adjust based on server type
        server = (target_info.server_type or '').lower()
        if 'cloudflare' in server:
            return 5
        elif 'nginx' in server:
            return 20
        elif 'apache' in server:
            return 15
        
        return 10
    
    async def _get_ai_scan_plan(self, target_info: TargetInfo) -> List[ScanTask]:
        """Get AI-generated scan plan"""
        context = f"""Target Analysis:
- URL: {target_info.url}
- Server: {target_info.server_type}
- Technologies: {', '.join(target_info.technology_stack)}
- CMS: {target_info.detected_cms or 'None'}
- Security Headers: {list(target_info.security_headers.keys())}"""
        
        question = """Create a prioritized scan plan with specific tasks. For each task provide:
1. Task type (directory_enumeration, backup_files, config_files, etc.)
2. Specific wordlist or patterns to use
3. Recommended parameters (threads, extensions, timeout)
4. Priority (1-100, higher is more important)"""
        
        response = await self.ai_connector.query_ai_agent(context, question)
        
        if response:
            # Parse AI response into scan tasks
            tasks = []
            try:
                # Simple parsing - extract task recommendations
                task_id = 1
                for section in response.split('\n\n'):
                    if 'task type' in section.lower():
                        task = ScanTask(
                            task_id=f'ai_task_{task_id}',
                            task_type='directory_enumeration',
                            priority=50,
                            parameters={}
                        )
                        
                        # Extract parameters from text
                        if 'threads' in section:
                            match = re.search(r'threads[:\s]+(\d+)', section, re.IGNORECASE)
                            if match:
                                task.parameters['threads'] = int(match.group(1))
                        
                        if 'wordlist' in section:
                            match = re.search(r'wordlist[:\s]+([^\s,]+)', section, re.IGNORECASE)
                            if match:
                                task.parameters['wordlist'] = match.group(1)
                        
                        if 'priority' in section:
                            match = re.search(r'priority[:\s]+(\d+)', section, re.IGNORECASE)
                            if match:
                                task.priority = int(match.group(1))
                        
                        tasks.append(task)
                        task_id += 1
                
            except Exception as e:
                self.logger.error(f"Failed to parse AI scan plan: {e}")
            
            return tasks
        
        return []
    
    async def execute_scan_plan(self, scan_tasks: List[ScanTask]) -> List[ScanResult]:
        """Execute scan plan with monitoring"""
        results = []
        
        for task in scan_tasks:
            self.logger.info(f"Executing task: {task.task_id} (priority: {task.priority})")
            
            start_time = time.time()
            
            # Execute based on task type
            if task.task_type == 'directory_enumeration':
                result = await self._execute_directory_scan(task)
            elif task.task_type == 'backup_files':
                result = await self._execute_backup_scan(task)
            elif task.task_type == 'cms_specific':
                result = await self._execute_cms_scan(task)
            else:
                result = ScanResult(
                    task_id=task.task_id,
                    status='skipped',
                    findings=[],
                    metrics={'reason': 'Unknown task type'},
                    timestamp=datetime.now().isoformat()
                )
            
            # Add execution time
            result.metrics['execution_time'] = time.time() - start_time
            
            results.append(result)
            
            # Learn from results
            if self.intelligence_mode == 'AI_AGENT':
                await self._learn_from_results(task, result)
        
        return results
    
    async def _execute_directory_scan(self, task: ScanTask) -> ScanResult:
        """Execute directory enumeration scan"""
        # This would integrate with DirsearchEngine
        # Placeholder implementation
        return ScanResult(
            task_id=task.task_id,
            status='completed',
            findings=[
                {'path': '/admin/', 'status': 200, 'size': 1234},
                {'path': '/backup/', 'status': 403, 'size': 403}
            ],
            metrics={
                'total_requests': 1000,
                'found_paths': 2,
                'errors': 0
            },
            timestamp=datetime.now().isoformat()
        )
    
    async def _execute_backup_scan(self, task: ScanTask) -> ScanResult:
        """Execute backup file scan"""
        # Placeholder
        return ScanResult(
            task_id=task.task_id,
            status='completed',
            findings=[],
            metrics={'total_requests': 100},
            timestamp=datetime.now().isoformat()
        )
    
    async def _execute_cms_scan(self, task: ScanTask) -> ScanResult:
        """Execute CMS-specific scan"""
        # Placeholder
        return ScanResult(
            task_id=task.task_id,
            status='completed',
            findings=[],
            metrics={'total_requests': 200},
            timestamp=datetime.now().isoformat()
        )
    
    async def _learn_from_results(self, task: ScanTask, result: ScanResult):
        """Learn from scan results for future optimization"""
        if result.status == 'completed' and result.findings:
            # Store successful patterns
            self.learning_data['successful_params'].append({
                'task_type': task.task_type,
                'parameters': task.parameters,
                'findings_count': len(result.findings),
                'execution_time': result.metrics.get('execution_time', 0)
            })
            
            # Ask AI for insights
            if len(result.findings) > 5:
                context = f"""Scan Results:
Task Type: {task.task_type}
Parameters: {json.dumps(task.parameters, indent=2)}
Findings: {len(result.findings)} paths found
Sample findings: {json.dumps(result.findings[:5], indent=2)}"""
                
                question = "What patterns do you see in these findings? Any recommendations for follow-up scans?"
                
                insights = await self.ai_connector.query_ai_agent(context, question)
                if insights:
                    self.logger.info(f"AI Learning Insights: {insights[:200]}...")
    
    async def optimize_parameters(self, target_info: TargetInfo) -> Dict[str, Any]:
        """Optimize scan parameters based on target"""
        optimized = {
            'threads': 10,
            'timeout': 10,
            'delay': 0,
            'retry_attempts': 3,
            'follow_redirects': True,
            'user_agent': 'Mozilla/5.0 (compatible; Dirsearch/1.0)'
        }
        
        if self.intelligence_mode == 'AI_AGENT':
            # Get AI optimization
            context = f"""Target: {target_info.url}
Server: {target_info.server_type}
Past successful scans: {len(self.learning_data.get('successful_params', []))}"""
            
            question = "Recommend optimal scan parameters for this target considering server type and avoiding detection."
            
            ai_params = await self.ai_connector.query_ai_agent(context, question)
            if ai_params:
                # Parse and merge AI recommendations
                self._merge_ai_parameters(optimized, ai_params)
        
        # Apply local rules
        optimized = self._apply_local_optimization(target_info, optimized)
        
        return optimized
    
    def _merge_ai_parameters(self, params: Dict[str, Any], ai_response: str):
        """Merge AI parameter recommendations"""
        try:
            # Extract numeric recommendations
            if 'threads' in ai_response:
                match = re.search(r'threads[:\s]+(\d+)', ai_response, re.IGNORECASE)
                if match:
                    params['threads'] = min(int(match.group(1)), 50)  # Cap at 50
            
            if 'timeout' in ai_response:
                match = re.search(r'timeout[:\s]+(\d+)', ai_response, re.IGNORECASE)
                if match:
                    params['timeout'] = int(match.group(1))
            
            if 'delay' in ai_response:
                match = re.search(r'delay[:\s]+(\d+\.?\d*)', ai_response, re.IGNORECASE)
                if match:
                    params['delay'] = float(match.group(1))
                    
        except Exception as e:
            self.logger.error(f"Failed to parse AI parameters: {e}")
    
    def _apply_local_optimization(self, target_info: TargetInfo, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply local optimization rules"""
        # WAF detection adjustments
        if any(waf in (target_info.server_type or '').lower() 
               for waf in ['cloudflare', 'akamai', 'incapsula']):
            params['threads'] = min(params['threads'], 5)
            params['delay'] = max(params['delay'], 0.5)
            params['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        # Slow server adjustments
        if target_info.response_patterns and target_info.response_patterns.get('response_time', 0) > 2:
            params['timeout'] = max(params['timeout'], 20)
            params['threads'] = min(params['threads'], 5)
        
        return params
    
    def get_scan_summary(self, results: List[ScanResult]) -> Dict[str, Any]:
        """Generate scan summary with insights"""
        summary = {
            'total_tasks': len(results),
            'completed_tasks': sum(1 for r in results if r.status == 'completed'),
            'total_findings': sum(len(r.findings) for r in results),
            'execution_time': sum(r.metrics.get('execution_time', 0) for r in results),
            'intelligence_mode': self.intelligence_mode,
            'top_findings': []
        }
        
        # Collect all findings
        all_findings = []
        for result in results:
            for finding in result.findings:
                all_findings.append({
                    'task_id': result.task_id,
                    **finding
                })
        
        # Sort by importance (status code, size)
        all_findings.sort(key=lambda x: (x.get('status', 999), -x.get('size', 0)))
        summary['top_findings'] = all_findings[:10]
        
        return summary