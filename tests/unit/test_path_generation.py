#!/usr/bin/env python3
"""
Simple test to check path generation and URL construction
"""

from urllib.parse import urljoin

def test_url_construction():
    """Test how URLs are constructed"""
    print("Testing URL construction with urljoin\n")
    
    base_urls = [
        "http://challenge01.root-me.org/web-serveur/ch4/",
        "http://challenge01.root-me.org/web-serveur/ch4",  # without trailing slash
        "http://example.com/",
        "http://example.com"
    ]
    
    paths = [
        "admin",
        "/admin",
        "admin/",
        "/admin/",
        "admin.php",
        "/admin.php"
    ]
    
    for base_url in base_urls:
        print(f"\nBase URL: {base_url}")
        print("-" * 50)
        for path in paths:
            result = urljoin(base_url, path)
            print(f"  {path:15} -> {result}")

def test_wordlist_check():
    """Check if admin is in wordlist"""
    print("\n\nChecking wordlist content\n")
    
    wordlist_path = "wordlists/common.txt"
    try:
        with open(wordlist_path, 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        
        print(f"Total words in {wordlist_path}: {len(words)}")
        
        # Check for admin variations
        admin_words = [w for w in words if 'admin' in w.lower()]
        print(f"\nWords containing 'admin': {len(admin_words)}")
        for word in admin_words[:10]:
            print(f"  - {word}")
        
        # Check if exact 'admin' exists
        if 'admin' in words:
            print(f"\n✅ Exact word 'admin' found at position {words.index('admin')}")
        else:
            print("\n❌ Exact word 'admin' NOT found")
            
    except FileNotFoundError:
        print(f"❌ Wordlist not found: {wordlist_path}")

def simulate_path_generation():
    """Simulate the engine's path generation"""
    print("\n\nSimulating path generation\n")
    
    words = ['admin', 'login', 'config']
    extensions = ['php', 'html', 'txt']
    
    print("Input:")
    print(f"  Words: {words}")
    print(f"  Extensions: {extensions}")
    print("\nGenerated paths:")
    
    paths = set()
    for word in words:
        # Add base word
        paths.add(word)
        
        # Add with extensions
        for ext in extensions:
            paths.add(f"{word}.{ext}")
    
    for path in sorted(paths):
        print(f"  - {path}")

if __name__ == "__main__":
    test_url_construction()
    test_wordlist_check()
    simulate_path_generation()