#!/usr/bin/env bash

# =========================================================
#  LUMINA XTREAM SERVER - PROXMOX INSTALLER
#  Based on Proxmox VE Helper-Scripts Styles
# =========================================================

YW=$(echo "\033[33m")
BL=$(echo "\033[36m")
RD=$(echo "\033[01;31m")
BGN=$(echo "\033[4;92m")
GN=$(echo "\033[1;92m")
DGN=$(echo "\033[32m")
CL=$(echo "\033[m")
BFR="\\r\\033[K"
HOLD="-"
CM="${GN}✓${CL}"
CROSS="${RD}✗${CL}"

function msg_info() {
    local msg="$1"
    echo -ne " ${HOLD} ${YW}${msg}..."
}

function msg_ok() {
    local msg="$1"
    echo -e "${BFR} ${CM} ${GN}${msg}${CL}"
}

function msg_error() {
    local msg="$1"
    echo -e "${BFR} ${CROSS} ${RD}${msg}${CL}"
}

if [ `id -u` -ne 0 ]; then
    msg_error "This script must be run as root"
    exit 1
fi

clear
echo -e "${BL}Lumina Xtream Server Auto-Installer${CL}"
echo -e "This script will create a Debian LXC Container and install Lumina.\n"

# --- 1. CONFIGURATION ---
NEXTID=$(pvesh get /cluster/nextid)
read -p "Container ID [$NEXTID]: " CT_ID
CT_ID=${CT_ID:-$NEXTID}

HOSTNAME="lumina-server"
read -p "Hostname [$HOSTNAME]: " INPUT_HOST
HOSTNAME=${INPUT_HOST:-$HOSTNAME}

DISK_SIZE="10"
read -p "Disk Size GB [$DISK_SIZE]: " INPUT_DISK
DISK_SIZE=${INPUT_DISK:-$DISK_SIZE}

CORES="2"
read -p "Allocated Cores [$CORES]: " INPUT_CORES
CORES=${INPUT_CORES:-$CORES}

RAM="2048"
read -p "Allocated RAM MB [$RAM]: " INPUT_RAM
RAM=${INPUT_RAM:-$RAM}

PASSWORD="lumina" # Default password for the container

# Auto-detect storage
STORAGE_TYPE=$(pvesm status -content rootdir | awk 'NR>1 {print $1}' | head -n 1)
if [ -z "$STORAGE_TYPE" ]; then STORAGE_TYPE="local-lvm"; fi
msg_info "Selected Storage: $STORAGE_TYPE"
echo ""

read -p "Proceed with installation? [y/N] " PROCEED
if [[ ! "$PROCEED" =~ ^[yY]$ ]]; then
    msg_error "Aborted by user."
    exit 0
fi

# --- 2. TEMPLATE ---
msg_info "Updating Template List"
pveam update >/dev/null 2>&1
msg_ok "Template List Updated"

TEMPLATE="debian-12-standard"
msg_info "Searching for $TEMPLATE"
TEMPLATE_VOL=$(pveam list local | grep "$TEMPLATE" | sort -r | head -n 1 | awk '{print $1}')

if [ -z "$TEMPLATE_VOL" ]; then
    msg_info "Downloading Debian 12 Template..."
    # Attempt download of latest standard debian 12
    pveam download local debian-12-standard_12.7-1_amd64.tar.zst >/dev/null 2>&1 || pveam download local debian-12-standard_12.2-1_amd64.tar.zst >/dev/null 2>&1
    
    TEMPLATE_VOL=$(pveam list local | grep "$TEMPLATE" | sort -r | head -n 1 | awk '{print $1}')
    if [ -z "$TEMPLATE_VOL" ]; then
        msg_error "Could not find or download Debian 12 template."
        exit 1
    fi
fi
msg_ok "Using Template: $TEMPLATE_VOL"

# --- 3. CREATE CONTAINER ---
msg_info "Creating LXC Container (ID: $CT_ID)"
pct create $CT_ID $TEMPLATE_VOL \
    --hostname $HOSTNAME \
    --cores $CORES \
    --memory $RAM \
    --swap 512 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --rootfs $STORAGE_TYPE:${DISK_SIZE}G \
    --storage $STORAGE_TYPE \
    --password $PASSWORD \
    --features nesting=1 \
    --unprivileged 1 \
    --onboot 1 >/dev/null 2>&1
msg_ok "LXC Container Created"

# --- 4. START & INSTALL ---
msg_info "Starting Container..."
pct start $CT_ID
msg_ok "Container Started"

msg_info "Waiting for Network..."
sleep 8
msg_ok "Network Ready"

msg_info "Installing Lumina Server (This may take 1-2 minutes)..."
pct exec $CT_ID -- bash -c "apt-get update -qq && apt-get install -y curl git -qq && curl -sL https://raw.githubusercontent.com/sonics007/Lumina/main/deploy.sh | bash" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    msg_ok "Lumina Installed Successfully"
else
    msg_error "Lumina Installation Failed"
    echo "Check logs inside container."
fi

# --- 5. SUMMARY ---
IP=$(pct exec $CT_ID -- hostname -I | awk '{print $1}')

echo -e "\n${GN}=================================================${CL}"
echo -e "${GN} INSTALLATION COMPLETE! ${CL}"
echo -e "${GN}=================================================${CL}"
echo -e "Lumina Dashboard: ${BL}http://${IP}:5001${CL}"
echo -e "Container ID:     ${BL}$CT_ID${CL}"
echo -e "SSH Root Pass:    ${BL}$PASSWORD${CL}"
echo -e "${GN}=================================================${CL}"
