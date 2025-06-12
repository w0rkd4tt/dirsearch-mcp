#!/bin/bash
# Setup wordlists with SecLists integration

echo "Setting up wordlists directory with SecLists..."
echo "=============================================="

# Create wordlists directory if it doesn't exist
mkdir -p wordlists

# Create symlinks to SecLists wordlists
echo "Creating symlinks to SecLists wordlists..."

# Common wordlists
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/common.txt wordlists/common.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/big.txt wordlists/big.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/directory-list-2.3-small.txt wordlists/directory-list-small.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt wordlists/directory-list-medium.txt

# Technology-specific wordlists
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/PHP.fuzz.txt wordlists/php_common.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/apache.txt wordlists/apache.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/nginx.txt wordlists/nginx.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/IIS.fuzz.txt wordlists/iis.txt

# CMS-specific wordlists
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/CMS/wordpress.fuzz.txt wordlists/wordpress.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/CMS/drupal.txt wordlists/drupal.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/CMS/joomla.txt wordlists/joomla.txt

# API wordlists
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/api/api-endpoints.txt wordlists/api_endpoints.txt

# Backup/sensitive files
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/raft-large-files.txt wordlists/sensitive_files.txt
ln -sf /Users/datnlq/SecLists/Discovery/Web-Content/CommonBackdoors-PHP.fuzz.txt wordlists/backdoors.txt

echo ""
echo "✅ Wordlists setup complete!"
echo ""
echo "Available wordlists in ./wordlists/:"
ls -la wordlists/ | grep -E "\.txt" | awk '{print "  - " $9 " -> " $11}'

echo ""
echo "Usage examples:"
echo "  python scan_with_seclists.py https://example.com"
echo "  python scan_with_seclists.py https://example.com -w wordlists/wordpress.txt"
echo "  python scan_with_seclists.py https://example.com -e php,asp,aspx -t 30"