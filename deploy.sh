#!/bin/bash

# ==========================================
#  LUMINA ONE-COMMAND DEPLOYMENT
#  Usage: curl -sL https://raw.githubusercontent.com/sonics007/Lumina/main/deploy.sh | bash
# ==========================================

REPO_URL="https://github.com/sonics007/Lumina.git"
INSTALL_DIR="/opt/lumina"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)"
  exit 1
fi

echo ">>> Starting Lumina Deployment..."

# 1. Install Git if missing
command -v git >/dev/null 2>&1 || { 
    echo "Installing git..."
    apt-get update -qq
    apt-get install -y git -qq
}

# 2. Clone or Update Repository
if [ -d "$INSTALL_DIR" ]; then
  echo "Updating existing installation at $INSTALL_DIR..."
  cd "$INSTALL_DIR"
  
  # Reset local changes to force update from remote
  git fetch --all
  git reset --hard origin/main || git reset --hard origin/master
  git pull
else
  echo "Cloning repository to $INSTALL_DIR..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# 3. Run Auto Installer
if [ -f "auto_install.sh" ]; then
    echo "Executing installer..."
    bash auto_install.sh
else
    echo "Error: auto_install.sh not found in the repository!"
    exit 1
fi
