import os
import time
import requests

# Etherscan API-Key sicher aus den GitHub Secrets holen
API_KEY = os.environ.get("ETHERSCAN_API_KEY")

# Beispiel-Wallet (z.B. eine bekannte Whale- oder CEX-Adresse zum Testen)
TARGET_ADDRESS = "0x28C6c06298d514Db089934071355E5743bf21d60" # Binance Hot Wallet als Beispiel
ETHERSCAN_URL = "https://api.etherscan.io/api"

def check_wallet():
    if not API_KEY:
        print("Fehler: ETHERSCAN_API_KEY Secret nicht gefunden!")
        return

    params = {
        "module": "account",
        "action": "balance",
        "address": TARGET_ADDRESS,
        "tag": "latest",
        "apikey": API_KEY
    }

    try:
        response = requests.get(ETHERSCAN_URL, params=params)
        data = response.json()
        
        if data["status"] == "1":
            wei_balance = int(data["result"])
            eth_balance = wei_balance / 10**18
            print(f"[SUCCESS] Aktueller ETH-Kontostand für {TARGET_ADDRESS}: {eth_balance:.4f} ETH")
        else:
            print(f"[API ERROR] {data['message']}: {data['result']}")
            
    except Exception as e:
        print(f"[CONNECTION ERROR] {e}")

if __name__ == "__main__":
    print("Starte On-Chain Abfrage...")
    check_wallet()
    # Einhaltung der Free-Tier Grenzen (max 3 Requests/Sekunde)
    time.sleep(1)
