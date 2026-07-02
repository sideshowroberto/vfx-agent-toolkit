#!/usr/bin/env python3
"""Batch validate all VFX skills and generate summary report."""

import os
import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    # Find all skills
    skills_dir = Path(__file__).parent.parent.parent
    skills = []
    
    for item in skills_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skills.append(item.name)
    
    skills.sort()
    
    print(f"\nFound {len(skills)} skills to validate\n")
    print("=" * 80)
    
    results = {}
    
    for skill in skills:
        print(f"\nValidating: {skill}")
        
        try:
            # Run validation with UTF-8 encoding
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "validate_skill.py"), skill],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )

            # Extract overall result
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if 'Overall:' in line:
                        if 'PASS' in line:
                            results[skill] = 'PASS'
                            print(f"  PASS")
                        else:
                            results[skill] = 'FAIL'
                            print(f"  FAIL")
                        break
                else:
                    results[skill] = 'ERROR'
                    print(f"  ERROR (no validation result)")
            else:
                results[skill] = 'ERROR'
                print(f"  ERROR (no output)")
                
        except Exception as e:
            results[skill] = 'ERROR'
            print(f"  ERROR: {e}")

    print("\n" + "=" * 80)
    print("\nSUMMARY:")
    print(f"Total skills: {len(skills)}")
    print(f"PASS: {sum(1 for v in results.values() if v == 'PASS')}")
    print(f"FAIL: {sum(1 for v in results.values() if v == 'FAIL')}")
    print(f"ERROR: {sum(1 for v in results.values() if v == 'ERROR')}")
    
    print("\nFailed skills:")
    for skill, result in results.items():
        if result == 'FAIL':
            print(f"  - {skill}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
