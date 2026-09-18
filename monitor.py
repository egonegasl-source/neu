import datetime
import json
import os
import requests

# API-Key aus den GitHub Secrets auslesen
API_KEY = os.getenv("ETHERSCAN_API_KEY")
TARGET_ADDRESS = "0x2000c8296d514080934071355743bf21d60"  # Binance Hot Wallet als Referenz

# Korrigierte Etherscan API V2 URL
ETHERSCAN_URL = "https://api.etherscan.io/v2/api"


def fetch_onchain_data():
  if not API_KEY:
    print("Fehler: ETHERSCAN_API_KEY Secret nicht gefunden!")
    return None

  # Parameter für die V2 API inklusive chainid (1 für Ethereum Mainnet)
  params = {
      "chainid": "1",
      "module": "account",
      "action": "balance",
      "address": TARGET_ADDRESS,
      "tag": "latest",
      "apikey": API_KEY,
  }

  try:
    response = requests.get(ETHERSCAN_URL, params=params)
    data = response.json()

    if data["status"] == "1":
      wei_balance = int(data["result"])
      eth_balance = wei_balance / 10**18

      result_data = {
          "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
          "address": TARGET_ADDRESS,
          "eth_balance": eth_balance,
          "status": "success",
      }
      return result_data
    else:
      print(f"[API ERROR] {data.get('message')}: {data.get('result')}")
      return None

  except Exception as e:
    print(f"[CONNECTION ERROR] {e}")
    return None


if __name__ == "__main__":
  print("Starte On-Chain Abfrage...")
  data = fetch_onchain_data()

  if data:
    # Daten in JSON-Datei speichern
    filename = "onchain_data.json"
    with open(filename, "w") as f:
      json.dump(data, f, indent=4)
    print(f"Daten erfolgreich in {filename} gespeichert.")
