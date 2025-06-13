#!/usr/bin/env python3
"""Test and demonstrate the Intelligent Scanner functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.intelligent_scanner import IntelligentScanner, EndpointRule
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def test_intelligent_scanner():
    """Test the intelligent scanner with various paths"""
    scanner = IntelligentScanner()
    
    console.print("\n[bold cyan]🧠 Intelligent Scanner Test[/bold cyan]")
    console.print("="*60)
    
    # Test paths
    test_paths = [
        ('/admin/login', 200),
        ('/api/v2/users', 200),
        ('/backup/db.sql', 200),
        ('/.git/config', 200),
        ('/wp-admin/', 301),
        ('/phpmyadmin/', 403),
        ('/api/swagger.json', 200),
        ('/old/site.zip', 200),
        ('/vendor/composer.json', 200),
        ('/graphql', 200),
        ('/config/.env', 200),
        ('/uploads/shell.php', 200),
        ('/monitor/health', 200),
        ('/login/auth', 200),
        ('/dev/debug.log', 200)
    ]
    
    # Test each path
    results = []
    for path, status in test_paths:
        rules = scanner.analyze_path(path, status)
        keywords = scanner.get_expansion_keywords(path)
        should_deep = scanner.should_deep_scan(path)
        extensions = scanner.get_smart_extensions(path)
        
        results.append({
            'path': path,
            'status': status,
            'rules': rules,
            'keywords': keywords,
            'deep_scan': should_deep,
            'extensions': extensions
        })
    
    # Display results
    result_table = Table(title="[bold]Path Analysis Results[/bold]", show_header=True)
    result_table.add_column("Path", style="cyan")
    result_table.add_column("Priority", style="yellow")
    result_table.add_column("Rule", style="green")
    result_table.add_column("Deep Scan", style="red")
    
    for result in results:
        path = result['path']
        rules = result['rules']
        priority = rules[0][1].priority if rules else 0
        rule_name = rules[0][0] if rules else "None"
        deep_scan = "✓" if result['deep_scan'] else "✗"
        
        result_table.add_row(path, str(priority), rule_name, deep_scan)
    
    console.print(result_table)
    
    # Show rule distribution
    console.print("\n[bold cyan]Rule Coverage:[/bold cyan]")
    rule_tree = Tree("📋 Intelligent Rules")
    
    rule_categories = {
        'Critical (80+)': [],
        'High (70-79)': [],
        'Medium (60-69)': [],
        'Low (<60)': []
    }
    
    for name, rule in scanner.rules.items():
        if rule.priority >= 80:
            rule_categories['Critical (80+)'].append((name, rule))
        elif rule.priority >= 70:
            rule_categories['High (70-79)'].append((name, rule))
        elif rule.priority >= 60:
            rule_categories['Medium (60-69)'].append((name, rule))
        else:
            rule_categories['Low (<60)'].append((name, rule))
    
    for category, rules in rule_categories.items():
        if rules:
            cat_branch = rule_tree.add(f"[bold]{category}[/bold]")
            for name, rule in rules:
                cat_branch.add(f"{name}: {rule.description} (Priority: {rule.priority})")
    
    console.print(rule_tree)
    
    # Test scan strategy generation
    console.print("\n[bold cyan]Scan Strategy Generation:[/bold cyan]")
    
    discovered_paths = [
        {'path': '/admin/login', 'status': 200},
        {'path': '/api/v1/', 'status': 200},
        {'path': '/.git/', 'status': 403},
        {'path': '/backup/', 'status': 200}
    ]
    
    strategy = scanner.get_scan_strategy('https://example.com', discovered_paths)
    
    strategy_panel = Panel(
        f"Priority Paths: {len(strategy['priority_paths'])}\n"
        f"Expansion Keywords: {len(strategy['expansion_keywords'])}\n"
        f"Deep Scan Paths: {len(strategy['deep_scan_paths'])}\n"
        f"Recommended Extensions: {', '.join(strategy['recommended_extensions'][:10])}\n"
        f"Custom Wordlists: {', '.join(strategy['custom_wordlists'].keys())}",
        title="🎯 Generated Scan Strategy",
        border_style="green"
    )
    
    console.print(strategy_panel)
    
    # Show expansion keywords for admin path
    console.print("\n[bold cyan]Keyword Expansion Example:[/bold cyan]")
    admin_keywords = scanner.get_expansion_keywords('/admin')
    
    keyword_table = Table(title="Keywords for /admin", show_header=False)
    keyword_table.add_column("Keywords", style="yellow")
    
    # Show first 20 keywords in rows of 5
    for i in range(0, min(20, len(admin_keywords)), 5):
        row = list(admin_keywords)[i:i+5]
        keyword_table.add_row(", ".join(row))
    
    console.print(keyword_table)
    
    if len(admin_keywords) > 20:
        console.print(f"[dim]... and {len(admin_keywords) - 20} more keywords[/dim]")
    
    # Statistics
    console.print("\n[bold cyan]Scanner Statistics:[/bold cyan]")
    total_keywords = sum(len(rule.keywords) for rule in scanner.rules.values())
    total_patterns = len(scanner.rules)
    
    stats_table = Table(show_header=False)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="yellow")
    
    stats_table.add_row("Total Rules", str(total_patterns))
    stats_table.add_row("Total Keywords", f"{total_keywords:,}")
    stats_table.add_row("Critical Rules", str(len([r for r in scanner.rules.values() if r.priority >= 80])))
    stats_table.add_row("Average Keywords/Rule", f"{total_keywords/total_patterns:.1f}")
    
    console.print(stats_table)


if __name__ == "__main__":
    test_intelligent_scanner()
    
    console.print("\n[bold green]✅ Intelligent Scanner is ready for smart discovery![/bold green]")
    console.print("[dim]The scanner will prioritize critical endpoints and expand wordlists dynamically.[/dim]\n")