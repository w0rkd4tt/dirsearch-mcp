"""
Wappalyzer integration plugin for Dirsearch MCP
Detects technologies used by the target website
"""

import aiohttp
import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..plugin_base import Plugin
from ..data_formats import TargetData


class WappalyzerPlugin(Plugin):
    """
    Wappalyzer plugin for technology detection
    
    This plugin enhances target analysis by detecting:
    - CMS (WordPress, Joomla, Drupal, etc.)
    - Frameworks (React, Angular, Vue, etc.)
    - Libraries (jQuery, Bootstrap, etc.)
    - Server software (Apache, Nginx, IIS, etc.)
    - Analytics tools
    - And more...
    """
    
    name = "wappalyzer"
    version = "1.0.0"
    description = "Technology detection using Wappalyzer"
    author = "Dirsearch MCP Team"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Wappalyzer plugin"""
        super().__init__(config)
        
        # Default configuration
        self.technologies_db = None
        self.cache = {}
        self.session = None
        
        # Configuration options
        self.cache_enabled = self.get_config('cache_enabled', True)
        self.timeout = self.get_config('timeout', 10)
        self.user_agent = self.get_config('user_agent', 
            'Mozilla/5.0 (compatible; Wappalyzer/1.0)')
        
    async def initialize(self):
        """Initialize the plugin"""
        self.log("Initializing Wappalyzer plugin...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': self.user_agent}
        )
        
        # Load technologies database
        await self._load_technologies_db()
        
        self.log("Wappalyzer plugin initialized successfully")
        
    async def cleanup(self):
        """Cleanup plugin resources"""
        if self.session:
            await self.session.close()
            
    async def _load_technologies_db(self):
        """Load Wappalyzer technologies database"""
        # In a real implementation, this would load the actual Wappalyzer DB
        # For demo purposes, we'll use a simplified version
        self.technologies_db = {
            'WordPress': {
                'headers': {'X-Powered-By': 'W3 Total Cache'},
                'meta': {'generator': 'WordPress'},
                'scripts': ['/wp-includes/', '/wp-content/'],
                'implies': ['PHP', 'MySQL']
            },
            'Joomla': {
                'headers': {'X-Content-Encoded-By': 'Joomla!'},
                'meta': {'generator': 'Joomla'},
                'scripts': ['/media/jui/', '/components/'],
                'implies': ['PHP']
            },
            'React': {
                'scripts': ['react.min.js', 'react.production.min.js'],
                'html': ['data-reactroot', '_reactRootContainer']
            },
            'jQuery': {
                'scripts': ['jquery.min.js', 'jquery-\\d+\\.\\d+\\.\\d+']
            },
            'Bootstrap': {
                'scripts': ['bootstrap.min.js'],
                'styles': ['bootstrap.min.css']
            },
            'Apache': {
                'headers': {'Server': 'Apache'}
            },
            'Nginx': {
                'headers': {'Server': 'nginx'}
            },
            'PHP': {
                'headers': {'X-Powered-By': 'PHP'},
                'cookies': {'PHPSESSID': ''}
            },
            'ASP.NET': {
                'headers': {'X-Powered-By': 'ASP.NET'},
                'cookies': {'ASP.NET_SessionId': ''}
            }
        }
        
    async def on_target_analyzed(self, target_data: TargetData):
        """
        Enhanced target analysis with technology detection
        
        Args:
            target_data: Target analysis data
        """
        self.log(f"Analyzing technologies for {target_data.url}")
        
        # Check cache
        if self.cache_enabled and target_data.domain in self.cache:
            technologies = self.cache[target_data.domain]
        else:
            # Detect technologies
            technologies = await self._detect_technologies(target_data)
            
            # Cache results
            if self.cache_enabled:
                self.cache[target_data.domain] = technologies
                
        # Update target data with detected technologies
        if technologies:
            # Add to technology stack
            for tech in technologies:
                if tech not in target_data.technology_stack:
                    target_data.technology_stack.append(tech)
                    
            # Detect CMS
            cms_list = ['WordPress', 'Joomla', 'Drupal', 'Magento', 'Shopify']
            for tech in technologies:
                if tech in cms_list and not target_data.detected_cms:
                    target_data.detected_cms = tech
                    
            self.log(f"Detected technologies: {', '.join(technologies)}")
            
    async def _detect_technologies(self, target_data: TargetData) -> List[str]:
        """
        Detect technologies used by the target
        
        Args:
            target_data: Target data
            
        Returns:
            List of detected technologies
        """
        detected = []
        
        try:
            # Fetch the homepage
            async with self.session.get(target_data.url) as response:
                html = await response.text()
                headers = dict(response.headers)
                
                # Check each technology
                for tech_name, tech_data in self.technologies_db.items():
                    if await self._check_technology(tech_name, tech_data, 
                                                  html, headers, target_data):
                        detected.append(tech_name)
                        
                        # Add implied technologies
                        if 'implies' in tech_data:
                            for implied in tech_data['implies']:
                                if implied not in detected:
                                    detected.append(implied)
                                    
        except Exception as e:
            self.log(f"Error detecting technologies: {e}", "error")
            
        return detected
        
    async def _check_technology(self, name: str, data: Dict[str, Any], 
                              html: str, headers: Dict[str, str],
                              target_data: TargetData) -> bool:
        """
        Check if a specific technology is present
        
        Args:
            name: Technology name
            data: Technology detection patterns
            html: Page HTML
            headers: Response headers
            target_data: Target data
            
        Returns:
            True if technology is detected
        """
        # Check headers
        if 'headers' in data:
            for header, pattern in data['headers'].items():
                if header in headers:
                    if pattern in headers[header]:
                        return True
                        
        # Check meta tags
        if 'meta' in data:
            for meta_name, pattern in data['meta'].items():
                if f'name="{meta_name}"' in html and pattern in html:
                    return True
                    
        # Check scripts
        if 'scripts' in data:
            for script in data['scripts']:
                if script in html:
                    return True
                    
        # Check styles
        if 'styles' in data:
            for style in data['styles']:
                if style in html:
                    return True
                    
        # Check HTML patterns
        if 'html' in data:
            for pattern in data['html']:
                if pattern in html:
                    return True
                    
        # Check cookies
        if 'cookies' in data and hasattr(target_data, 'cookies'):
            for cookie_name in data['cookies']:
                if cookie_name in target_data.cookies:
                    return True
                    
        return False
        
    async def on_scan_completed(self, scan_data):
        """
        Generate technology report after scan completion
        
        Args:
            scan_data: Completed scan data
        """
        if not scan_data.target_info.technology_stack:
            return
            
        self.log("\n=== Technology Detection Report ===")
        self.log(f"Target: {scan_data.target}")
        self.log(f"Detected Technologies: {', '.join(scan_data.target_info.technology_stack)}")
        
        if scan_data.target_info.detected_cms:
            self.log(f"CMS: {scan_data.target_info.detected_cms}")
            
            # Provide CMS-specific recommendations
            recommendations = self._get_cms_recommendations(scan_data.target_info.detected_cms)
            if recommendations:
                self.log("\nRecommendations:")
                for rec in recommendations:
                    self.log(f"  - {rec}")
                    
    def _get_cms_recommendations(self, cms: str) -> List[str]:
        """Get CMS-specific scanning recommendations"""
        recommendations = {
            'WordPress': [
                'Check /wp-admin/ and /wp-login.php for admin panel',
                'Look for /wp-content/uploads/ for uploaded files',
                'Check /wp-json/ for REST API endpoints',
                'Try common plugin paths like /wp-content/plugins/',
                'Check for xmlrpc.php (often vulnerable)'
            ],
            'Joomla': [
                'Check /administrator/ for admin panel',
                'Look for /components/ and /modules/',
                'Check /configuration.php~ for backup files',
                'Try /api/ for REST API endpoints'
            ],
            'Drupal': [
                'Check /admin/ and /user/login for admin access',
                'Look for /sites/default/files/',
                'Check CHANGELOG.txt for version info',
                'Try /node/ paths for content'
            ]
        }
        
        return recommendations.get(cms, [])
        
    async def on_finding(self, finding: Dict[str, Any]):
        """
        Analyze findings for technology-specific patterns
        
        Args:
            finding: Discovery finding
        """
        path = finding.get('path', '')
        
        # Detect technology-specific paths
        tech_patterns = {
            'WordPress': ['/wp-', 'wordpress'],
            'Joomla': ['/components/', '/modules/', 'joomla'],
            'Drupal': ['/sites/', 'drupal'],
            'Laravel': ['/storage/', 'laravel'],
            'Symfony': ['/bundles/', 'symfony'],
            'Django': ['/static/', '/media/', 'django'],
            'Ruby on Rails': ['/assets/', 'rails']
        }
        
        for tech, patterns in tech_patterns.items():
            for pattern in patterns:
                if pattern in path.lower():
                    finding['meta'] = finding.get('meta', {})
                    finding['meta']['detected_technology'] = tech
                    self.log(f"Technology hint in path: {tech} - {path}")
                    break