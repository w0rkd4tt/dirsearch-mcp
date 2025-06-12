import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import html
from dataclasses import asdict
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns


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
        
        # Structure the report
        report = {
            'metadata': {
                'report_version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'generator': 'DirsearchMCP'
            },
            'scan_info': {
                'target_url': clean_data.get('target_url', ''),
                'target_domain': clean_data.get('target_domain', ''),
                'start_time': clean_data.get('start_time', ''),
                'end_time': clean_data.get('end_time', ''),
                'duration': clean_data.get('duration', 0),
                'intelligence_mode': clean_data.get('intelligence_mode', 'LOCAL')
            },
            'target_analysis': clean_data.get('target_analysis', {}),
            'mcp_decisions': clean_data.get('mcp_decisions', []),
            'scan_plan': clean_data.get('scan_plan', []),
            'scan_results': clean_data.get('scan_results', []),
            'findings_summary': self._generate_findings_summary(clean_data),
            'performance_metrics': clean_data.get('performance_metrics', {}),
            'recommendations': self._generate_recommendations(clean_data)
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
            <h1>Dirsearch MCP Scan Report</h1>
            <div class="metadata">
                <span>Target: <strong>{html.escape(scan_data.get('target_url', ''))}</strong></span>
                <span>Generated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></span>
                <span>Mode: <strong>{scan_data.get('intelligence_mode', 'LOCAL')}</strong></span>
            </div>
        </header>
        
        {self._generate_executive_summary_html(scan_data)}
        {self._generate_target_analysis_html(scan_data)}
        {self._generate_mcp_decisions_html(scan_data)}
        {self._generate_findings_html(scan_data, charts)}
        {self._generate_performance_html(scan_data, charts)}
        {self._generate_recommendations_html(scan_data)}
        
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
        
        md_content = f"""# Dirsearch MCP Scan Report

**Target:** {scan_data.get('target_url', 'Unknown')}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Intelligence Mode:** {scan_data.get('intelligence_mode', 'LOCAL')}

---

## Executive Summary

{self._generate_executive_summary_md(scan_data)}

## Target Analysis

{self._generate_target_analysis_md(scan_data)}

## MCP Coordination Decisions

{self._generate_mcp_decisions_md(scan_data)}

## Scan Results

{self._generate_findings_md(scan_data)}

## Performance Metrics

{self._generate_performance_md(scan_data)}

## Recommendations

{self._generate_recommendations_md(scan_data)}

---

*Generated by Dirsearch MCP - Intelligent Directory Scanner with AI Integration*
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
        results = scan_data.get('scan_results', [])
        all_findings = []
        
        for result in results:
            all_findings.extend(result.get('findings', []))
        
        # Group by status code
        status_groups = {}
        for finding in all_findings:
            status = finding.get('status', 0)
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(finding)
        
        return {
            'total_findings': len(all_findings),
            'by_status': {str(k): len(v) for k, v in status_groups.items()},
            'interesting_paths': [f for f in all_findings if f.get('status') in [200, 301, 302, 401, 403]],
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
        }
        
        .metadata {
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.9;
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
            findings_rows += f"""
            <tr>
                <td>{html.escape(finding.get('path', ''))}</td>
                <td class="{status_class}">{finding.get('status', '')}</td>
                <td>{finding.get('size', 0)}</td>
                <td>{html.escape(finding.get('task_id', ''))}</td>
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
                <button class="tab active" data-tab="findings-tab">Interesting Findings</button>
                <button class="tab" data-tab="vulnerabilities-tab">Potential Vulnerabilities</button>
            </div>
            
            <div id="findings-tab" class="tab-content active">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Path</th>
                            <th>Status</th>
                            <th>Size</th>
                            <th>Task</th>
                        </tr>
                    </thead>
                    <tbody>
                        {findings_rows}
                    </tbody>
                </table>
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
                <strong>[{rec['priority']}] {html.escape(rec['category'])}:</strong> {html.escape(rec['recommendation'])}
                <br>
                <small>{html.escape(rec['details'])}</small>
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

{findings_table}

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