import os
import sys

# Get paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
check_script = os.path.join(parent_dir, 'check_bahu_completeness.py')

print(f"--- Starting Bahu Completeness Check ---\n")
print(f"Running: {check_script}")
print("-" * 40)

# Run the check script (it handles path insertion and logging internally)
# We use system call to ensure it runs in the proper environment/cwd context if needed.
exit_code = os.system(f"{sys.executable} {check_script}")

print("-" * 40)
if exit_code == 0:
    print(f"Check finished. Log saved to: {os.path.join(current_dir, 'completeness_last_check.txt')}")
else:
    print("Check failed.")
