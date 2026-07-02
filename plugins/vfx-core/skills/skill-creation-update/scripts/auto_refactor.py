#!/usr/bin/env python3
"""
Auto-refactor skills by extracting large sections to reference files.

Strategy:
1. Identify sections >50 lines (good candidates for extraction)
2. Extract to reference/*.md files
3. Replace with pointer in main SKILL.md
4. Update line count
"""

import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_sections(content):
    """Parse SKILL.md and identify large sections."""
    lines = content.split('\n')
    sections = []
    current_section = {
        'name': '',
        'start_line': 0,
        'lines': [],
        'level': 0
    }
    
    for i, line in enumerate(lines, 1):
        # Detect markdown headers
        if line.startswith('#'):
            # Save previous section if it exists
            if current_section['lines']:
                current_section['end_line'] = i - 1
                current_section['line_count'] = len(current_section['lines'])
                sections.append(current_section.copy())
            
            # Start new section
            level = len(line) - len(line.lstrip('#'))
            current_section = {
                'name': line.strip(),
                'start_line': i,
                'lines': [line],
                'level': level
            }
        else:
            current_section['lines'].append(line)
    
    # Don't forget last section
    if current_section['lines']:
        current_section['end_line'] = len(lines)
        current_section['line_count'] = len(current_section['lines'])
        sections.append(current_section)
    
    return sections

def identify_extraction_candidates(sections, min_lines=50):
    """Find sections >min_lines suitable for extraction."""
    candidates = []
    
    for section in sections:
        # Skip top-level sections and very small ones
