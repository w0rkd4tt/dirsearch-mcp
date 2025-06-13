import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import time
from datetime import datetime

from src.core.mcp_coordinator import (
    MCPCoordinator, AIAgentConnector, TargetInfo, ScanTask, ScanResult
)
from src.config.settings import Settings


# Fixtures
@pytest.fixture
def settings():
    """Create test settings"""
    return Settings(
        ai_config={
            'openai_api_key': 'test-key-123',
            'deepseek_api_key': 'test-deepseek-456',
            'openai_model': 'gpt-3.5-turbo'
        },
        default_scan_config={
            'threads': 10,
            'timeout': 10
        }
    )


@pytest.fixture
def ai_connector(settings):
    """Create AIAgentConnector instance"""
    return AIAgentConnector(settings)


@pytest.fixture
def mcp_coordinator(settings):
    """Create MCPCoordinator instance"""
    return MCPCoordinator(settings)


@pytest.fixture
def sample_target_info():
    """Create sample TargetInfo"""
    return TargetInfo(
        url='http://test.com',
        domain='test.com',
        server_type='nginx/1.18.0',
        technology_stack=['PHP', 'MySQL'],
        detected_cms='WordPress',
        security_headers={'X-Frame-Options': 'SAMEORIGIN'},
        response_patterns={'status_code': 200, 'has_forms': True}
    )


@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing"""
    return """Based on the target analysis:

1. Additional technology stack components that might be present:
- jQuery
- Bootstrap CSS framework
- MySQL database

2. Recommended wordlists for this specific stack:
- wordpress.txt
- php_common.txt
- wp-plugins.txt

3. Optimal scan parameters:
- threads: 15
- timeout: 20
- delay: 0.5

4. Potential vulnerabilities to focus on:
- WordPress plugin vulnerabilities
- Exposed configuration files
- Backup files

5. Any special considerations:
- Use lower thread count to avoid detection
- Focus on wp-content directory"""


# Test AIAgentConnector
class TestAIAgentConnector:
    
    @pytest.mark.asyncio
    async def test_detect_ai_availability_openai(self, ai_connector):
        """Test OpenAI availability detection"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            available, provider = await ai_connector.detect_ai_availability()
            
            assert available is True
            assert provider == 'openai'
    
    @pytest.mark.asyncio
    async def test_detect_ai_availability_deepseek(self, ai_connector):
        """Test DeepSeek availability detection"""
        # Remove OpenAI key to test DeepSeek
        ai_connector.config.ai_config['openai_api_key'] = None
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            available, provider = await ai_connector.detect_ai_availability()
            
            assert available is True
            assert provider == 'deepseek'
    
    @pytest.mark.asyncio
    async def test_detect_ai_availability_none(self, ai_connector):
        """Test when no AI is available"""
        ai_connector.config.ai_config['openai_api_key'] = None
        ai_connector.config.ai_config['deepseek_api_key'] = None
        
        available, provider = await ai_connector.detect_ai_availability()
        
        assert available is False
        assert provider is None
    
    def test_check_rate_limit(self, ai_connector):
        """Test rate limiting"""
        # Test OpenAI rate limit (60 requests per minute)
        for i in range(60):
            assert ai_connector._check_rate_limit('openai') is True
        
        # 61st request should be blocked
        assert ai_connector._check_rate_limit('openai') is False
        
        # Simulate time passing
        ai_connector.rate_limiter['openai']['reset_time'] = time.time() - 61
        assert ai_connector._check_rate_limit('openai') is True
    
    def test_get_cache_key(self, ai_connector):
        """Test cache key generation"""
        context = "Test context"
        question = "Test question"
        
        key1 = ai_connector._get_cache_key(context, question)
        key2 = ai_connector._get_cache_key(context, question)
        key3 = ai_connector._get_cache_key("Different", question)
        
        assert key1 == key2  # Same input should generate same key
        assert key1 != key3  # Different input should generate different key
    
    @pytest.mark.asyncio
    async def test_query_ai_agent_cached(self, ai_connector):
        """Test cached AI response"""
        context = "Test context"
        question = "Test question"
        cached_response = "Cached response"
        
        # Add to cache
        cache_key = ai_connector._get_cache_key(context, question)
        ai_connector.cache[cache_key] = cached_response
        
        response = await ai_connector.query_ai_agent(context, question)
        
        assert response == cached_response
    
    @pytest.mark.asyncio
    async def test_query_openai(self, ai_connector, mock_ai_response):
        """Test OpenAI API query"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'choices': [{'message': {'content': mock_ai_response}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await ai_connector._query_openai("context", "question")
            
            assert response == mock_ai_response
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_deepseek(self, ai_connector, mock_ai_response):
        """Test DeepSeek API query"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                'choices': [{'message': {'content': mock_ai_response}}]
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await ai_connector._query_deepseek("context", "question")
            
            assert response == mock_ai_response
    
    def test_build_prompt(self, ai_connector):
        """Test prompt building"""
        context = "Target: example.com"
        question = "What vulnerabilities to check?"
        
        prompt = ai_connector._build_prompt(context, question)
        
        assert context in prompt
        assert question in prompt
        assert "recommendations" in prompt.lower()


# Test MCPCoordinator
class TestMCPCoordinator:
    
    @pytest.mark.asyncio
    async def test_initialize_with_ai(self, mcp_coordinator):
        """Test initialization with AI available"""
        with patch.object(mcp_coordinator.ai_connector, 'detect_ai_availability', 
                         return_value=(True, 'openai')):
            await mcp_coordinator.initialize()
            
            assert mcp_coordinator.intelligence_mode == 'AI_AGENT'
    
    @pytest.mark.asyncio
    async def test_initialize_without_ai(self, mcp_coordinator):
        """Test initialization without AI"""
        with patch.object(mcp_coordinator.ai_connector, 'detect_ai_availability', 
                         return_value=(False, None)):
            await mcp_coordinator.initialize()
            
            assert mcp_coordinator.intelligence_mode == 'LOCAL'
    
    @pytest.mark.asyncio
    async def test_analyze_target(self, mcp_coordinator):
        """Test target analysis"""
        url = 'http://test.com'
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            'Server': 'nginx/1.18.0',
            'X-Powered-By': 'PHP/7.4',
            'X-Frame-Options': 'SAMEORIGIN'
        }
        mock_response.text = AsyncMock(return_value='<title>Test</title>')
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            target_info = await mcp_coordinator.analyze_target(url)
            
            assert target_info.url == url
            assert target_info.server_type == 'nginx/1.18.0'
            assert 'PHP/7.4' in target_info.technology_stack
            assert 'X-Frame-Options' in target_info.security_headers
            assert target_info.response_patterns['has_title'] is True
    
    def test_detect_cms(self, mcp_coordinator):
        """Test CMS detection"""
        # WordPress detection
        wp_content = '<link rel="stylesheet" href="/wp-content/themes/test.css">'
        assert mcp_coordinator._detect_cms(wp_content, {}) == 'WordPress'
        
        # Joomla detection
        joomla_content = '<meta name="generator" content="Joomla! 3.9">'
        assert mcp_coordinator._detect_cms(joomla_content, {}) == 'Joomla'
        
        # No CMS
        plain_content = '<html><body>Hello</body></html>'
        assert mcp_coordinator._detect_cms(plain_content, {}) is None
    
    @pytest.mark.asyncio
    async def test_get_ai_target_analysis(self, mcp_coordinator, sample_target_info, mock_ai_response):
        """Test AI-enhanced target analysis"""
        with patch.object(mcp_coordinator.ai_connector, 'query_ai_agent', 
                         return_value=mock_ai_response):
            insights = await mcp_coordinator._get_ai_target_analysis(sample_target_info)
            
            assert insights is not None
            assert 'additional_tech' in insights
            assert 'recommended_wordlists' in insights
            assert insights['scan_parameters']['threads'] == 15
    
    @pytest.mark.asyncio
    async def test_generate_scan_plan_local(self, mcp_coordinator, sample_target_info):
        """Test local scan plan generation"""
        mcp_coordinator.intelligence_mode = 'LOCAL'
        
        scan_plan = await mcp_coordinator.generate_scan_plan(sample_target_info)
        
        assert len(scan_plan) > 0
        assert scan_plan[0].task_type == 'directory_enumeration'
        assert scan_plan[0].priority == 100
        
        # Should include WordPress-specific task
        wp_tasks = [t for t in scan_plan if t.task_id == 'wp_scan']
        assert len(wp_tasks) == 1
    
    @pytest.mark.asyncio
    async def test_generate_scan_plan_ai(self, mcp_coordinator, sample_target_info):
        """Test AI-enhanced scan plan generation"""
        mcp_coordinator.intelligence_mode = 'AI_AGENT'
        
        ai_response = """Task type: directory_enumeration
Wordlist: wordpress.txt
Threads: 15
Priority: 90

Task type: backup_files
Priority: 80"""
        
        with patch.object(mcp_coordinator.ai_connector, 'query_ai_agent', 
                         return_value=ai_response):
            scan_plan = await mcp_coordinator.generate_scan_plan(sample_target_info)
            
            assert len(scan_plan) > 0
    
    def test_select_wordlist(self, mcp_coordinator, sample_target_info):
        """Test wordlist selection logic"""
        # WordPress CMS
        assert mcp_coordinator._select_wordlist(sample_target_info) == 'wordpress.txt'
        
        # PHP stack without CMS
        sample_target_info.detected_cms = None
        assert mcp_coordinator._select_wordlist(sample_target_info) == 'php_common.txt'
        
        # ASP.NET stack
        sample_target_info.technology_stack = ['ASP.NET', 'IIS']
        assert mcp_coordinator._select_wordlist(sample_target_info) == 'aspnet_common.txt'
        
        # Default
        sample_target_info.technology_stack = []
        assert mcp_coordinator._select_wordlist(sample_target_info) == 'common.txt'
    
    def test_select_extensions(self, mcp_coordinator, sample_target_info):
        """Test file extension selection"""
        extensions = mcp_coordinator._select_extensions(sample_target_info)
        
        # Should include PHP extensions for WordPress
        assert 'php' in extensions
        assert 'html' in extensions
        
        # Test ASP.NET extensions
        sample_target_info.technology_stack = ['ASP.NET']
        sample_target_info.detected_cms = None
        extensions = mcp_coordinator._select_extensions(sample_target_info)
        assert 'aspx' in extensions
    
    def test_calculate_threads(self, mcp_coordinator, sample_target_info):
        """Test thread calculation logic"""
        # Normal server
        threads = mcp_coordinator._calculate_threads(sample_target_info)
        assert threads == 15  # nginx default
        
        # Rate-limited server
        sample_target_info.security_headers['Retry-After'] = '60'
        threads = mcp_coordinator._calculate_threads(sample_target_info)
        assert threads == 2
        
        # Cloudflare
        sample_target_info.security_headers = {}
        sample_target_info.server_type = 'cloudflare'
        threads = mcp_coordinator._calculate_threads(sample_target_info)
        assert threads == 5
    
    @pytest.mark.asyncio
    async def test_execute_scan_plan(self, mcp_coordinator):
        """Test scan plan execution"""
        scan_tasks = [
            ScanTask(
                task_id='test1',
                task_type='directory_enumeration',
                priority=100,
                parameters={'wordlist': 'test.txt'}
            ),
            ScanTask(
                task_id='test2',
                task_type='backup_files',
                priority=80,
                parameters={}
            )
        ]
        
        results = await mcp_coordinator.execute_scan_plan(scan_tasks)
        
        assert len(results) == 2
        assert all(r.status == 'completed' for r in results)
        assert all(r.task_id in ['test1', 'test2'] for r in results)
    
    @pytest.mark.asyncio
    async def test_optimize_parameters_local(self, mcp_coordinator, sample_target_info):
        """Test parameter optimization in local mode"""
        mcp_coordinator.intelligence_mode = 'LOCAL'
        
        params = await mcp_coordinator.optimize_parameters(sample_target_info)
        
        assert 'threads' in params
        assert 'timeout' in params
        assert 'user_agent' in params
        
        # Test WAF adjustments
        sample_target_info.server_type = 'cloudflare'
        params = await mcp_coordinator.optimize_parameters(sample_target_info)
        assert params['threads'] <= 5
        assert params['delay'] >= 0.5
    
    @pytest.mark.asyncio
    async def test_optimize_parameters_ai(self, mcp_coordinator, sample_target_info):
        """Test AI-enhanced parameter optimization"""
        mcp_coordinator.intelligence_mode = 'AI_AGENT'
        
        ai_response = "Use threads: 20 for optimal performance. Set timeout: 15 seconds."
        
        with patch.object(mcp_coordinator.ai_connector, 'query_ai_agent', 
                         return_value=ai_response):
            params = await mcp_coordinator.optimize_parameters(sample_target_info)
            
            assert params['threads'] == 20
            assert params['timeout'] == 15
    
    def test_merge_ai_parameters(self, mcp_coordinator):
        """Test AI parameter merging"""
        params = {'threads': 10, 'timeout': 10}
        ai_response = "threads: 25, timeout: 20, delay: 1.5"
        
        mcp_coordinator._merge_ai_parameters(params, ai_response)
        
        assert params['threads'] == 25
        assert params['timeout'] == 20
        assert params['delay'] == 1.5
    
    @pytest.mark.asyncio
    async def test_learn_from_results(self, mcp_coordinator):
        """Test learning from scan results"""
        mcp_coordinator.intelligence_mode = 'AI_AGENT'
        
        task = ScanTask(
            task_id='test',
            task_type='directory_enumeration',
            priority=100,
            parameters={'wordlist': 'test.txt'}
        )
        
        result = ScanResult(
            task_id='test',
            status='completed',
            findings=[{'path': f'/path{i}', 'status': 200} for i in range(10)],
            metrics={'execution_time': 5.0},
            timestamp=datetime.now().isoformat()
        )
        
        with patch.object(mcp_coordinator.ai_connector, 'query_ai_agent', 
                         return_value="Interesting pattern detected"):
            await mcp_coordinator._learn_from_results(task, result)
            
            assert len(mcp_coordinator.learning_data['successful_params']) == 1
            assert mcp_coordinator.learning_data['successful_params'][0]['findings_count'] == 10
    
    def test_get_scan_summary(self, mcp_coordinator):
        """Test scan summary generation"""
        results = [
            ScanResult(
                task_id='test1',
                status='completed',
                findings=[
                    {'path': '/admin', 'status': 200, 'size': 1000},
                    {'path': '/backup', 'status': 403, 'size': 500}
                ],
                metrics={'execution_time': 2.0},
                timestamp=datetime.now().isoformat()
            ),
            ScanResult(
                task_id='test2',
                status='completed',
                findings=[
                    {'path': '/api', 'status': 200, 'size': 2000}
                ],
                metrics={'execution_time': 1.0},
                timestamp=datetime.now().isoformat()
            )
        ]
        
        summary = mcp_coordinator.get_scan_summary(results)
        
        assert summary['total_tasks'] == 2
        assert summary['completed_tasks'] == 2
        assert summary['total_findings'] == 3
        assert summary['execution_time'] == 3.0
        assert len(summary['top_findings']) == 3


# Performance Benchmarks
class TestMCPPerformance:
    
    @pytest.mark.benchmark
    def test_cms_detection_performance(self, mcp_coordinator, benchmark):
        """Benchmark CMS detection"""
        content = '<html>' + 'wp-content' * 100 + '</html>'
        
        result = benchmark(mcp_coordinator._detect_cms, content, {})
        assert result == 'WordPress'
    
    @pytest.mark.benchmark
    def test_wordlist_selection_performance(self, mcp_coordinator, sample_target_info, benchmark):
        """Benchmark wordlist selection"""
        result = benchmark(mcp_coordinator._select_wordlist, sample_target_info)
        assert result == 'wordpress.txt'
    
    @pytest.mark.benchmark
    def test_extension_selection_performance(self, mcp_coordinator, sample_target_info, benchmark):
        """Benchmark extension selection"""
        result = benchmark(mcp_coordinator._select_extensions, sample_target_info)
        assert 'php' in result


# Edge Cases and Error Conditions
class TestMCPEdgeCases:
    
    @pytest.mark.asyncio
    async def test_analyze_target_timeout(self, mcp_coordinator):
        """Test target analysis with timeout"""
        url = 'http://timeout.com'
        
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError()):
            target_info = await mcp_coordinator.analyze_target(url)
            
            assert target_info.url == url
            assert target_info.server_type is None
    
    @pytest.mark.asyncio
    async def test_ai_query_rate_limited(self, ai_connector):
        """Test AI query when rate limited"""
        # Exhaust rate limit
        for _ in range(60):
            ai_connector._check_rate_limit('openai')
        
        response = await ai_connector.query_ai_agent("context", "question", provider='openai')
        assert response is None
    
    @pytest.mark.asyncio
    async def test_ai_query_api_error(self, ai_connector):
        """Test AI query with API error"""
        with patch('aiohttp.ClientSession.post', side_effect=Exception("API Error")):
            response = await ai_connector._query_openai("context", "question")
            assert response is None
    
    def test_empty_technology_stack(self, mcp_coordinator):
        """Test with empty technology stack"""
        target_info = TargetInfo(
            url='http://test.com',
            domain='test.com'
        )
        
        wordlist = mcp_coordinator._select_wordlist(target_info)
        assert wordlist == 'common.txt'
        
        extensions = mcp_coordinator._select_extensions(target_info)
        assert 'html' in extensions  # Should have default extensions
    
    @pytest.mark.asyncio
    async def test_malformed_ai_response(self, mcp_coordinator, sample_target_info):
        """Test handling malformed AI response"""
        mcp_coordinator.intelligence_mode = 'AI_AGENT'
        
        # Malformed response
        ai_response = "This is not a properly formatted response"
        
        with patch.object(mcp_coordinator.ai_connector, 'query_ai_agent', 
                         return_value=ai_response):
            insights = await mcp_coordinator._get_ai_target_analysis(sample_target_info)
            
            # Should handle gracefully
            assert insights is not None
            assert isinstance(insights, dict)
    
    @pytest.mark.parametrize("server_type,expected_threads", [
        ("nginx/1.18.0", 20),
        ("Apache/2.4", 15),
        ("cloudflare", 5),
        ("Unknown", 10),
        (None, 10)
    ])
    def test_thread_calculation_parametrized(self, mcp_coordinator, server_type, expected_threads):
        """Parameterized test for thread calculation"""
        target_info = TargetInfo(
            url='http://test.com',
            domain='test.com',
            server_type=server_type
        )
        
        threads = mcp_coordinator._calculate_threads(target_info)
        assert threads == expected_threads