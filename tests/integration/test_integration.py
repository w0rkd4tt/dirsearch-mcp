import pytest
import asyncio
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime

from src.core.mcp_coordinator import MCPCoordinator, TargetInfo, ScanTask
from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.config.settings import Settings
from src.utils.logger import LoggerSetup
from src.utils.reporter import ReportGenerator
from src.cli.interactive_menu import InteractiveMenu


# Integration Test Fixtures
@pytest.fixture
def integration_settings():
    """Settings for integration tests"""
    return Settings(
        default_scan_config={
            'threads': 20,
            'timeout': 10,
            'user_agent': 'Integration-Test',
            'follow_redirects': True
        },
        ai_config={
            'openai_api_key': 'test-integration-key'
        },
        paths={
            'wordlists': 'tests/data/wordlists',
            'reports': 'tests/output/reports',
            'logs': 'tests/output/logs'
        }
    )


@pytest.fixture
def test_wordlist(tmp_path):
    """Create test wordlist for integration tests"""
    wordlist_dir = tmp_path / "wordlists"
    wordlist_dir.mkdir()
    
    # Common wordlist
    common_file = wordlist_dir / "common.txt"
    common_file.write_text("\n".join([
        "admin", "api", "login", "dashboard", "config",
        "backup", "test", "users", "upload", "download"
    ]))
    
    # WordPress wordlist
    wp_file = wordlist_dir / "wordpress.txt"
    wp_file.write_text("\n".join([
        "wp-admin", "wp-content", "wp-includes", "wp-login.php",
        "xmlrpc.php", "wp-config.php", "wp-json"
    ]))
    
    return str(wordlist_dir)


@pytest.fixture
async def integrated_system(integration_settings, test_wordlist):
    """Create integrated system components"""
    integration_settings.paths['wordlists'] = test_wordlist
    
    # Initialize logging
    LoggerSetup.initialize(integration_settings.paths['logs'])
    
    # Create components
    mcp = MCPCoordinator(integration_settings)
    engine = DirsearchEngine(integration_settings)
    reporter = ReportGenerator(integration_settings.paths['reports'])
    
    # Initialize MCP
    await mcp.initialize()
    
    return {
        'mcp': mcp,
        'engine': engine,
        'reporter': reporter,
        'settings': integration_settings
    }


# Mock HTTP Server for controlled testing
class MockHTTPServer:
    """Mock HTTP server for integration testing"""
    
    def __init__(self):
        self.endpoints = {
            '/': (200, '<html><title>Test Site</title></html>', {'Server': 'nginx/1.18.0'}),
            '/admin': (200, 'Admin Panel', {'Content-Type': 'text/html'}),
            '/api': (200, '{"status": "ok"}', {'Content-Type': 'application/json'}),
            '/login': (301, '', {'Location': '/auth/login'}),
            '/wp-admin': (301, '', {'Location': '/wp-admin/'}),
            '/wp-content': (200, 'WordPress Content', {}),
            '/backup': (403, 'Forbidden', {}),
            '/config': (404, 'Not Found', {}),
            '/error': (500, 'Internal Server Error', {}),
        }
        self.request_log = []
    
    async def handle_request(self, url, **kwargs):
        """Handle HTTP request"""
        path = url.replace('http://test.local', '')
        self.request_log.append({
            'path': path,
            'time': time.time(),
            'headers': kwargs.get('headers', {})
        })
        
        if path in self.endpoints:
            status, content, headers = self.endpoints[path]
            return MockResponse(status, content, headers, url)
        
        return MockResponse(404, 'Not Found', {}, url)


class MockResponse:
    """Mock HTTP response"""
    def __init__(self, status, text, headers, url):
        self.status = status
        self._text = text
        self.headers = headers
        self.url = url
    
    async def text(self):
        return self._text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# End-to-End Integration Tests
class TestEndToEndIntegration:
    
    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, integrated_system):
        """Test complete scan workflow from analysis to reporting"""
        mcp = integrated_system['mcp']
        engine = integrated_system['engine']
        reporter = integrated_system['reporter']
        
        target_url = 'http://test.local'
        mock_server = MockHTTPServer()
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_server.handle_request):
            # Step 1: Target Analysis
            target_info = await mcp.analyze_target(target_url)
            
            assert target_info.url == target_url
            assert target_info.server_type == 'nginx/1.18.0'
            
            # Step 2: Generate Scan Plan
            scan_plan = await mcp.generate_scan_plan(target_info)
            
            assert len(scan_plan) > 0
            assert scan_plan[0].task_type == 'directory_enumeration'
            
            # Step 3: Execute Scan
            scan_request = ScanRequest(
                base_url=target_url,
                wordlist=Path(integrated_system['settings'].paths['wordlists']) / 'common.txt',
                extensions=['php', 'html'],
                threads=10
            )
            
            scan_response = await engine.execute_scan(scan_request)
            
            assert scan_response.statistics['total_requests'] > 0
            assert len(scan_response.results) > 0
            
            # Step 4: Generate Report
            scan_data = {
                'target_url': target_url,
                'target_domain': 'test.local',
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 5.0,
                'intelligence_mode': mcp.intelligence_mode,
                'target_analysis': {
                    'server_type': target_info.server_type,
                    'technology_stack': target_info.technology_stack
                },
                'scan_results': [{
                    'task_id': 'test',
                    'status': 'completed',
                    'findings': scan_response.results,
                    'metrics': scan_response.statistics,
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            report_files = reporter.generate_report(scan_data)
            
            assert 'json' in report_files
            assert Path(report_files['json']).exists()
    
    @pytest.mark.asyncio
    async def test_wordpress_detection_and_scanning(self, integrated_system):
        """Test WordPress-specific detection and scanning"""
        mcp = integrated_system['mcp']
        target_url = 'http://wordpress.local'
        
        # Mock WordPress site
        wordpress_endpoints = {
            '/': (200, '<html><link href="/wp-content/themes/test.css"></html>', 
                  {'Server': 'Apache/2.4', 'X-Powered-By': 'PHP/7.4'}),
            '/wp-admin': (301, '', {'Location': '/wp-admin/'}),
            '/wp-content': (200, 'WordPress Content', {}),
            '/wp-includes': (403, 'Forbidden', {}),
            '/wp-login.php': (200, 'WordPress Login', {}),
        }
        
        async def mock_wp_request(url, **kwargs):
            path = url.replace('http://wordpress.local', '')
            if path in wordpress_endpoints:
                status, content, headers = wordpress_endpoints[path]
                return MockResponse(status, content, headers, url)
            return MockResponse(404, 'Not Found', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_wp_request):
            # Analyze target
            target_info = await mcp.analyze_target(target_url)
            
            assert target_info.detected_cms == 'WordPress'
            assert 'PHP/7.4' in target_info.technology_stack
            
            # Generate scan plan
            scan_plan = await mcp.generate_scan_plan(target_info)
            
            # Should have WordPress-specific tasks
            wp_tasks = [t for t in scan_plan if 'wp' in t.task_id or 'WordPress' in str(t.parameters)]
            assert len(wp_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_ai_integration(self, integrated_system):
        """Test MCP with AI agent integration"""
        mcp = integrated_system['mcp']
        
        # Mock AI responses
        mock_ai_response = """Based on analysis:
1. Additional technologies: Node.js, React
2. Recommended wordlists: api_endpoints.txt, nodejs_common.txt
3. Parameters: threads: 25, timeout: 15"""
        
        with patch.object(mcp.ai_connector, 'detect_ai_availability', return_value=(True, 'openai')):
            await mcp.initialize()
            assert mcp.intelligence_mode == 'AI_AGENT'
            
            with patch.object(mcp.ai_connector, 'query_ai_agent', return_value=mock_ai_response):
                target_info = TargetInfo(
                    url='http://api.test.com',
                    domain='api.test.com',
                    server_type='nginx',
                    technology_stack=['Node.js']
                )
                
                # Test AI-enhanced analysis
                insights = await mcp._get_ai_target_analysis(target_info)
                assert insights is not None
                
                # Test AI-enhanced parameter optimization
                params = await mcp.optimize_parameters(target_info)
                assert params['threads'] == 25
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_logging(self, integrated_system, tmp_path):
        """Test error handling and recovery across components"""
        mcp = integrated_system['mcp']
        engine = integrated_system['engine']
        
        # Create a wordlist that will cause some errors
        error_wordlist = tmp_path / "error_test.txt"
        error_wordlist.write_text("valid\ntimeout\nerror\nvalid2")
        
        target_url = 'http://error-test.local'
        error_count = 0
        
        async def mock_error_request(url, **kwargs):
            nonlocal error_count
            path = url.split('/')[-1]
            
            if path == 'timeout':
                raise asyncio.TimeoutError()
            elif path == 'error':
                error_count += 1
                raise aiohttp.ClientError("Connection failed")
            elif path == 'valid' or path == 'valid2':
                return MockResponse(200, 'OK', {}, url)
            
            return MockResponse(404, 'Not Found', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_error_request):
            scan_request = ScanRequest(
                base_url=target_url,
                wordlist=str(error_wordlist),
                threads=5
            )
            
            # Should handle errors gracefully
            response = await engine.execute_scan(scan_request)
            
            assert response.statistics['errors'] > 0
            assert response.statistics['found_paths'] == 2  # Only valid paths
            assert error_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_scan_performance(self, integrated_system):
        """Test concurrent scanning performance"""
        engine = integrated_system['engine']
        
        # Create large wordlist
        large_wordlist = [f'path{i}' for i in range(100)]
        
        request_times = []
        max_concurrent = 0
        current_concurrent = 0
        
        async def mock_concurrent_request(url, **kwargs):
            nonlocal max_concurrent, current_concurrent
            
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            request_times.append(time.time())
            
            await asyncio.sleep(0.01)  # Simulate network delay
            
            current_concurrent -= 1
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_concurrent_request):
            with patch.object(engine, '_load_wordlist', return_value=large_wordlist):
                scan_request = ScanRequest(
                    base_url='http://perf-test.local',
                    wordlist='large.txt',
                    threads=50
                )
                
                start_time = time.time()
                response = await engine.execute_scan(scan_request)
                total_time = time.time() - start_time
                
                # Should complete much faster than sequential
                sequential_time = len(large_wordlist) * 0.01
                assert total_time < sequential_time / 2
                
                # Should use concurrent connections
                assert max_concurrent > 10
                assert response.statistics['total_requests'] == 100


# Component Integration Tests
class TestComponentIntegration:
    
    @pytest.mark.asyncio
    async def test_mcp_engine_integration(self, integrated_system):
        """Test integration between MCP and DirsearchEngine"""
        mcp = integrated_system['mcp']
        engine = integrated_system['engine']
        
        # MCP analyzes and creates plan
        target_info = TargetInfo(
            url='http://integration.test',
            domain='integration.test',
            server_type='Apache/2.4',
            technology_stack=['PHP', 'MySQL']
        )
        
        scan_plan = await mcp.generate_scan_plan(target_info)
        
        # Convert MCP tasks to engine requests
        for task in scan_plan:
            if task.task_type == 'directory_enumeration':
                scan_request = ScanRequest(
                    base_url=target_info.url,
                    wordlist=task.parameters.get('wordlist', 'common.txt'),
                    extensions=task.parameters.get('extensions', []),
                    threads=task.parameters.get('threads', 10)
                )
                
                # Engine should be able to execute MCP-generated requests
                with patch('aiohttp.ClientSession.get') as mock_get:
                    mock_get.return_value = MockResponse(200, 'OK', {}, '')
                    with patch.object(engine, '_load_wordlist', return_value=['test']):
                        response = await engine.execute_scan(scan_request)
                        assert response is not None
    
    def test_logger_reporter_integration(self, integrated_system, tmp_path):
        """Test integration between Logger and Reporter"""
        reporter = integrated_system['reporter']
        
        # Log some MCP decisions
        LoggerSetup.log_mcp_decision(
            'target_analysis',
            {'url': 'http://test.com'},
            'Detected WordPress CMS',
            confidence=0.95
        )
        
        LoggerSetup.log_performance_metric(
            'scan_speed',
            150.5,
            'requests/sec',
            {'threads': 20}
        )
        
        # Create scan data with logged decisions
        scan_data = {
            'target_url': 'http://test.com',
            'target_domain': 'test.com',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 10.0,
            'intelligence_mode': 'AI_AGENT',
            'mcp_decisions': [
                {
                    'type': 'target_analysis',
                    'decision': 'Detected WordPress CMS',
                    'confidence': 0.95,
                    'context': {'url': 'http://test.com'}
                }
            ],
            'scan_results': [],
            'performance_metrics': {
                'scan_speed': 150.5,
                'total_requests': 1000
            }
        }
        
        # Generate reports
        report_files = reporter.generate_report(scan_data)
        
        # Verify reports contain logged information
        with open(report_files['json'], 'r') as f:
            report_data = json.load(f)
            
            assert len(report_data['mcp_decisions']) > 0
            assert report_data['mcp_decisions'][0]['confidence'] == 0.95
            assert report_data['performance_metrics']['scan_speed'] == 150.5
    
    @pytest.mark.asyncio
    async def test_cli_integration(self, integrated_system, monkeypatch):
        """Test CLI integration with core components"""
        menu = InteractiveMenu()
        menu.settings = integrated_system['settings']
        menu.mcp_coordinator = integrated_system['mcp']
        menu.dirsearch_engine = integrated_system['engine']
        menu.report_generator = integrated_system['reporter']
        
        # Mock user inputs
        inputs = iter(['http://cli-test.local', 'y'])  # URL and confirm
        monkeypatch.setattr('rich.prompt.Prompt.ask', lambda *args, **kwargs: next(inputs))
        monkeypatch.setattr('rich.prompt.Confirm.ask', lambda *args, **kwargs: True)
        
        # Mock HTTP responses
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value = MockResponse(
                200, '<html><title>CLI Test</title></html>', 
                {'Server': 'nginx'}, 'http://cli-test.local'
            )
            
            # Get target URL (mocked input)
            target_url = menu._get_target_url()
            assert target_url == 'http://cli-test.local'
            
            # Execute scan through CLI
            with patch.object(menu.dirsearch_engine, 'execute_scan') as mock_scan:
                from src.core.dirsearch_engine import ScanResponse
                mock_scan.return_value = ScanResponse(
                    target_url='http://cli-test.local',
                    results=[{'path': '/admin', 'status': 200, 'size': 1000}],
                    statistics={'total_requests': 10, 'found_paths': 1, 'errors': 0}
                )
                
                await menu._execute_scan(target_url, quick_mode=True)


# Performance Integration Tests
class TestPerformanceIntegration:
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_full_scan_performance(self, integrated_system, benchmark):
        """Benchmark full scan performance"""
        mcp = integrated_system['mcp']
        engine = integrated_system['engine']
        
        async def run_full_scan():
            # Mock fast responses
            async def mock_fast_response(url, **kwargs):
                return MockResponse(200, 'OK', {}, url)
            
            with patch('aiohttp.ClientSession.get', side_effect=mock_fast_response):
                # Analyze
                target_info = await mcp.analyze_target('http://perf.test')
                
                # Plan
                scan_plan = await mcp.generate_scan_plan(target_info)
                
                # Execute
                with patch.object(engine, '_load_wordlist', return_value=['a', 'b', 'c']):
                    scan_request = ScanRequest(
                        base_url='http://perf.test',
                        wordlist='test.txt',
                        threads=10
                    )
                    return await engine.execute_scan(scan_request)
        
        result = benchmark(lambda: asyncio.run(run_full_scan()))
        assert result.statistics['total_requests'] > 0
    
    @pytest.mark.benchmark
    def test_report_generation_performance(self, integrated_system, benchmark):
        """Benchmark report generation performance"""
        reporter = integrated_system['reporter']
        
        # Create large scan data
        large_findings = [
            {'path': f'/path{i}', 'status': 200, 'size': 1000}
            for i in range(1000)
        ]
        
        scan_data = {
            'target_url': 'http://perf.test',
            'target_domain': 'perf.test',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': 60.0,
            'intelligence_mode': 'AI_AGENT',
            'scan_results': [{
                'task_id': 'perf_test',
                'status': 'completed',
                'findings': large_findings,
                'metrics': {'total_requests': 10000},
                'timestamp': datetime.now().isoformat()
            }]
        }
        
        def generate_all_reports():
            return reporter.generate_report(scan_data, format='all')
        
        result = benchmark(generate_all_reports)
        assert 'json' in result
        assert 'html' in result
        assert 'markdown' in result


# Real Target Tests (Controlled Environment)
@pytest.mark.real_target
class TestRealTargets:
    """Tests against real targets in controlled environment"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not pytest.config.getoption("--real-targets"), 
                        reason="Real target tests disabled by default")
    async def test_scan_local_server(self, integrated_system):
        """Test scanning a local test server"""
        # This test assumes a local test server is running
        # Start with: python -m http.server 8888
        
        mcp = integrated_system['mcp']
        engine = integrated_system['engine']
        
        target_url = 'http://localhost:8888'
        
        # Analyze target
        target_info = await mcp.analyze_target(target_url)
        assert target_info.server_type is not None
        
        # Quick scan with limited wordlist
        scan_request = ScanRequest(
            base_url=target_url,
            wordlist=['index.html', 'test', 'admin'],
            threads=5
        )
        
        with patch.object(engine, '_load_wordlist', return_value=['index.html', 'test', 'admin']):
            response = await engine.execute_scan(scan_request)
            
            assert response.statistics['total_requests'] == 3
            # At least index.html should exist
            assert response.statistics['found_paths'] >= 1