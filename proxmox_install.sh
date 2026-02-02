#!/bin/bash

# ==========================================
#  LUMINA PROXMOX LXC INSTALLER
#  Run this script on your Proxmox VE Host
# ==========================================

set -e

echo "┌──────────────────────────────────────────┐"
echo "│      Lumina Xtream Server Installer      │"
echo "└──────────────────────────────────────────┘"

# --- 1. CONFIGURATION ---
NEXT_ID=$(pvesh get /cluster/nextid)
read -p "Enter Container ID [$NEXT_ID]: " CT_ID
CT_ID=${CT_ID:-$NEXT_ID}

HOSTNAME="lumina-server"
PASSWORD="lumina"  # Default password
MEMORY=2048
CORES=2
DISK_SIZE="10G"

# Auto-detect storage for rootfs (local-lvm, local-zfs, or local)
STORAGE=$(pvesm status -content rootdir | grep active | head -n 1 | awk '{print $1}')
echo "-> Target Storage: $STORAGE"

# --- 2. TEMPLATE SETUP ---
echo "-> Checking Debian 12 Template..."
# Basic check for existing template
TEMPLATE_VOLID=$(pveam list local | grep "debian-12-standard" | sort -r | head -n 1 | awk '{print $1}')

if [ -z "$TEMPLATE_VOLID" ]; then
    echo "   Template not found. Updating list and downloading..."
    pveam update
    # Try generic debian-12 download
    pveam download local debian-12-standard_12.2-1_amd64.tar.zst || echo "Attempting manual download..."
    
    # Check again
    TEMPLATE_VOLID=$(pveam list local | grep "debian-12-standard" | sort -r | head -n 1 | awk '{print $1}')
    
    if [ -z "$TEMPLATE_VOLID" ]; then
        echo "ERROR: Could not find or download Debian 12 template."
        exit 1
    fi
fi
echo "   Using Template: $TEMPLATE_VOLID"

# --- 3. CREATE CONTAINER ---
echo "-> Creating LXC Container $CT_ID..."
pct create $CT_ID $TEMPLATE_VOLID \
    --hostname $HOSTNAME \
    --password $PASSWORD \
    --cores $CORES \
    --memory $MEMORY \
    --swap 512 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --rootfs $STORAGE:$DISK_SIZE \
    --onboot 1 \
    --features nesting=1 \
    --unprivileged 1

# --- 4. START & INSTALL ---
echo "-> Starting Container..."
pct start $CT_ID

echo "-> Waiting for network (10s)..."
sleep 10

echo "-> Installing Dependencies & Lumina inside CT..."
# Run the installation inside the container
pct exec $CT_ID -- bash -c "apt-get update && apt-get install -y curl && curl -sL https://raw.githubusercontent.com/sonics007/Lumina/main/deploy.sh | bash"

# --- 5. FINISH ---
IP=$(pct exec $CT_ID -- hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo " ✅ INSTALLATION SUCCESSFUL"
echo "=========================================="
echo " Web Interface: http://$IP:5001"
echo " Container ID:  $CT_ID"
echo " Root Password: $PASSWORD"
echo "=========================================="
