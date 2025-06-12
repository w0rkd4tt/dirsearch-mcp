import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from aiohttp import ClientSession, ClientResponse
from pathlib import Path
import json

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanResponse
from src.config.settings import Settings


# Fixtures
@pytest.fixture
def settings():
    """Create test settings"""
    return Settings(
        default_scan_config={
            'threads': 10,
            'timeout': 5,
            'user_agent': 'Test-Agent',
            'follow_redirects': True,
            'retry_attempts': 2
        },
        paths={
            'wordlists': 'tests/data/wordlists'
        }
    )


@pytest.fixture
def engine(settings):
    """Create DirsearchEngine instance"""
    return DirsearchEngine(settings)


@pytest.fixture
def sample_wordlist(tmp_path):
    """Create a sample wordlist file"""
    wordlist_file = tmp_path / "test_wordlist.txt"
    wordlist_file.write_text("admin\nlogin\ntest\napi\nconfig.php\nbackup.zip")
    return str(wordlist_file)


@pytest.fixture
def mock_responses():
    """Mock HTTP responses for different scenarios"""
    return {
        'http://test.com/admin': (200, 'Admin Panel', {'Content-Type': 'text/html'}),
        'http://test.com/login': (301, '', {'Location': '/auth/login'}),
        'http://test.com/test': (404, 'Not Found', {}),
        'http://test.com/api': (403, 'Forbidden', {}),
        'http://test.com/config.php': (200, '<?php', {'Content-Type': 'text/plain'}),
        'http://test.com/backup.zip': (200, 'PK', {'Content-Type': 'application/zip'}),
        'http://test.com/error': (500, 'Internal Server Error', {}),
        'http://test.com/timeout': 'timeout',
        'http://test.com/slow': (200, 'Slow response', {}, 3.0)  # 3 second delay
    }


class MockResponse:
    """Mock aiohttp response"""
    def __init__(self, status, text, headers, url=''):
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


# Test DirsearchEngine Core Methods
class TestDirsearchEngine:
    
    @pytest.mark.asyncio
    async def test_load_wordlist(self, engine, sample_wordlist):
        """Test wordlist loading"""
        words = await engine._load_wordlist(sample_wordlist)
        
        assert len(words) == 6
        assert 'admin' in words
        assert 'backup.zip' in words
    
    @pytest.mark.asyncio
    async def test_load_wordlist_not_found(self, engine):
        """Test loading non-existent wordlist"""
        with pytest.raises(FileNotFoundError):
            await engine._load_wordlist('nonexistent.txt')
    
    def test_generate_paths(self, engine):
        """Test path generation with extensions"""
        base_path = 'test'
        extensions = ['php', 'html']
        
        paths = engine._generate_paths(base_path, extensions)
        
        assert 'test' in paths
        assert 'test.php' in paths
        assert 'test.html' in paths
        assert len(paths) == 3
    
    def test_is_valid_response_default(self, engine):
        """Test response validation with default settings"""
        # Valid responses
        assert engine._is_valid_response(200, {}) == True
        assert engine._is_valid_response(301, {}) == True
        assert engine._is_valid_response(403, {}) == True
        
        # Invalid responses
        assert engine._is_valid_response(404, {}) == False
        assert engine._is_valid_response(500, {}) == True  # Server errors are interesting
    
    def test_is_valid_response_custom_exclude(self, engine):
        """Test response validation with custom exclusions"""
        # Set custom exclusions
        engine.config['exclude_status'] = '403,500'
        
        assert engine._is_valid_response(403, {}) == False
        assert engine._is_valid_response(500, {}) == False
        assert engine._is_valid_response(200, {}) == True
    
    @pytest.mark.asyncio
    async def test_scan_single_path_success(self, engine, mock_responses):
        """Test scanning a single path successfully"""
        url = 'http://test.com/admin'
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value = MockResponse(200, 'Admin Panel', {'Content-Type': 'text/html'}, url)
            
            result = await engine._scan_single_path(None, url, '/admin')
            
            assert result is not None
            assert result['path'] == '/admin'
            assert result['status'] == 200
            assert result['size'] == len('Admin Panel')
            assert 'response_time' in result
    
    @pytest.mark.asyncio
    async def test_scan_single_path_404(self, engine):
        """Test scanning path that returns 404"""
        url = 'http://test.com/notfound'
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value = MockResponse(404, 'Not Found', {}, url)
            
            result = await engine._scan_single_path(None, url, '/notfound')
            
            assert result is None  # 404s should be filtered out
    
    @pytest.mark.asyncio
    async def test_scan_single_path_timeout(self, engine):
        """Test handling timeout during scan"""
        url = 'http://test.com/timeout'
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await engine._scan_single_path(None, url, '/timeout')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_scan_single_path_with_retry(self, engine):
        """Test retry mechanism on failure"""
        url = 'http://test.com/flaky'
        engine.config['retry_attempts'] = 2
        
        call_count = 0
        
        async def mock_get_flaky(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise aiohttp.ClientError("Connection failed")
            return MockResponse(200, 'Success', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get_flaky):
            result = await engine._scan_single_path(None, url, '/flaky')
            
            assert result is not None
            assert result['status'] == 200
            assert call_count == 2  # First attempt failed, second succeeded
    
    @pytest.mark.asyncio
    async def test_execute_scan(self, engine, sample_wordlist):
        """Test full scan execution"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=sample_wordlist,
            extensions=['php', 'html'],
            threads=5
        )
        
        # Mock responses for all paths
        async def mock_get(url, *args, **kwargs):
            if 'admin' in url:
                return MockResponse(200, 'Admin', {}, url)
            elif 'config.php' in url:
                return MockResponse(200, 'Config', {}, url)
            else:
                return MockResponse(404, 'Not Found', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            response = await engine.execute_scan(scan_request)
        
        assert isinstance(response, ScanResponse)
        assert response.target_url == 'http://test.com'
        assert len(response.results) > 0
        assert response.statistics['total_requests'] > 0
        assert response.statistics['found_paths'] > 0
    
    @pytest.mark.parametrize("status,content,expected", [
        (200, "Admin Panel", True),
        (301, "", True),
        (403, "Forbidden", True),
        (404, "Not Found", False),
        (500, "Error", True),
    ])
    def test_response_validation_parametrized(self, engine, status, content, expected):
        """Parameterized test for response validation"""
        result = engine._is_valid_response(status, {})
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_concurrent_scanning(self, engine, sample_wordlist):
        """Test concurrent scanning with multiple threads"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=sample_wordlist,
            threads=20  # High thread count
        )
        
        request_times = []
        
        async def mock_get(url, *args, **kwargs):
            request_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate network delay
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            start_time = time.time()
            response = await engine.execute_scan(scan_request)
            total_time = time.time() - start_time
        
        # With 6 words and 20 threads, should complete faster than sequential
        assert total_time < 0.6  # Should be much less than 6 * 0.1 seconds
        assert len(request_times) == 6
    
    @pytest.mark.asyncio
    async def test_custom_headers(self, engine):
        """Test scanning with custom headers"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist='admin',
            custom_headers={'Authorization': 'Bearer token123'}
        )
        
        captured_headers = None
        
        async def mock_get(url, headers=None, **kwargs):
            nonlocal captured_headers
            captured_headers = headers
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            with patch.object(engine, '_load_wordlist', return_value=['admin']):
                await engine.execute_scan(scan_request)
        
        assert captured_headers is not None
        assert 'Authorization' in captured_headers
        assert captured_headers['Authorization'] == 'Bearer token123'
    
    @pytest.mark.asyncio
    async def test_follow_redirects(self, engine):
        """Test redirect following behavior"""
        engine.config['follow_redirects'] = False
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value = MockResponse(301, '', {'Location': '/new-path'}, 'http://test.com/old')
            
            result = await engine._scan_single_path(None, 'http://test.com/old', '/old')
            
            assert result is not None
            assert result['status'] == 301
            assert result['redirect'] == '/new-path'
    
    @pytest.mark.asyncio
    async def test_error_handling_and_statistics(self, engine, sample_wordlist):
        """Test error handling and statistics collection"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=sample_wordlist,
            threads=5
        )
        
        error_count = 0
        
        async def mock_get(url, *args, **kwargs):
            nonlocal error_count
            if 'error' in url:
                error_count += 1
                raise aiohttp.ClientError("Connection failed")
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            # Add 'error' to wordlist to trigger errors
            with patch.object(engine, '_load_wordlist', return_value=['admin', 'error', 'test']):
                response = await engine.execute_scan(scan_request)
        
        assert response.statistics['errors'] > 0
        assert error_count > 0


# Performance Benchmarks
class TestDirsearchPerformance:
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_scan_performance_small_wordlist(self, engine, benchmark):
        """Benchmark scanning with small wordlist"""
        wordlist = ['admin', 'test', 'api', 'config']
        
        async def run_scan():
            scan_request = ScanRequest(
                base_url='http://test.com',
                wordlist=wordlist,
                threads=10
            )
            
            async def mock_get(url, *args, **kwargs):
                await asyncio.sleep(0.01)  # Simulate 10ms response time
                return MockResponse(200, 'OK', {}, url)
            
            with patch('aiohttp.ClientSession.get', side_effect=mock_get):
                with patch.object(engine, '_load_wordlist', return_value=wordlist):
                    return await engine.execute_scan(scan_request)
        
        result = benchmark(lambda: asyncio.run(run_scan()))
        assert result.statistics['total_requests'] == len(wordlist)
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_scan_performance_large_wordlist(self, engine, benchmark):
        """Benchmark scanning with large wordlist"""
        wordlist = [f'path{i}' for i in range(1000)]
        
        async def run_scan():
            scan_request = ScanRequest(
                base_url='http://test.com',
                wordlist=wordlist,
                threads=50
            )
            
            async def mock_get(url, *args, **kwargs):
                # No delay to test pure processing speed
                return MockResponse(200, 'OK', {}, url)
            
            with patch('aiohttp.ClientSession.get', side_effect=mock_get):
                with patch.object(engine, '_load_wordlist', return_value=wordlist):
                    return await engine.execute_scan(scan_request)
        
        result = benchmark(lambda: asyncio.run(run_scan()))
        assert result.statistics['total_requests'] == len(wordlist)
    
    def test_path_generation_performance(self, engine, benchmark):
        """Benchmark path generation with extensions"""
        extensions = ['php', 'html', 'js', 'jsp', 'asp', 'aspx']
        
        def generate_paths():
            paths = []
            for i in range(100):
                paths.extend(engine._generate_paths(f'path{i}', extensions))
            return paths
        
        result = benchmark(generate_paths)
        assert len(result) == 100 * (len(extensions) + 1)


# Edge Cases and Error Conditions
class TestDirsearchEdgeCases:
    
    @pytest.mark.asyncio
    async def test_empty_wordlist(self, engine):
        """Test scanning with empty wordlist"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=[]
        )
        
        with patch.object(engine, '_load_wordlist', return_value=[]):
            response = await engine.execute_scan(scan_request)
        
        assert response.statistics['total_requests'] == 0
        assert len(response.results) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_url(self, engine):
        """Test scanning with invalid URL"""
        scan_request = ScanRequest(
            base_url='not-a-valid-url',
            wordlist=['admin']
        )
        
        with patch.object(engine, '_load_wordlist', return_value=['admin']):
            with pytest.raises(Exception):
                await engine.execute_scan(scan_request)
    
    @pytest.mark.asyncio
    async def test_very_long_paths(self, engine):
        """Test scanning with very long paths"""
        long_path = 'a' * 1000
        
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=[long_path]
        )
        
        async def mock_get(url, *args, **kwargs):
            assert len(url) > 1000
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            with patch.object(engine, '_load_wordlist', return_value=[long_path]):
                response = await engine.execute_scan(scan_request)
        
        assert response.statistics['total_requests'] == 1
    
    @pytest.mark.asyncio
    async def test_special_characters_in_paths(self, engine):
        """Test scanning with special characters in paths"""
        special_paths = [
            'path with spaces',
            'path?query=1',
            'path#fragment',
            'path/../../../etc/passwd',
            'path%20encoded'
        ]
        
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=special_paths
        )
        
        scanned_urls = []
        
        async def mock_get(url, *args, **kwargs):
            scanned_urls.append(url)
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            with patch.object(engine, '_load_wordlist', return_value=special_paths):
                response = await engine.execute_scan(scan_request)
        
        assert len(scanned_urls) == len(special_paths)
        # URLs should be properly encoded
        assert any('%20' in url for url in scanned_urls)
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, engine):
        """Test connection pool limits with many concurrent requests"""
        scan_request = ScanRequest(
            base_url='http://test.com',
            wordlist=[f'path{i}' for i in range(100)],
            threads=100  # Very high concurrency
        )
        
        active_connections = 0
        max_active = 0
        
        async def mock_get(url, *args, **kwargs):
            nonlocal active_connections, max_active
            active_connections += 1
            max_active = max(max_active, active_connections)
            await asyncio.sleep(0.1)
            active_connections -= 1
            return MockResponse(200, 'OK', {}, url)
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_get):
            with patch.object(engine, '_load_wordlist', return_value=[f'path{i}' for i in range(100)]):
                await engine.execute_scan(scan_request)
        
        # Should respect connection limits
        assert max_active <= 100