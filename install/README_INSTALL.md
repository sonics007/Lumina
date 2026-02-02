# Lumina Installation Guide

## Prepare
1. Upload the project files to your server (e.g. `/root/lumina` or `/opt/lumina`).

## Install
Run the following commands as **root**:

```bash
cd lumina
chmod +x install/setup.sh
./install/setup.sh
```

**Troubleshooting:**
If you see an error like `/bin/bash^M: bad interpreter`, it means the file has Windows line endings. Fix it by running:
```bash
sed -i 's/\r$//' install/setup.sh
./install/setup.sh
```

## Manage Service
- **Status:** `systemctl status lumina`
- **Restart:** `systemctl restart lumina`
- **Logs:** `journalctl -u lumina -f`

## Access
Open browser at `http://YOUR_SERVER_IP:5001`
