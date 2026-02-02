#!/bin/bash
# Wrapper for installation
# Usage: bash auto_install.sh

echo " Preparing Installation..."

# 1. Fix Windows line endings in the setup script (common issue)
if [ -f "install/setup.sh" ]; then
    sed -i 's/\r$//' install/setup.sh
else
    echo "Error: install/setup.sh not found!"
    exit 1
fi

# 2. Make it executable
chmod +x install/setup.sh

# 3. Run it
./install/setup.sh
