import datetime
import json
import os
import requests

# Konfiguration
API_KEY = os.getenv("ETHERSCAN_API_KEY")
TARGET_ADDRESS = "0x2000c8296d514080934071355743bf21d60"  # Binance Hot Wallet
ETHERSCAN_URL = "https://api.etherscan.io/v2/api"

# Schwellenwerte für Alarme (Beispielwerte: ab 100 ETH oder ca. 300.000 USD Bewegung)
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
      return None
  return None


def fetch_onchain_balance():
  """Ruft den aktuellen ETH-Kontostand von Etherscan V2 ab."""
  if not API_KEY:
    print("Fehler: ETHERSCAN_API_KEY Secret nicht gefunden!")
    return None

  params = {
      "chainid": "1",
      "module": "account",
      "action": "balance",
      "address": TARGET_ADDRESS,
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
      print(f"[API ERROR] {data.get('message')}: {data.get('result')}")
      return None
  except Exception as e:
    print(f"[CONNECTION ERROR] {e}")
    return None


if __name__ == "__main__":
  print("Starte erweiterte On-Chain & Markt-Abfrage...")

  # 1. Aktuelle On-Chain Daten & Marktpreis holen
  current_balance = fetch_onchain_balance()
  if current_balance is None:
    exit(1)

  eth_price = fetch_eth_price()
  current_usd = current_balance * eth_price

  # 2. Alten Stand laden für Delta-Berechnung
  previous_data = load_previous_data()
  previous_balance = (
      previous_data.get("eth_balance", current_balance)
      if previous_data
      else current_balance
  )

  # 3. Differenz berechnen (Delta)
  delta_eth = current_balance - previous_balance
  delta_usd = delta_eth * eth_price

  # 4. Schwellenwert-Prüfung (Alarm-Logik)
  alert_triggered = False
  alert_message = ""

  if abs(delta_eth) >= THRESHOLD_ETH or abs(delta_usd) >= THRESHOLD_USD:
    alert_triggered = True
    direction = "Zustrom (Inflow)" if delta_eth > 0 else "Abfluss (Outflow)"
    alert_message = (
        f"[WHALE ALERT] Signifikanter {direction}! Delta: {delta_eth:,.2f} ETH"
        f" (~{delta_usd:,.2f} USD)"
    )
    print(alert_message)
  else:
    print(
        f"Keine Überschreitung der Schwellenwerte. Delta: {delta_eth:,.2f} ETH"
        f" (~{delta_usd:,.2f} USD)"
    )

  # 5. Strukturierte Daten für die JSON-Speicherung aufbereiten
  result_data = {
      "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
      "address": TARGET_ADDRESS,
      "eth_balance": current_balance,
      "eth_price_usd": eth_price,
      "total_usd": current_usd,
      "delta_eth": delta_eth,
      "delta_usd": delta_usd,
      "alert": alert_triggered,
      "alert_message": alert_message,
      "status": "success",
  }

  filename = "onchain_data.json"
  with open(filename, "w") as f:
    json.dump(result_data, f, indent=4)
  print(f"Erweiterte Daten erfolgreich in {filename} gespeichert.")
    print(f"Daten erfolgreich in {filename} gespeichert.")
