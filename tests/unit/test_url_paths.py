#!/usr/bin/env python3
"""Test URL path handling"""

from urllib.parse import urljoin, urlparse

# Test cases for URL handling
test_cases = [
    # (base_url, path, expected_result)
    ("http://192.168.214.143", "admin", "http://192.168.214.143/admin"),
    ("http://192.168.214.143/", "admin", "http://192.168.214.143/admin"),
    ("http://192.168.214.143/api", "admin", "http://192.168.214.143/admin"),  # This might be wrong!
    ("http://192.168.214.143/api/", "admin", "http://192.168.214.143/api/admin"),
    ("http://192.168.214.143/api", "../admin", "http://192.168.214.143/admin"),
    ("http://192.168.214.143/api/v1", "users", "http://192.168.214.143/api/users"),  # This might be wrong!
    ("http://192.168.214.143/api/v1/", "users", "http://192.168.214.143/api/v1/users"),
]

print("Testing URL path handling with urljoin:\n")
print(f"{'Base URL':<30} {'Path':<15} {'Result':<50} {'Expected':<50} {'OK?':<5}")
print("-" * 150)

for base_url, path, expected in test_cases:
    result = urljoin(base_url, path)
    ok = result == expected
    print(f"{base_url:<30} {path:<15} {result:<50} {expected:<50} {'✓' if ok else '✗'}")

print("\nIssue: When base URL has a path without trailing slash, urljoin replaces the last segment!")
print("Solution: Ensure base URLs end with '/' when they represent directories")

# Test the fix
print("\n\nTesting with proper trailing slashes:")
print(f"{'Base URL':<30} {'Path':<15} {'Result':<50}")
print("-" * 95)

# Fix: Ensure directory URLs end with /
def fix_base_url(url):
    """Ensure directory URLs end with /"""
    parsed = urlparse(url)
    if parsed.path and not parsed.path.endswith('/'):
        # Check if it looks like a directory (no extension)
        last_segment = parsed.path.split('/')[-1]
        if '.' not in last_segment:  # Likely a directory
            return url + '/'
    return url

test_urls = [
    "http://192.168.214.143/api",
    "http://192.168.214.143/api/v1",
    "http://192.168.214.143/api/v1/test.php",  # This is a file, not directory
]

for url in test_urls:
    fixed_url = fix_base_url(url)
    result = urljoin(fixed_url, "admin")
    print(f"{url:<30} {'admin':<15} {result:<50}")