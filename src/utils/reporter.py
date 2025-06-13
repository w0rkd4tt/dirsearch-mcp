import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import html
from dataclasses import asdict
import base64
import io
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ReportGenerator:
    """Multi-format report generator for scan results"""
    
    def __init__(self, report_dir: str = "report"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different formats
        for subdir in ['json', 'html', 'markdown']:
            (self.report_dir / subdir).mkdir(exist_ok=True)
    
    def generate_report(self, scan_data: Dict[str, Any], format: str = 'all') -> Dict[str, str]:
        """Generate report in specified format(s)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"scan_report_{scan_data.get('target_domain', 'unknown')}_{timestamp}"
        
        generated_files = {}
        
        if format in ['json', 'all']:
            json_file = self._generate_json_report(scan_data, base_name)
            generated_files['json'] = str(json_file)
        
        if format in ['html', 'all']:
            html_file = self._generate_html_report(scan_data, base_name)
            generated_files['html'] = str(html_file)
        
        if format in ['markdown', 'all']:
            md_file = self._generate_markdown_report(scan_data, base_name)
            generated_files['markdown'] = str(md_file)
        
        return generated_files
    
    def _generate_json_report(self, scan_data: Dict[str, Any], base_name: str) -> Path:
        """Generate JSON format report"""
        file_path = self.report_dir / 'json' / f"{base_name}.json"
        
        # Convert any dataclasses to dicts
        clean_data = self._clean_data_for_json(scan_data)
        
        # Extract scan configuration
        scan_config = clean_data.get('scan_config', {})
        
        # Structure the report focusing on target, config, and directory tree
        report = {
            'target': {
                'url': clean_data.get('target_url', ''),
                'domain': clean_data.get('target_domain', ''),
                'server_type': clean_data.get('target_analysis', {}).get('server_type', 'Unknown'),
                'technology_stack': clean_data.get('target_analysis', {}).get('technology_stack', [])
            },
            'scan_configuration': {
                'wordlist': scan_config.get('wordlist', 'unknown'),
                'threads': scan_config.get('threads', 10),
                'timeout': scan_config.get('timeout', 10),
                'extensions': scan_config.get('extensions', []),
                'follow_redirects': scan_config.get('follow_redirects', False),
                'recursive': scan_config.get('recursive', False),
                'recursion_depth': scan_config.get('recursion_depth', 0),
                'detect_wildcards': scan_config.get('detect_wildcards', True),
                'intelligence_mode': clean_data.get('intelligence_mode', 'LOCAL'),
                'user_agent': scan_config.get('user_agent', 'Default')
            },
            'scan_summary': {
                'start_time': clean_data.get('start_time', ''),
                'end_time': clean_data.get('end_time', ''),
                'duration': clean_data.get('duration', 0),
                'total_requests': clean_data.get('performance_metrics', {}).get('total_requests', 0),
                'findings_count': len(clean_data.get('scan_results', []))
            },
            'directory_tree': self._generate_directory_tree(clean_data),
            'detailed_results': clean_data.get('scan_results', []),
            'metadata': {
                'report_version': '2.0',
                'generated_at': datetime.now().isoformat(),
                'generator': 'DirsearchMCP'
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _generate_html_report(self, scan_data: Dict[str, Any], base_name: str) -> Path:
        """Generate HTML format report with interactive features"""
        file_path = self.report_dir / 'html' / f"{base_name}.html"
        
        # Generate charts
        charts = self._generate_charts(scan_data)
        
        # HTML template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dirsearch MCP Scan Report - {scan_data.get('target_domain', 'Unknown')}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/dataTables.bootstrap5.min.css">
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Directory Scan Report</h1>
            <div class="target-info">
                <h2>{html.escape(scan_data.get('target_url', ''))}</h2>
                <div class="metadata">
                    <span>Domain: <strong>{html.escape(scan_data.get('target_domain', ''))}</strong></span>
                    <span>Date: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></span>
                </div>
            </div>
        </header>
        
        {self._generate_scan_config_html(scan_data)}
        {self._generate_directory_tree_html(scan_data)}
        {self._generate_scan_summary_html(scan_data)}
        
        <footer>
            <p>Generated by Dirsearch MCP - Intelligent Directory Scanner with AI Integration</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript_code()}
    </script>
</body>
</html>"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _generate_markdown_report(self, scan_data: Dict[str, Any], base_name: str) -> Path:
        """Generate Markdown format report"""
        file_path = self.report_dir / 'markdown' / f"{base_name}.md"
        
        scan_config = scan_data.get('scan_config', {})
        
        md_content = f"""# Directory Scan Report

## Target: {scan_data.get('target_url', 'Unknown')}

**Domain:** {scan_data.get('target_domain', 'Unknown')}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Scan Configuration

| Setting | Value |
|---------|-------|
| Wordlist | {scan_config.get('wordlist', 'default')} |
| Threads | {scan_config.get('threads', 10)} |
| Extensions | {', '.join(scan_config.get('extensions', [])) or 'None'} |
| Recursive | {'Yes' if scan_config.get('recursive', False) else 'No'} |
| Follow Redirects | {'Yes' if scan_config.get('follow_redirects', False) else 'No'} |
| Wildcard Detection | {'Enabled' if scan_config.get('detect_wildcards', True) else 'Disabled'} |
| User Agent | {scan_config.get('user_agent', 'Default')[:50]} |
| Intelligence Mode | {scan_data.get('intelligence_mode', 'LOCAL')} |

---

## Directory Tree

{self._generate_directory_tree_md(scan_data)}

---

## Scan Summary

{self._generate_scan_summary_md(scan_data)}

---

*Generated by Dirsearch MCP - Intelligent Directory Scanner*
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return file_path
    
    def _clean_data_for_json(self, data: Any) -> Any:
        """Recursively clean data for JSON serialization"""
        if hasattr(data, '__dict__'):
            return self._clean_data_for_json(asdict(data))
        elif isinstance(data, dict):
            return {k: self._clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_json(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)
    
    def _generate_findings_summary(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate findings summary statistics"""
        # scan_results is directly the array of findings
        all_findings = scan_data.get('scan_results', [])
        
        # Group by status code
        status_groups = {}
        directories = []
        files = []
        
        for finding in all_findings:
            status = finding.get('status', 0)
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(finding)
            
            # Track directories vs files
            if finding.get('is_directory', False):
                directories.append(finding)
            else:
                files.append(finding)
        
        return {
            'total_findings': len(all_findings),
            'by_status': {str(k): len(v) for k, v in status_groups.items()},
            'interesting_paths': [f for f in all_findings if f.get('status') in [200, 301, 302, 401, 403]],
            'directories_found': len(directories),
            'files_found': len(files),
            'directory_list': [d.get('path', '') for d in directories],
            'potential_vulnerabilities': self._identify_vulnerabilities(all_findings)
        }
    
    def _identify_vulnerabilities(self, findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify potential vulnerabilities from findings"""
        vulnerabilities = []
        
        for finding in findings:
            path = finding.get('path', '')
            status = finding.get('status', 0)
            
            # Check for backup files
            if any(ext in path for ext in ['.bak', '.old', '.backup', '.copy']):
                vulnerabilities.append({
                    'type': 'Backup File',
                    'path': path,
                    'severity': 'High',
                    'description': 'Potential backup file found that may contain sensitive data'
                })
            
            # Check for configuration files
            if any(name in path for name in ['config', 'settings', '.env', 'database']):
                vulnerabilities.append({
                    'type': 'Configuration File',
                    'path': path,
                    'severity': 'High',
                    'description': 'Configuration file that may expose sensitive settings'
                })
            
            # Check for admin interfaces
            if status == 401 and any(admin in path for admin in ['admin', 'manager', 'console']):
                vulnerabilities.append({
                    'type': 'Admin Interface',
                    'path': path,
                    'severity': 'Medium',
                    'description': 'Protected admin interface found'
                })
        
        return vulnerabilities
    
    def _generate_recommendations(self, scan_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate recommendations based on findings"""
        recommendations = []
        findings_summary = self._generate_findings_summary(scan_data)
        
        # Based on directories found
        if findings_summary.get('directories_found', 0) > 0:
            recommendations.append({
                'category': 'Directory Enumeration',
                'recommendation': 'Directories Discovered',
                'details': f"Found {findings_summary['directories_found']} directories. Consider recursive scanning of discovered directories.",
                'priority': 'High'
            })
        
        # Based on vulnerabilities
        vulns = findings_summary.get('potential_vulnerabilities', [])
        if vulns:
            vuln_types = set(v['type'] for v in vulns)
            if 'Backup File' in vuln_types:
                recommendations.append({
                    'priority': 'High',
                    'category': 'Security',
                    'recommendation': 'Remove or secure backup files',
                    'details': 'Backup files were found that may contain sensitive information. These should be removed from the web root or properly secured.'
                })
            
            if 'Configuration File' in vuln_types:
                recommendations.append({
                    'priority': 'High',
                    'category': 'Security',
                    'recommendation': 'Protect configuration files',
                    'details': 'Configuration files should not be accessible via web. Move them outside the web root or implement proper access controls.'
                })
        
        # Based on server configuration
        target_analysis = scan_data.get('target_analysis', {})
        if not target_analysis.get('security_headers'):
            recommendations.append({
                'priority': 'Medium',
                'category': 'Security Headers',
                'recommendation': 'Implement security headers',
                'details': 'Consider implementing security headers like X-Frame-Options, X-Content-Type-Options, and Content-Security-Policy.'
            })
        
        # Performance recommendations
        if scan_data.get('performance_metrics', {}).get('avg_response_time', 0) > 2:
            recommendations.append({
                'priority': 'Low',
                'category': 'Performance',
                'recommendation': 'Optimize server response time',
                'details': 'The server response time is higher than optimal. Consider implementing caching or optimizing backend performance.'
            })
        
        return recommendations
    
    def _generate_charts(self, scan_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for HTML report"""
        charts = {}
        
        if not MATPLOTLIB_AVAILABLE:
            return charts
        
        try:
            # Status code distribution chart
            findings_summary = self._generate_findings_summary(scan_data)
            status_dist = findings_summary.get('by_status', {})
            
            if status_dist:
                fig, ax = plt.subplots(figsize=(8, 6))
                statuses = list(status_dist.keys())
                counts = list(status_dist.values())
                
                colors = ['#28a745' if s == '200' else '#dc3545' if s.startswith('4') else '#ffc107' for s in statuses]
                ax.bar(statuses, counts, color=colors)
                ax.set_xlabel('Status Code')
                ax.set_ylabel('Count')
                ax.set_title('HTTP Status Code Distribution')
                
                # Convert to base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                charts['status_distribution'] = base64.b64encode(buffer.read()).decode()
                plt.close()
            
            # Timeline chart if available
            perf_metrics = scan_data.get('performance_metrics', {})
            if 'timeline' in perf_metrics:
                fig, ax = plt.subplots(figsize=(10, 6))
                timeline = perf_metrics['timeline']
                times = [t['time'] for t in timeline]
                rates = [t['rate'] for t in timeline]
                
                ax.plot(times, rates, 'b-', linewidth=2)
                ax.set_xlabel('Time (seconds)')
                ax.set_ylabel('Requests/second')
                ax.set_title('Scan Performance Over Time')
                ax.grid(True, alpha=0.3)
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                charts['performance_timeline'] = base64.b64encode(buffer.read()).decode()
                plt.close()
        except Exception as e:
            # If chart generation fails, continue without charts
            pass
        
        return charts
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background-color: #2c3e50;
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        
        header h1 {
            margin-bottom: 1rem;
            font-size: 2.5rem;
        }
        
        .target-info h2 {
            color: #3498db;
            margin: 1rem 0 0.5rem 0;
            font-size: 1.8rem;
            word-break: break-all;
        }
        
        .metadata {
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .config-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        
        .config-label {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .config-value {
            color: #555;
        }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .stat-item {
            text-align: center;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .stat-value {
            display: block;
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .primary-section {
            border: 2px solid #3498db;
        }
        
        .primary-section h2 {
            color: #3498db;
            font-size: 1.8rem;
        }
        
        .tree-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 1200px) {
            .tree-container {
                grid-template-columns: 1fr;
            }
        }
        
        .tree-visualization pre {
            margin: 0;
            background-color: #2c3e50 !important;
            color: #ecf0f1 !important;
        }
        
        .tree-info {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .tree-stat {
            text-align: center;
            padding: 0.75rem;
            background-color: #f8f9fa;
            border-radius: 6px;
        }
        
        .tree-stat-value {
            display: block;
            font-size: 1.5rem;
            font-weight: bold;
            color: #3498db;
        }
        
        .tree-stat-label {
            font-size: 0.8rem;
            color: #7f8c8d;
            text-transform: uppercase;
        }
        
        .legend-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }
        
        .legend-item span {
            font-size: 1.2rem;
        }
        
        .section {
            background-color: white;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ecf0f1;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 4px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .summary-card h3 {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }
        
        .summary-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .status-200 { color: #28a745; }
        .status-301, .status-302 { color: #17a2b8; }
        .status-401, .status-403 { color: #ffc107; }
        .status-404 { color: #6c757d; }
        .status-500 { color: #dc3545; }
        
        .chart-container {
            margin: 2rem 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .vulnerability {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        .vulnerability.high {
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }
        
        .recommendation {
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        .recommendation.high {
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }
        
        .mcp-decision {
            background-color: #e7f3ff;
            border-left: 4px solid #3498db;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        .decision-type {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        
        .decision-details {
            font-size: 0.9rem;
            color: #555;
        }
        
        footer {
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
            font-size: 0.9rem;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #ecf0f1;
            margin-bottom: 1rem;
        }
        
        .tab {
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            background-color: transparent;
            border: none;
            font-size: 1rem;
            color: #7f8c8d;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #3498db;
            border-bottom: 2px solid #3498db;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        """
    
    def _get_javascript_code(self) -> str:
        """Get JavaScript code for HTML report"""
        return """
        $(document).ready(function() {
            // Initialize DataTables
            $('.data-table').DataTable({
                pageLength: 25,
                order: [[1, 'asc']],
                responsive: true
            });
            
            // Tab functionality
            $('.tab').click(function() {
                const tabId = $(this).data('tab');
                
                // Update active tab
                $('.tab').removeClass('active');
                $(this).addClass('active');
                
                // Show corresponding content
                $('.tab-content').removeClass('active');
                $('#' + tabId).addClass('active');
            });
            
            // Collapsible sections
            $('.section h2').click(function() {
                $(this).parent().find('.section-content').toggle(300);
            });
        });
        """
    
    def _generate_executive_summary_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate executive summary section for HTML"""
        summary = self._generate_findings_summary(scan_data)
        duration = scan_data.get('duration', 0)
        
        return f"""
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Findings</h3>
                    <div class="value">{summary['total_findings']}</div>
                </div>
                <div class="summary-card">
                    <h3>Scan Duration</h3>
                    <div class="value">{duration:.1f}s</div>
                </div>
                <div class="summary-card">
                    <h3>Success Rate</h3>
                    <div class="value">{summary['by_status'].get('200', 0)}</div>
                </div>
                <div class="summary-card">
                    <h3>Potential Issues</h3>
                    <div class="value">{len(summary['potential_vulnerabilities'])}</div>
                </div>
            </div>
        </div>
        """
    
    def _generate_target_analysis_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate target analysis section for HTML"""
        target = scan_data.get('target_analysis', {})
        
        tech_stack = target.get('technology_stack', [])
        tech_list = ''.join(f'<li>{html.escape(tech)}</li>' for tech in tech_stack) if tech_stack else '<li>None detected</li>'
        
        return f"""
        <div class="section">
            <h2>Target Analysis</h2>
            <div class="section-content">
                <table>
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Server Type</td>
                        <td>{html.escape(target.get('server_type') or 'Unknown')}</td>
                    </tr>
                    <tr>
                        <td>Detected CMS</td>
                        <td>{html.escape(target.get('detected_cms') or 'None')}</td>
                    </tr>
                    <tr>
                        <td>Technology Stack</td>
                        <td><ul>{tech_list}</ul></td>
                    </tr>
                    <tr>
                        <td>Security Headers</td>
                        <td>{len(target.get('security_headers', {}))}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
    
    def _generate_mcp_decisions_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate MCP decisions section for HTML"""
        decisions = scan_data.get('mcp_decisions', [])
        
        if not decisions:
            return ""
        
        decisions_html = ""
        for decision in decisions:
            decisions_html += f"""
            <div class="mcp-decision">
                <div class="decision-type">{html.escape(decision.get('type', ''))}</div>
                <div class="decision-details">
                    <strong>Decision:</strong> {html.escape(decision.get('decision', ''))}
                    <br>
                    <strong>Confidence:</strong> {decision.get('confidence', 1.0):.0%}
                    <br>
                    <strong>Context:</strong> {html.escape(str(decision.get('context', {})))}
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>MCP Coordination Decisions</h2>
            <div class="section-content">
                {decisions_html}
            </div>
        </div>
        """
    
    def _generate_findings_html(self, scan_data: Dict[str, Any], charts: Dict[str, str]) -> str:
        """Generate findings section for HTML"""
        summary = self._generate_findings_summary(scan_data)
        
        # Status distribution chart
        chart_html = ""
        if 'status_distribution' in charts:
            chart_html = f"""
            <div class="chart-container">
                <h3>Status Code Distribution</h3>
                <img src="data:image/png;base64,{charts['status_distribution']}" alt="Status Distribution">
            </div>
            """
        
        # Findings table
        findings_rows = ""
        for finding in summary['interesting_paths'][:50]:  # Limit to 50 entries
            status_class = f"status-{finding.get('status', 0)}"
            type_indicator = "📁" if finding.get('is_directory', False) else "📄"
            findings_rows += f"""
            <tr>
                <td>{html.escape(finding.get('path', ''))}</td>
                <td class="{status_class}">{finding.get('status', '')}</td>
                <td>{finding.get('size', 0)}</td>
                <td>{type_indicator} {'Directory' if finding.get('is_directory', False) else 'File'}</td>
            </tr>
            """
        
        # Vulnerabilities
        vulns_html = ""
        for vuln in summary['potential_vulnerabilities']:
            severity_class = 'high' if vuln['severity'] == 'High' else ''
            vulns_html += f"""
            <div class="vulnerability {severity_class}">
                <strong>{html.escape(vuln['type'])}:</strong> {html.escape(vuln['path'])}
                <br>
                <small>{html.escape(vuln['description'])}</small>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>Scan Results</h2>
            
            {chart_html}
            
            <div class="tabs">
                <button class="tab active" data-tab="all-results-tab">All Results</button>
                <button class="tab" data-tab="findings-tab">Interesting Findings</button>
                <button class="tab" data-tab="directories-tab">Directories</button>
                <button class="tab" data-tab="vulnerabilities-tab">Potential Vulnerabilities</button>
            </div>
            
            <div id="all-results-tab" class="tab-content active">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Path</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>Size</th>
                            <th>Content Type</th>
                            <th>Response Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {self._generate_all_results_rows(scan_data)}
                    </tbody>
                </table>
            </div>
            
            <div id="findings-tab" class="tab-content">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Path</th>
                            <th>Status</th>
                            <th>Size</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {findings_rows}
                    </tbody>
                </table>
            </div>
            
            <div id="directories-tab" class="tab-content">
                {self._generate_directories_html(summary)}
            </div>
            
            <div id="vulnerabilities-tab" class="tab-content">
                {vulns_html if vulns_html else '<p>No potential vulnerabilities detected.</p>'}
            </div>
        </div>
        """
    
    def _generate_performance_html(self, scan_data: Dict[str, Any], charts: Dict[str, str]) -> str:
        """Generate performance section for HTML"""
        metrics = scan_data.get('performance_metrics', {})
        
        # Performance timeline chart
        chart_html = ""
        if 'performance_timeline' in charts:
            chart_html = f"""
            <div class="chart-container">
                <h3>Performance Timeline</h3>
                <img src="data:image/png;base64,{charts['performance_timeline']}" alt="Performance Timeline">
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="section-content">
                {chart_html}
                
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Requests</td>
                        <td>{metrics.get('total_requests', 0)}</td>
                    </tr>
                    <tr>
                        <td>Average Response Time</td>
                        <td>{metrics.get('avg_response_time', 0):.2f}s</td>
                    </tr>
                    <tr>
                        <td>Requests per Second</td>
                        <td>{metrics.get('requests_per_second', 0):.1f}</td>
                    </tr>
                    <tr>
                        <td>Error Rate</td>
                        <td>{metrics.get('error_rate', 0):.1%}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
    
    def _generate_recommendations_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate recommendations section for HTML"""
        recommendations = self._generate_recommendations(scan_data)
        
        if not recommendations:
            return ""
        
        recs_html = ""
        for rec in recommendations:
            priority_class = 'high' if rec['priority'] == 'High' else ''
            recs_html += f"""
            <div class="recommendation {priority_class}">
                <strong>[{rec.get('priority', 'Medium')}] {html.escape(str(rec.get('category', '')))}:</strong> {html.escape(str(rec.get('recommendation', '')))}
                <br>
                <small>{html.escape(str(rec.get('details', '')))}</small>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>Recommendations</h2>
            <div class="section-content">
                {recs_html}
            </div>
        </div>
        """
    
    def _generate_executive_summary_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate executive summary for Markdown"""
        summary = self._generate_findings_summary(scan_data)
        duration = scan_data.get('duration', 0)
        
        return f"""
- **Total Findings:** {summary['total_findings']}
- **Scan Duration:** {duration:.1f} seconds
- **Successful Paths (200 OK):** {summary['by_status'].get('200', 0)}
- **Potential Vulnerabilities:** {len(summary['potential_vulnerabilities'])}
- **Intelligence Mode:** {scan_data.get('intelligence_mode', 'LOCAL')}
"""
    
    def _generate_target_analysis_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate target analysis for Markdown"""
        target = scan_data.get('target_analysis', {})
        tech_stack = target.get('technology_stack', [])
        
        tech_list = '\n'.join(f'- {tech}' for tech in tech_stack) if tech_stack else '- None detected'
        
        return f"""
**Server Type:** {target.get('server_type') or 'Unknown'}  
**Detected CMS:** {target.get('detected_cms') or 'None'}  
**Technology Stack:**
{tech_list}

**Security Headers:** {len(target.get('security_headers', {}))} configured
"""
    
    def _generate_mcp_decisions_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate MCP decisions for Markdown"""
        decisions = scan_data.get('mcp_decisions', [])
        
        if not decisions:
            return "No MCP decisions recorded."
        
        md_content = ""
        for i, decision in enumerate(decisions, 1):
            md_content += f"""
### Decision {i}: {decision.get('type', 'Unknown')}

- **Decision:** {decision.get('decision', '')}
- **Confidence:** {decision.get('confidence', 1.0):.0%}
- **Context:** {decision.get('context', {})}

"""
        
        return md_content
    
    def _generate_findings_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate findings for Markdown"""
        summary = self._generate_findings_summary(scan_data)
        
        # Status distribution
        status_table = "| Status Code | Count |\n|------------|-------|\n"
        for status, count in sorted(summary['by_status'].items()):
            status_table += f"| {status} | {count} |\n"
        
        # Top findings
        findings_table = "\n### Top Interesting Findings\n\n| Path | Status | Size |\n|------|--------|------|\n"
        for finding in summary['interesting_paths'][:20]:
            findings_table += f"| {finding.get('path', '')} | {finding.get('status', '')} | {finding.get('size', 0)} |\n"
        
        # Directories
        dirs_content = "\n### Directories Found\n\n"
        if summary.get('directories_found', 0) > 0:
            dirs_content += f"**Total Directories:** {summary['directories_found']}\n\n"
            dirs_content += "| Directory Path | Type |\n|----------------|------|\n"
            for dir_path in summary.get('directory_list', [])[:20]:  # Limit to 20
                dirs_content += f"| {dir_path} | 📁 Directory |\n"
            if len(summary.get('directory_list', [])) > 20:
                dirs_content += f"| ... and {len(summary.get('directory_list', [])) - 20} more | |\n"
        else:
            dirs_content += "No directories detected.\n"
        
        # Vulnerabilities
        vulns_content = "\n### Potential Vulnerabilities\n\n"
        if summary['potential_vulnerabilities']:
            for vuln in summary['potential_vulnerabilities']:
                vulns_content += f"- **{vuln['type']}** ({vuln['severity']}): `{vuln['path']}`\n  - {vuln['description']}\n"
        else:
            vulns_content += "No potential vulnerabilities detected.\n"
        
        return f"""
### Status Code Distribution

{status_table}

### Summary Statistics

- **Total Findings:** {summary['total_findings']}
- **Directories Found:** {summary.get('directories_found', 0)}
- **Files Found:** {summary.get('files_found', 0)}

{findings_table}

{dirs_content}

{vulns_content}
"""
    
    def _generate_performance_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate performance metrics for Markdown"""
        metrics = scan_data.get('performance_metrics', {})
        
        return f"""
| Metric | Value |
|--------|-------|
| Total Requests | {metrics.get('total_requests', 0)} |
| Average Response Time | {metrics.get('avg_response_time', 0):.2f}s |
| Requests per Second | {metrics.get('requests_per_second', 0):.1f} |
| Error Rate | {metrics.get('error_rate', 0):.1%} |
"""
    
    def _generate_recommendations_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate recommendations for Markdown"""
        recommendations = self._generate_recommendations(scan_data)
        
        if not recommendations:
            return "No specific recommendations at this time."
        
        md_content = ""
        for rec in sorted(recommendations, key=lambda x: x['priority']):
            md_content += f"""
### {rec['priority']} Priority - {rec['category']}

**Recommendation:** {rec['recommendation']}

{rec['details']}

"""
        
        return md_content
    
    def _generate_all_results_rows(self, scan_data: Dict[str, Any]) -> str:
        """Generate table rows for all scan results"""
        results = scan_data.get('scan_results', [])
        rows = ""
        
        for result in results:
            status_class = f"status-{result.get('status', 0)}"
            type_indicator = "📁" if result.get('is_directory', False) else "📄"
            
            rows += f"""
            <tr>
                <td>{html.escape(result.get('path', ''))}</td>
                <td class="{status_class}">{result.get('status', '')}</td>
                <td>{type_indicator} {'Directory' if result.get('is_directory', False) else 'File'}</td>
                <td>{result.get('size', 0)}</td>
                <td>{html.escape(result.get('content_type', 'N/A') or 'N/A')}</td>
                <td>{result.get('response_time', 0):.3f}s</td>
            </tr>
            """
        
        return rows
    
    def _generate_directories_html(self, summary: Dict[str, Any]) -> str:
        """Generate directories section HTML"""
        directories = summary.get('directory_list', [])
        
        if not directories:
            return '<p>No directories found during the scan.</p>'
        
        html_content = f"""
        <div class="directories-summary">
            <p><strong>Total Directories Found:</strong> {summary.get('directories_found', 0)}</p>
            <p>The following directories were discovered and may contain additional resources:</p>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Directory Path</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for directory in directories:
            html_content += f"""
                <tr>
                    <td>📁 {html.escape(str(directory))}</td>
                    <td><span class="badge">Consider recursive scan</span></td>
                </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            
            <div class="recommendation">
                <strong>Recommendation:</strong> These directories may contain additional files and subdirectories. 
                Consider running recursive scans on promising directories to discover more content.
            </div>
        </div>
        """
        
        return html_content
    
    def _generate_scan_config_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate scan configuration section for HTML"""
        scan_config = scan_data.get('scan_config', {})
        
        return f"""
        <div class="section">
            <h2>Scan Configuration</h2>
            <div class="section-content">
                <div class="config-grid">
                    <div class="config-item">
                        <span class="config-label">Wordlist:</span>
                        <span class="config-value">{html.escape(str(scan_config.get('wordlist', 'default')))}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Threads:</span>
                        <span class="config-value">{scan_config.get('threads', 10)}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Extensions:</span>
                        <span class="config-value">{', '.join(scan_config.get('extensions', [])) or 'None'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Recursive:</span>
                        <span class="config-value">{'Yes' if scan_config.get('recursive', False) else 'No'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Follow Redirects:</span>
                        <span class="config-value">{'Yes' if scan_config.get('follow_redirects', False) else 'No'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Wildcard Detection:</span>
                        <span class="config-value">{'Enabled' if scan_config.get('detect_wildcards', True) else 'Disabled'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">User Agent:</span>
                        <span class="config-value">{html.escape(str(scan_config.get('user_agent', 'Default')[:50]))}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Intelligence Mode:</span>
                        <span class="config-value">{scan_data.get('intelligence_mode', 'LOCAL')}</span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_scan_summary_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate scan summary section for HTML"""
        duration = scan_data.get('duration', 0)
        results = scan_data.get('scan_results', [])
        
        # Count by status
        status_counts = {}
        for result in results:
            status = result.get('status', 0)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return f"""
        <div class="section">
            <h2>Scan Summary</h2>
            <div class="section-content">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-value">{len(results)}</span>
                        <span class="stat-label">Total Findings</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{duration:.1f}s</span>
                        <span class="stat-label">Duration</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{status_counts.get(200, 0)}</span>
                        <span class="stat-label">200 OK</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{status_counts.get(301, 0) + status_counts.get(302, 0)}</span>
                        <span class="stat-label">Redirects</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{status_counts.get(403, 0)}</span>
                        <span class="stat-label">Forbidden</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{status_counts.get(401, 0)}</span>
                        <span class="stat-label">Unauthorized</span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_directory_tree_html(self, scan_data: Dict[str, Any]) -> str:
        """Generate directory tree visualization for HTML report"""
        tree_data = self._generate_directory_tree(scan_data)
        
        return f"""
        <div class="section primary-section">
            <h2>📁 Directory Structure</h2>
            <div class="section-content">
                <div class="tree-container">
                    <div class="tree-visualization">
                        <pre style="background-color: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 8px; overflow-x: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; line-height: 1.5;">
{html.escape(str(tree_data.get('visualization', '')))}
                        </pre>
                    </div>
                    
                    <div class="tree-info">
                        <div class="tree-statistics">
                            <h3>Statistics</h3>
                            <div class="stat-grid">
                                <div class="tree-stat">
                                    <span class="tree-stat-value">{tree_data.get('total_items', 0)}</span>
                                    <span class="tree-stat-label">Total Items</span>
                                </div>
                                <div class="tree-stat">
                                    <span class="tree-stat-value">{tree_data.get('statistics', {}).get('total_directories', 0)}</span>
                                    <span class="tree-stat-label">Directories</span>
                                </div>
                                <div class="tree-stat">
                                    <span class="tree-stat-value">{tree_data.get('statistics', {}).get('total_files', 0)}</span>
                                    <span class="tree-stat-label">Files</span>
                                </div>
                                <div class="tree-stat">
                                    <span class="tree-stat-value">{tree_data.get('statistics', {}).get('max_depth', 0)}</span>
                                    <span class="tree-stat-label">Max Depth</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tree-legend">
                            <h3>Legend</h3>
                            <div class="legend-grid">
                                <div class="legend-item"><span>📁</span> Directory</div>
                                <div class="legend-item"><span>📄</span> File</div>
                                <div class="legend-item"><span>🟢</span> 200 OK</div>
                                <div class="legend-item"><span>🟡</span> Redirect</div>
                                <div class="legend-item"><span>🔴</span> Forbidden</div>
                                <div class="legend-item"><span>🔒</span> Auth Required</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_directory_tree(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate directory tree structure from scan results"""
        results = scan_data.get('scan_results', [])
        
        # Build tree structure
        tree = {}
        root_url = scan_data.get('target_url', '')
        
        for result in results:
            if not isinstance(result, dict):
                continue
                
            path = result.get('path', '')
            if not path:
                continue
                
            status = result.get('status', 0)
            is_directory = result.get('is_directory', False)
            size = result.get('size', 0)
            
            # Parse path into segments
            segments = [s for s in str(path).strip('/').split('/') if s]
            
            if not segments:
                continue
            
            # Navigate to the correct position in tree
            current = tree
            for i, segment in enumerate(segments):
                if segment not in current:
                    current[segment] = {
                        '_meta': {
                            'type': 'directory' if i < len(segments) - 1 or is_directory else 'file',
                            'status': None,
                            'size': None,
                            'path': '/' + '/'.join(segments[:i+1])
                        },
                        '_children': {}
                    }
                
                # Update meta for the final segment
                if i == len(segments) - 1:
                    current[segment]['_meta']['status'] = status
                    current[segment]['_meta']['size'] = size
                    current[segment]['_meta']['type'] = 'directory' if is_directory else 'file'
                
                current = current[segment]['_children']
        
        # Generate tree visualization
        tree_lines = []
        self._build_tree_lines(tree, tree_lines, '', True)
        
        # Calculate statistics
        stats = self._calculate_tree_stats(tree)
        
        return {
            'structure': tree,
            'visualization': '\n'.join(tree_lines) if tree_lines else '',
            'statistics': stats,
            'total_items': len(results)
        }
    
    def _build_tree_lines(self, tree: Dict, lines: List[str], prefix: str, is_last: bool):
        """Build tree visualization lines recursively"""
        items = sorted(tree.items())
        
        for i, (name, node) in enumerate(items):
            if name == '_meta':
                continue
            
            is_last_item = i == len(items) - 1
            
            # Build current line
            if prefix == '':
                connector = ''
                extension = ''
            else:
                connector = '└── ' if is_last_item else '├── '
                extension = '    ' if is_last_item else '│   '
            
            meta = node.get('_meta', {})
            status = meta.get('status', '')
            item_type = meta.get('type', 'unknown')
            
            # Status indicators
            status_icon = ''
            if status == 200:
                status_icon = ' 🟢'
            elif status in [301, 302]:
                status_icon = ' 🟡'
            elif status == 403:
                status_icon = ' 🔴'
            elif status == 401:
                status_icon = ' 🔒'
            elif status == 404:
                status_icon = ' ⚫'
            
            # Type indicator
            type_icon = '📁' if item_type == 'directory' else '📄'
            
            # Build line
            line = f"{prefix}{connector}{type_icon} {name}{status_icon}"
            if status:
                line += f" [{status}]"
            
            lines.append(line)
            
            # Process children
            children = node.get('_children', {})
            if children:
                new_prefix = prefix + extension
                self._build_tree_lines(children, lines, new_prefix, is_last_item)
    
    def _calculate_tree_stats(self, tree: Dict, depth: int = 0) -> Dict[str, Any]:
        """Calculate statistics from tree structure"""
        stats = {
            'max_depth': depth,
            'total_directories': 0,
            'total_files': 0,
            'by_status': {},
            'by_depth': {}
        }
        
        for name, node in tree.items():
            if name == '_meta':
                continue
            
            meta = node.get('_meta', {})
            item_type = meta.get('type', 'unknown')
            status = meta.get('status')
            
            # Count by type
            if item_type == 'directory':
                stats['total_directories'] += 1
            else:
                stats['total_files'] += 1
            
            # Count by status
            if status:
                status_str = str(status)
                stats['by_status'][status_str] = stats['by_status'].get(status_str, 0) + 1
            
            # Count by depth
            stats['by_depth'][str(depth)] = stats['by_depth'].get(str(depth), 0) + 1
            
            # Process children
            children = node.get('_children', {})
            if children:
                child_stats = self._calculate_tree_stats(children, depth + 1)
                stats['max_depth'] = max(stats['max_depth'], child_stats['max_depth'])
                stats['total_directories'] += child_stats['total_directories']
                stats['total_files'] += child_stats['total_files']
                
                # Merge status counts
                for status, count in child_stats['by_status'].items():
                    stats['by_status'][status] = stats['by_status'].get(status, 0) + count
                
                # Merge depth counts
                for d, count in child_stats['by_depth'].items():
                    stats['by_depth'][d] = stats['by_depth'].get(d, 0) + count
        
        return stats
    
    def _generate_directory_tree_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate directory tree for Markdown report"""
        tree_data = self._generate_directory_tree(scan_data)
        
        return f"""
### Statistics

- **Total Items:** {tree_data.get('total_items', 0)}
- **Directories:** {tree_data.get('statistics', {}).get('total_directories', 0)}
- **Files:** {tree_data.get('statistics', {}).get('total_files', 0)}
- **Maximum Depth:** {tree_data.get('statistics', {}).get('max_depth', 0)}

### Status Distribution

| Status Code | Count |
|------------|-------|
{self._format_status_table_md(tree_data.get('statistics', {}).get('by_status', {}))}

### Directory Structure

```
{tree_data.get('visualization', '')}
```

### Legend

- 📁 Directory
- 📄 File
- 🟢 200 OK
- 🟡 301/302 Redirect
- 🔴 403 Forbidden
- 🔒 401 Unauthorized
- ⚫ 404 Not Found
"""
    
    def _format_status_table_md(self, status_dict: Dict[str, int]) -> str:
        """Format status distribution for markdown table"""
        rows = []
        for status, count in sorted(status_dict.items()):
            rows.append(f"| {status} | {count} |")
        return '\n'.join(rows) if rows else '| No data | 0 |'
    
    def _generate_scan_summary_md(self, scan_data: Dict[str, Any]) -> str:
        """Generate scan summary for Markdown"""
        duration = scan_data.get('duration', 0)
        results = scan_data.get('scan_results', [])
        
        # Count by status
        status_counts = {}
        for result in results:
            status = result.get('status', 0)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return f"""
- **Total Findings:** {len(results)}
- **Scan Duration:** {duration:.1f} seconds
- **200 OK:** {status_counts.get(200, 0)}
- **301/302 Redirects:** {status_counts.get(301, 0) + status_counts.get(302, 0)}
- **403 Forbidden:** {status_counts.get(403, 0)}
- **401 Unauthorized:** {status_counts.get(401, 0)}
"""