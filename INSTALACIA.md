# Inštalácia Lumina na Debian/Ubuntu

## 1. Rýchla Inštalácia (Odporúčané)
Pripojte sa na server ako **root** a spustite tento príkaz:

```bash
curl -sL https://raw.githubusercontent.com/sonics007/Lumina/main/deploy.sh | bash
```

Tento príkaz automaticky:
*   Stiahne najnovšiu verziu aplikácie do `/opt/lumina`.
*   Nainštaluje Python, FFmpeg a všetky potrebné knižnice.
*   Nastaví službu `lumina`, ktorá sa spustí automaticky po reštarte.

Po inštalácii bude aplikácia dostupná na: `http://IP-VASHO-SERVERA:5001`.

---

## 2. Manuálna Inštalácia
Ak chcete inštalovať ručne:

1.  Stiahnite kód:
    ```bash
    git clone https://github.com/sonics007/Lumina.git /opt/lumina
    cd /opt/lumina
    ```

2.  Spustite inštalačný skript:
    ```bash
    bash auto_install.sh
    ```

## Správa Služby
*   **Štart:** `systemctl start lumina`
*   **Stop:** `systemctl stop lumina`
*   **Reštart:** `systemctl restart lumina`
*   **Zobraziť Logy:** `journalctl -u lumina -f`
