import datetime
import json
import os
import requests

# Konfiguration
API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_URL = "https://api.etherscan.io/v2/api"

# Zu überwachende Börsen-Wallets
TARGET_WALLETS = {
    "Binance Hot Wallet": "0x2000c8296d514080934071355743bf21d60",
    "Coinbase Hot Wallet": "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
    "Kraken Hot Wallet": "0xFC9161b4ac969B7B9",
}

# Schwellenwerte für Alarme pro Wallet
THRESHOLD_ETH = 100.0
THRESHOLD_USD = 300000.0


def fetch_eth_price():
  """Holt den aktuellen ETH-Preis in USD via CoinGecko Public API."""
  try:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url, timeout=10)
    data = response.json()
    return float(data["ethereum"]["usd"])
  except Exception as e:
    print(f"[PRICE ERROR] Konnte ETH-Preis nicht abrufen: {e}")
    return 0.0


def load_previous_data():
  """Lädt die vorherigen Daten aus der JSON-Datei, falls vorhanden."""
  if os.path.exists("onchain_data.json"):
    try:
      with open("onchain_data.json", "r") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def fetch_onchain_balance(address):
  """Ruft den aktuellen ETH-Kontostand einer Adresse von Etherscan V2 ab."""
  if not API_KEY:
    return None

  params = {
      "chainid": "1",
      "module": "account",
      "action": "balance",
      "address": address,
      "tag": "latest",
      "apikey": API_KEY,
  }

  try:
    response = requests.get(ETHERSCAN_URL, params=params, timeout=10)
    data = response.json()

    if data["status"] == "1":
      wei_balance = int(data["result"])
      return wei_balance / 10**18
    else:
      print(f"[API ERROR for {address}] {data.get('message')}")
      return None
  except Exception as e:
    print(f"[CONNECTION ERROR for {address}] {e}")
    return None


if __name__ == "__main__":
  print("Starte Multi-Wallet On-Chain & Markt-Abfrage...")

  eth_price = fetch_eth_price()
  previous_data = load_previous_data().get("wallets", {})

  wallet_results = {}
  global_alert = False

  for name, address in TARGET_WALLETS.items():
    print(f"Prüfe {name} ({address})...")
    current_balance = fetch_onchain_balance(address)

    if current_balance is None:
      continue

    current_usd = current_balance * eth_price

    # Alten Stand für diese spezifische Wallet holen
    prev_wallet_info = previous_data.get(name, {})
    previous_balance = prev_wallet_info.get("eth_balance", current_balance)

    delta_eth = current_balance - previous_balance
    delta_usd = delta_eth * eth_price

    alert_triggered = False
    alert_message = ""

    if abs(delta_eth) >= THRESHOLD_ETH or abs(delta_usd) >= THRESHOLD_USD:
      alert_triggered = True
      global_alert = True
      direction = "Inflow" if delta_eth > 0 else "Outflow"
      alert_message = (
          f"[WHALE ALERT - {name}] {direction}! Delta: {delta_eth:,.2f} ETH"
          f" (~{delta_usd:,.2f} USD)"
      )
      print(alert_message)

    wallet_results[name] = {
        "address": address,
        "eth_balance": current_balance,
        "total_usd": current_usd,
        "delta_eth": delta_eth,
        "delta_usd": delta_usd,
        "alert": alert_triggered,
        "alert_message": alert_message,
    }

  # Gesamt-Struktur aufbereiten
  result_data = {
      "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
      "eth_price_usd": eth_price,
      "global_alert": global_alert,
      "wallets": wallet_results,
      "status": "success",
  }

  filename = "onchain_data.json"
  with open(filename, "w") as f:
    json.dump(result_data, f, indent=4)
  print(f"Multi-Wallet Daten erfolgreich in {filename} gespeichert.")
