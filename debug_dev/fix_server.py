#!/usr/bin/env python3
"""
Fix server.py syntax error - remove unreachable code after else: return
"""

with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the problematic section (around line 505-537)
# Remove lines 508-532 (unreachable code under else: return)
# Keep line 533-537 but wrap in try

fixed_lines = []
skip_until = 0

for i, line in enumerate(lines, 1):
    if skip_until > 0 and i <= skip_until:
        continue
    
    # Line 505: else:
    # Line 506: return "Fetch Error..."
    # Line 507: (empty)
    # Lines 508-532: unreachable code - DELETE
    # Line 533: except - needs try
    
    if i == 505 and 'else:' in line:
        # Keep else and return, then add proper try block
        fixed_lines.append(line)  # else:
        fixed_lines.append(lines[i])  # return statement (line 506)
        fixed_lines.append('\n')
        # Add try block
        fixed_lines.append('    # Rewrite Logic\n')
        fixed_lines.append('    try:\n')
        # Skip unreachable code (lines 508-532)
        skip_until = 532
        continue
    
    # Line 533: except - change indentation
    if i == 533 and 'except Exception' in line:
        # Already have try above, keep except but check indentation
        fixed_lines.append('    except Exception as e:\n')
        continue
    
    # Lines 534-537: keep as is
    if 534 <= i <= 537:
        fixed_lines.append(line)
        continue
    
    fixed_lines.append(line)

# Write fixed version
with open('server.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Fixed server.py")
print("Removed unreachable code (lines 508-532)")
print("Added try block before except")
