#!/bin/bash
# Test all enhanced features

TARGET=${1:-"http://127.0.0.1:8080/"}

echo "======================================"
echo "Testing Enhanced Dirsearch Features"
echo "Target: $TARGET"
echo "======================================"
echo ""

echo "Available tests:"
echo "1. test_recursive_then_depth.py - Main recursive + deep analysis test"
echo "2. test_comparison.py - Compare different scanning approaches"
echo "3. demo_visual_results.py - Visual demonstration"
echo "4. test_enhanced_comprehensive.py - Comprehensive test with full wordlist"
echo "5. test_smart_recursive.py - Smart recursive scanning test"
echo ""

echo "Which test would you like to run? (1-5, or 'all' for all tests):"
read choice

case $choice in
    1)
        echo "Running Recursive + Deep Analysis Test..."
        python test_recursive_then_depth.py "$TARGET"
        ;;
    2)
        echo "Running Comparison Test..."
        python test_comparison.py "$TARGET"
        ;;
    3)
        echo "Running Visual Demo..."
        python demo_visual_results.py "$TARGET"
        ;;
    4)
        echo "Running Comprehensive Test..."
        python test_enhanced_comprehensive.py "$TARGET"
        ;;
    5)
        echo "Running Smart Recursive Test..."
        python test_smart_recursive.py "$TARGET"
        ;;
    all)
        echo "Running all tests..."
        echo ""
        echo "=== Test 1: Recursive + Deep Analysis ==="
        python test_recursive_then_depth.py "$TARGET"
        echo ""
        echo "Press Enter to continue..."
        read
        
        echo "=== Test 2: Comparison ==="
        python test_comparison.py "$TARGET"
        echo ""
        echo "Press Enter to continue..."
        read
        
        echo "=== Test 3: Visual Demo ==="
        python demo_visual_results.py "$TARGET"
        echo ""
        echo "Press Enter to continue..."
        read
        
        echo "=== Test 4: Comprehensive ==="
        python test_enhanced_comprehensive.py "$TARGET"
        echo ""
        echo "Press Enter to continue..."
        read
        
        echo "=== Test 5: Smart Recursive ==="
        python test_smart_recursive.py "$TARGET"
        ;;
    *)
        echo "Invalid choice. Please run again and choose 1-5 or 'all'"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Testing complete!"
echo "======================================