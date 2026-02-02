#!/usr/bin/env bash

# =========================================================
#  LUMINA XTREAM SERVER - PROXMOX INSTALLER v2 (Debug)
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

# Network Configuration
read -p "VLAN Tag (Optional, press Enter for none): " INPUT_VLAN
VLAN_OPT=""
if [ -n "$INPUT_VLAN" ]; then VLAN_OPT=",tag=$INPUT_VLAN"; fi

read -p "Use DHCP? [y/N]: " USE_DHCP
if [[ "$USE_DHCP" =~ ^[yY]$ ]]; then
    NET_CONFIG="name=eth0,bridge=vmbr0,ip=dhcp${VLAN_OPT}"
else
    read -p "IP Address (CIDR, e.g. 192.168.1.100/24): " INPUT_IP
    read -p "Gateway (e.g. 192.168.1.1): " INPUT_GW
    NET_CONFIG="name=eth0,bridge=vmbr0,ip=$INPUT_IP,gw=$INPUT_GW${VLAN_OPT}"
fi

PASSWORD="lumina" 

# Check storage
STORAGE_TYPE=$(pvesm status -content rootdir | awk 'NR>1 {print $1}' | head -n 1)
if [ -z "$STORAGE_TYPE" ]; then STORAGE_TYPE="local-lvm"; fi
echo -e "${YW}Selected Storage: ${STORAGE_TYPE}${CL}"

read -p "Proceed with installation? [y/N] " PROCEED
if [[ ! "$PROCEED" =~ ^[yY]$ ]]; then
    msg_error "Aborted by user."
    exit 0
fi

# --- 2. TEMPLATE ---
msg_info "Checking Template"
pveam update >/dev/null 2>&1
TEMPLATE="debian-12-standard"
TEMPLATE_VOL=$(pveam list local | grep "$TEMPLATE" | sort -r | head -n 1 | awk '{print $1}')

if [ -z "$TEMPLATE_VOL" ]; then
    msg_info "Downloading Debian 12 Template..."
    pveam download local debian-12-standard_12.7-1_amd64.tar.zst || pveam download local debian-12-standard_12.2-1_amd64.tar.zst
    TEMPLATE_VOL=$(pveam list local | grep "$TEMPLATE" | sort -r | head -n 1 | awk '{print $1}')
fi

if [ -z "$TEMPLATE_VOL" ]; then
    msg_error "Template NOT found. Please download Debian 12 template manually to 'local' storage."
    exit 1
fi
msg_ok "Using Template: $TEMPLATE_VOL"

# --- 3. CREATE CONTAINER ---
echo -e "${YW}Creating LXC Container (ID: $CT_ID)...${CL}"

# Execute without silencing output to see errors
pct create $CT_ID $TEMPLATE_VOL \
    --hostname $HOSTNAME \
    --cores $CORES \
    --memory $RAM \
    --swap 512 \
    --net0 $NET_CONFIG \
    --rootfs $STORAGE_TYPE:${DISK_SIZE} \
    --storage $STORAGE_TYPE \
    --password $PASSWORD \
    --features nesting=1 \
    --unprivileged 1 \
    --onboot 1

if [ $? -ne 0 ]; then
    echo ""
    msg_error "Container Creation FAILED. See error messsage above."
    exit 1
fi
msg_ok "LXC Container Created"

# --- 4. START & INSTALL ---
msg_info "Starting Container..."
pct start $CT_ID
if [ $? -ne 0 ]; then
    msg_error "Failed to start container $CT_ID"
    exit 1
fi
msg_ok "Container Started"

msg_info "Waiting for Network (10s)..."
sleep 10
msg_ok "Network Check"

msg_info "Installing Lumina Server..."
pct exec $CT_ID -- bash -c "apt-get update -qq && apt-get install -y curl git -qq && curl -sL https://raw.githubusercontent.com/sonics007/Lumina/main/deploy.sh | bash"

if [ $? -eq 0 ]; then
    IP=$(pct exec $CT_ID -- hostname -I | awk '{print $1}')
    echo -e "\n${GN}=================================================${CL}"
    echo -e "${GN} INSTALLATION COMPLETE! ${CL}"
    echo -e "Lumina Dashboard: ${BL}http://${IP}:5001${CL}"
    echo -e "Container ID:     ${BL}$CT_ID${CL}"
    echo -e "SSH Login:        ${BL}root${CL}"
    echo -e "SSH Password:     ${BL}$PASSWORD${CL}"
    echo -e "${GN}=================================================${CL}"
else
    msg_error "Lumina Installation Failed inside container."
fi
