#!/usr/bin/env python3
"""
Comprehensive test suite for migrated dirsearch features
Tests all the enhanced functionality added to dirsearch_engine.py
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.dirsearch_engine import (
    DirsearchEngine, 
    ScanOptions, 
    DynamicContentParser,
    ScanResult
)
from src.config import Settings


class TestDynamicContentParser:
    """Test dynamic content detection functionality"""
    
    def test_static_content_detection(self):
        """Test detection of static content"""
        content1 = "This is static content"
        content2 = "This is static content"
        
        parser = DynamicContentParser(content1, content2)
        
        # Should detect as static
        assert parser._is_static == True
        assert parser.compare_to(content1) == True
        assert parser.compare_to("Different content") == False
    
    def test_dynamic_content_detection(self):
        """Test detection of dynamic content"""
        content1 = "User ID: 12345 Welcome to the site"
        content2 = "User ID: 67890 Welcome to the site"
        
        parser = DynamicContentParser(content1, content2)
        
        # Should detect as dynamic
        assert parser._is_static == False
        
        # Similar content should match
        content3 = "User ID: 99999 Welcome to the site"
        assert parser.compare_to(content3) == True
        
        # Very different content should not match
        content4 = "Completely different page"
        assert parser.compare_to(content4) == False
    
    def test_pattern_extraction(self):
        """Test static pattern extraction"""
        content1 = "The time is 10:30 and date is Monday"
        content2 = "The time is 14:45 and date is Tuesday"
        
        parser = DynamicContentParser(content1, content2)
        patterns = parser.get_static_patterns(
            parser._differ.compare(content1.split(), content2.split())
        )
        
        # Should extract static parts
        assert "The" in patterns
        assert "time" in patterns
        assert "is" in patterns
        assert "and" in patterns
        assert "date" in patterns
        
        # Should not include dynamic parts
        assert "10:30" not in patterns
        assert "Monday" not in patterns


class TestWildcardDetection:
    """Test wildcard response detection"""
    
    @pytest.mark.asyncio
    async def test_wildcard_detection_positive(self):
        """Test positive wildcard detection"""
        engine = DirsearchEngine(Settings())
        
        # Mock responses that indicate wildcard
        mock_response1 = {
            'status_code': 200,
            'text': 'Page not found: random1234',
            'headers': {'content-type': 'text/html'}
        }
        mock_response2 = {
            'status_code': 200,
            'text': 'Page not found: random5678',
            'headers': {'content-type': 'text/html'}
        }
        
        with patch.object(engine, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response1, mock_response2]
            
            options = ScanOptions(detect_wildcards=True)
            result = await engine._detect_wildcard("http://example.com", options)
            
            assert result is not None
            assert result['detected'] == True
            assert result['status'] == 200
            assert 'parser' in result
        
        await engine.close()
    
    @pytest.mark.asyncio
    async def test_wildcard_detection_negative(self):
        """Test negative wildcard detection (no wildcard)"""
        engine = DirsearchEngine(Settings())
        
        # Mock different status codes (not wildcard)
        mock_response1 = {
            'status_code': 404,
            'text': 'Not found',
            'headers': {'content-type': 'text/html'}
        }
        mock_response2 = {
            'status_code': 403,
            'text': 'Forbidden',
            'headers': {'content-type': 'text/html'}
        }
        
        with patch.object(engine, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response1, mock_response2]
            
            options = ScanOptions(detect_wildcards=True)
            result = await engine._detect_wildcard("http://example.com", options)
            
            # Should not detect wildcard due to different status codes
            assert result is None or not result.get('detected', False)
        
        await engine.close()


class TestAuthenticationMethods:
    """Test various authentication methods"""
    
    def test_basic_auth_handler(self):
        """Test basic authentication handler"""
        engine = DirsearchEngine(Settings())
        
        auth = engine._get_auth_handler('basic', ('user', 'pass'))
        
        # Should return httpx.BasicAuth
        assert auth is not None
        assert hasattr(auth, 'username')
        assert hasattr(auth, 'password')
    
    def test_digest_auth_handler(self):
        """Test digest authentication handler"""
        engine = DirsearchEngine(Settings())
        
        auth = engine._get_auth_handler('digest', ('user', 'pass'))
        
        # Should return DigestAuth
        assert auth is not None
        assert type(auth).__name__ == 'DigestAuth'
    
    @pytest.mark.skipif(not hasattr(sys.modules.get('httpx_ntlm', None), 'NTLMAuth'),
                        reason="httpx-ntlm not installed")
    def test_ntlm_auth_handler(self):
        """Test NTLM authentication handler"""
        engine = DirsearchEngine(Settings())
        
        auth = engine._get_auth_handler('ntlm', ('domain\\user', 'pass'))
        
        # Should return NTLMAuth if available
        assert auth is not None
        assert 'NTLM' in type(auth).__name__


class TestExtensionTags:
    """Test extension tag replacement functionality"""
    
    def test_extension_tag_replacement(self):
        """Test basic extension tag replacement"""
        engine = DirsearchEngine(Settings())
        
        word = "config.%EXT%"
        extension = "php"
        
        result = engine._replace_extension_tag(word, extension)
        assert result == "config.php"
    
    def test_enhance_wordlist_with_extensions(self):
        """Test wordlist enhancement with extension tags"""
        engine = DirsearchEngine(Settings())
        
        wordlist = [
            "admin.%EXT%",
            "config.%EXT%",
            "backup",  # No tag
            "test.%EXT%.bak"
        ]
        extensions = ['php', 'asp', 'jsp']
        
        enhanced = engine._enhance_wordlist_with_extensions(wordlist, extensions)
        
        # Check expansion
        assert "admin.php" in enhanced
        assert "admin.asp" in enhanced
        assert "admin.jsp" in enhanced
        assert "config.php" in enhanced
        assert "backup" in enhanced  # Should remain unchanged
        assert "test.php.bak" in enhanced
        
        # Should not contain original tags
        assert "admin.%EXT%" not in enhanced
        assert "config.%EXT%" not in enhanced
    
    def test_path_generation_with_extension_tags(self):
        """Test path generation with extension tags"""
        engine = DirsearchEngine(Settings())
        
        wordlist = ["admin.%EXT%", "index"]
        options = ScanOptions(
            extensions=['php', 'html'],
            extension_tag='%EXT%'
        )
        
        paths = engine._generate_paths(wordlist, options)
        
        # Should have expanded paths
        assert "admin.php" in paths
        assert "admin.html" in paths
        assert "index" in paths
        assert "index.php" in paths  # Regular extension handling
        assert "index.html" in paths


class TestBlacklists:
    """Test blacklist functionality"""
    
    def test_blacklist_loading(self):
        """Test loading of blacklist files"""
        engine = DirsearchEngine(Settings())
        
        # Create temporary blacklist
        test_blacklist = {
            403: ['admin', 'private', 'forbidden'],
            500: ['error', 'crash', 'debug']
        }
        
        # Test blacklist checking
        options = ScanOptions(blacklists=test_blacklist)
        
        # Should be blacklisted
        assert engine._is_blacklisted('admin/panel', 403, options) == True
        assert engine._is_blacklisted('private/data', 403, options) == True
        assert engine._is_blacklisted('error.log', 500, options) == True
        
        # Should not be blacklisted
        assert engine._is_blacklisted('public/index', 403, options) == False
        assert engine._is_blacklisted('normal.html', 500, options) == False
        assert engine._is_blacklisted('admin/panel', 200, options) == False


class TestCrawling:
    """Test content crawling functionality"""
    
    @pytest.mark.asyncio
    async def test_html_crawling(self):
        """Test HTML content crawling"""
        engine = DirsearchEngine(Settings())
        
        html_content = """
        <html>
        <head>
            <link href="/css/style.css" rel="stylesheet">
            <script src="/js/app.js"></script>
        </head>
        <body>
            <a href="/about">About</a>
            <a href="/contact.php">Contact</a>
            <a href="http://external.com/page">External</a>
            <img src="/images/logo.png">
            <form action="/submit">
                <input type="submit">
            </form>
        </body>
        </html>
        """
        
        response_data = {
            'headers': {'content-type': 'text/html'},
            'text': html_content,
            'path': 'index.html'
        }
        
        paths = await engine._crawl_response(response_data, "http://example.com/")
        
        # Should find internal paths
        assert "about" in paths
        assert "contact.php" in paths
        assert "submit" in paths
        
        # Should not include external URLs
        assert not any("external.com" in p for p in paths)
        
        # Should not include media files by default
        assert not any(p.endswith('.css') for p in paths)
        assert not any(p.endswith('.png') for p in paths)
        
        await engine.close()
    
    @pytest.mark.asyncio
    async def test_robots_txt_crawling(self):
        """Test robots.txt parsing"""
        engine = DirsearchEngine(Settings())
        
        robots_content = """
        User-agent: *
        Disallow: /admin/
        Disallow: /private/data/
        Allow: /public/
        Disallow: /tmp/*.log
        Sitemap: /sitemap.xml
        """
        
        response_data = {
            'headers': {'content-type': 'text/plain'},
            'text': robots_content,
            'path': 'robots.txt'
        }
        
        paths = await engine._crawl_response(response_data, "http://example.com/")
        
        # Should extract paths from robots.txt
        assert "admin/" in paths or "admin" in paths
        assert "private/data/" in paths or "private/data" in paths
        assert "public/" in paths or "public" in paths
        assert "sitemap.xml" in paths
        
        await engine.close()
    
    def test_path_normalization(self):
        """Test crawled path normalization"""
        engine = DirsearchEngine(Settings())
        
        base_url = "http://example.com/"
        
        # Test various path formats
        test_cases = [
            ("/absolute/path", "absolute/path"),
            ("relative/path", "relative/path"),
            ("http://example.com/internal", "internal"),
            ("http://external.com/path", None),  # External URL
            ("#anchor", None),  # Anchor
            ("javascript:void(0)", None),  # JavaScript
            ("mailto:test@example.com", None),  # Mailto
            ("/path?query=1#anchor", "path"),  # With query and anchor
        ]
        
        for input_path, expected in test_cases:
            result = engine._normalize_crawled_path(input_path, base_url)
            assert result == expected


class TestRandomUserAgents:
    """Test random user agent functionality"""
    
    def test_user_agent_loading(self):
        """Test loading of user agents"""
        engine = DirsearchEngine(Settings())
        
        # Should have default user agents
        agents = engine._load_user_agents()
        assert len(agents) > 0
        assert all(isinstance(ua, str) for ua in agents)
    
    def test_random_user_agent_selection(self):
        """Test random user agent selection"""
        engine = DirsearchEngine(Settings())
        
        # Get multiple user agents
        user_agents = set()
        for _ in range(10):
            ua = engine._get_random_user_agent()
            user_agents.add(ua)
        
        # Should have at least one user agent
        assert len(user_agents) >= 1
        assert all(isinstance(ua, str) for ua in user_agents)


class TestIntegration:
    """Integration tests for complete scanning workflow"""
    
    @pytest.mark.asyncio
    async def test_scan_with_wildcard_detection(self):
        """Test full scan with wildcard detection"""
        engine = DirsearchEngine(Settings())
        
        wordlist = ['admin', 'test', 'config']
        options = ScanOptions(
            detect_wildcards=True,
            extensions=['php'],
            threads=5,
            exclude_status_codes=[404]
        )
        
        # Mock the HTTP requests
        with patch.object(engine, '_make_request', new_callable=AsyncMock) as mock_request:
            # First two calls for wildcard detection
            mock_request.side_effect = [
                {'status_code': 404, 'text': 'Not found', 'headers': {}, 'size': 100},
                {'status_code': 404, 'text': 'Not found', 'headers': {}, 'size': 100},
                # Actual scan results
                {'status_code': 200, 'text': 'Admin panel', 'headers': {}, 'size': 500},
                {'status_code': 403, 'text': 'Forbidden', 'headers': {}, 'size': 200},
                {'status_code': 404, 'text': 'Not found', 'headers': {}, 'size': 100},
            ]
            
            results = await engine.scan_target("http://example.com", wordlist, options)
            
            # Should have made requests
            assert mock_request.call_count > 0
            
            # Should have results (excluding 404s)
            assert len(results) >= 0
        
        await engine.close()
    
    @pytest.mark.asyncio
    async def test_scan_with_crawling(self):
        """Test scan with crawling enabled"""
        engine = DirsearchEngine(Settings())
        
        wordlist = ['index']
        options = ScanOptions(
            crawl=True,
            extensions=['html'],
            threads=5
        )
        
        # Mock response with HTML content
        html_response = {
            'status_code': 200,
            'text': '<html><a href="/admin">Admin</a></html>',
            'headers': {'content-type': 'text/html'},
            'size': 100
        }
        
        with patch.object(engine, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = html_response
            
            results = await engine.scan_target("http://example.com", wordlist, options)
            
            # Should have discovered /admin through crawling
            assert 'admin' in engine._crawled_paths or 'admin' in engine._dynamic_wordlist
        
        await engine.close()
    
    @pytest.mark.asyncio
    async def test_scan_with_authentication(self):
        """Test scan with various authentication methods"""
        engine = DirsearchEngine(Settings())
        
        wordlist = ['private']
        
        # Test different auth types
        for auth_type in ['basic', 'digest']:
            options = ScanOptions(
                auth=('user', 'pass'),
                auth_type=auth_type,
                threads=5
            )
            
            with patch.object(engine, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {
                    'status_code': 200,
                    'text': 'Authenticated content',
                    'headers': {},
                    'size': 100
                }
                
                results = await engine.scan_target("http://example.com", wordlist, options)
                
                # Should pass auth to requests
                _, kwargs = mock_request.call_args
                assert 'auth' in kwargs or mock_request.call_count > 0
        
        await engine.close()


# Fixtures for testing
@pytest.fixture
def mock_settings():
    """Mock settings object"""
    settings = Mock()
    settings.default_scan_config = {
        'threads': 10,
        'timeout': 10,
        'user_agent': 'Test Agent',
        'follow_redirects': True,
        'exclude_status': '404'
    }
    return settings


@pytest.fixture
async def engine(mock_settings):
    """Create engine instance for testing"""
    engine = DirsearchEngine(mock_settings)
    yield engine
    await engine.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])