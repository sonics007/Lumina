#!/bin/bash

# Lumina Installer for Debian/Ubuntu
# Run this script as root (sudo ./install/setup.sh)

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

APP_DIR=$(pwd)
CURRENT_USER=${SUDO_USER:-root}

echo "============================================="
echo " Lumina Installer "
echo "============================================="
echo "Installation Directory: $APP_DIR"
echo "Running User: $CURRENT_USER"
echo ""

# 1. Install System Dependencies
echo "[1/4] Installing System Dependencies (apt)..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv python3-full ffmpeg git curl -qq

# 2. Create Virtual Environment
echo "[2/4] Creating Python Virtual Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    # Fix permissions if created as root but meant for user
    chown -R $CURRENT_USER:$CURRENT_USER .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# 3. Install Python Packages
echo "[3/4] Installing Python Packages..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r install/requirements.txt -q
echo "Packages installed."

# 3.1 Initialize Database
echo "Initializing Database tables..."
python3 -c "from server import app; from app.models import db; app.app_context().push(); db.create_all()"


# 4. Setup Systemd Service
echo "[4/4] Configuring Systemd Service..."
SERVICE_TEMPLATE="install/lumina.service"
TARGET_SERVICE="/etc/systemd/system/lumina.service"

if [ -f "$SERVICE_TEMPLATE" ]; then
    cp $SERVICE_TEMPLATE $TARGET_SERVICE

    # Update paths and user in service file
    sed -i "s|WorkingDirectory=/opt/lumina|WorkingDirectory=$APP_DIR|g" $TARGET_SERVICE
    sed -i "s|ExecStart=/opt/lumina/.venv/bin/gunicorn|ExecStart=$APP_DIR/.venv/bin/gunicorn|g" $TARGET_SERVICE
    sed -i "s|User=root|User=$CURRENT_USER|g" $TARGET_SERVICE

    # Reload Daemon & Start
    systemctl daemon-reload
    systemctl enable lumina
    systemctl restart lumina

    echo "============================================="
    echo " INSTALLATION COMPLETE "
    echo "============================================="
    echo "Service Status:"
    systemctl status lumina --no-pager | head -n 10
    echo ""
    IP_ADDR=$(hostname -I | awk '{print $1}')
    echo "Access the dashboard at: http://$IP_ADDR:5001"
    echo "============================================="
else
    echo "Error: Service template not found at $SERVICE_TEMPLATE"
fi
