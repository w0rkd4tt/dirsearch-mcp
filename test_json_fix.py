#!/usr/bin/env python3
"""Test script to verify JSON serialization fix"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.reporter import ReportGenerator
from src.core.dirsearch_engine import DynamicContentParser

def test_json_serialization():
    """Test that DynamicContentParser doesn't break JSON serialization"""
    
    # Create a test scan data structure that might contain DynamicContentParser
    parser = DynamicContentParser("content1", "content2")
    
    scan_data = {
        'target_url': 'http://example.com',
        'target_domain': 'example.com',
        'scan_results': [
            {
                'path': '/admin',
                'status': 200,
                'size': 1234,
                'is_directory': True
            }
        ],
        'wildcard_info': {
            'parser': parser,  # This would normally cause JSON serialization to fail
            'detected': True
        },
        'statistics': {
            'total_requests': 100,
            'found_paths': 5
        }
    }
    
    # Test the reporter
    reporter = ReportGenerator()
    
    try:
        # This should not raise an error with our fix
        clean_data = reporter._clean_data_for_json(scan_data)
        
        # Verify it can be JSON serialized
        json_str = json.dumps(clean_data, indent=2)
        print("✅ JSON serialization successful!")
        print("\nCleaned data structure:")
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
        
        # Verify the parser was removed
        if 'wildcard_info' in clean_data and clean_data['wildcard_info'].get('parser') is None:
            print("\n✅ DynamicContentParser was properly cleaned")
        else:
            print("\n❌ DynamicContentParser might not be properly cleaned")
            
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing JSON serialization fix for DynamicContentParser...\n")
    success = test_json_serialization()
    sys.exit(0 if success else 1)