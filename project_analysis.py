#!/usr/bin/env python3
"""
Project Statistics and Structure Report
Generated for Telegram Bot Integration Project
"""

import os
import json
from pathlib import Path
from datetime import datetime

def get_file_stats(filepath):
    """Get statistics for a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        return {
            'size_bytes': os.path.getsize(filepath),
            'lines': len(lines),
            'type': Path(filepath).suffix
        }
    except:
        return None

def analyze_project(root_path):
    """Analyze project structure"""
    stats = {
        'generated_at': datetime.now().isoformat(),
        'root': root_path,
        'files': {},
        'summary': {
            'total_files': 0,
            'total_lines': 0,
            'total_size_kb': 0,
            'python_files': 0,
            'documentation_files': 0,
            'config_files': 0
        },
        'categories': {
            'core': [],
            'integration': [],
            'examples': [],
            'documentation': [],
            'configuration': [],
            'testing': []
        }
    }
    
    # Define file categories
    categorization = {
        'telegram_sender.py': 'core',
        'telegram_integration.py': 'integration',
        'zalo_integration.py': 'integration',
        'models.py': 'core',
        'webhooks.py': 'integration',
        'main.py': 'configuration',
        'telegram_sender_example.py': 'examples',
        'test_telegram_sender.py': 'testing',
        'requirements.txt': 'configuration',
        '.env.example': 'configuration',
        '.gitignore': 'configuration',
        'README.md': 'documentation',
        'TELEGRAM_SENDER_README.md': 'documentation',
        'IMPLEMENTATION_SUMMARY.md': 'documentation',
        'send.ts': 'examples',
    }
    
    # Scan directory
    for filename in os.listdir(root_path):
        filepath = os.path.join(root_path, filename)
        
        if os.path.isfile(filepath):
            file_stats = get_file_stats(filepath)
            if file_stats:
                stats['files'][filename] = file_stats
                stats['summary']['total_files'] += 1
                stats['summary']['total_lines'] += file_stats['lines']
                stats['summary']['total_size_kb'] += file_stats['size_bytes'] / 1024
                
                # Count by type
                if file_stats['type'] == '.py':
                    stats['summary']['python_files'] += 1
                if file_stats['type'] in ['.md', '.markdown']:
                    stats['summary']['documentation_files'] += 1
                if filename in ['.env', '.env.example', '.gitignore', 'requirements.txt']:
                    stats['summary']['config_files'] += 1
                
                # Categorize
                category = categorization.get(filename, 'other')
                if category in stats['categories']:
                    stats['categories'][category].append({
                        'name': filename,
                        'lines': file_stats['lines'],
                        'size_kb': round(file_stats['size_bytes'] / 1024, 2)
                    })
    
    return stats

def print_report(stats):
    """Print formatted report"""
    print("\n" + "="*70)
    print("TELEGRAM BOT INTEGRATION PROJECT - STRUCTURE & STATISTICS")
    print("="*70 + "\n")
    
    print(f"Generated: {stats['generated_at']}")
    print(f"Project Root: {stats['root']}\n")
    
    # Summary
    print("📊 SUMMARY")
    print("-" * 70)
    print(f"  Total Files:        {stats['summary']['total_files']}")
    print(f"  Python Files:       {stats['summary']['python_files']}")
    print(f"  Documentation:      {stats['summary']['documentation_files']}")
    print(f"  Configuration:      {stats['summary']['config_files']}")
    print(f"  Total Lines:        {stats['summary']['total_lines']:,}")
    print(f"  Total Size:         {stats['summary']['total_size_kb']:.2f} KB\n")
    
    # Categories
    print("📁 ORGANIZED BY CATEGORY")
    print("-" * 70)
    
    for category, files in stats['categories'].items():
        if not files:
            continue
        print(f"\n  {category.upper()} ({len(files)} files)")
        for file_info in files:
            print(f"    ✓ {file_info['name']:<30} | {file_info['lines']:>5} lines | {file_info['size_kb']:>6.1f} KB")
    
    # Python Files
    print("\n\n🐍 PYTHON FILES")
    print("-" * 70)
    python_files = [f for f in stats['files'] if f.endswith('.py')]
    for py_file in sorted(python_files):
        file_info = stats['files'][py_file]
        print(f"  {py_file:<35} | {file_info['lines']:>5} lines | {file_info['size_bytes']:>7} bytes")
    
    # Documentation Files
    print("\n\n📚 DOCUMENTATION")
    print("-" * 70)
    doc_files = [f for f in stats['files'] if f.endswith(('.md', '.txt')) and 'example' not in f]
    for doc_file in sorted(doc_files):
        file_info = stats['files'][doc_file]
        print(f"  {doc_file:<35} | {file_info['lines']:>5} lines | {file_info['size_bytes']:>7} bytes")
    
    print("\n" + "="*70)
    print("✅ PROJECT IMPLEMENTATION COMPLETE")
    print("="*70 + "\n")

def main():
    """Main entry point"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    stats = analyze_project(project_root)
    print_report(stats)
    
    # Save JSON report
    report_file = os.path.join(project_root, 'project_stats.json')
    with open(report_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"📄 Detailed report saved to: {report_file}\n")

if __name__ == "__main__":
    main()
