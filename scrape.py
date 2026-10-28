"""Lädt die aktuelle Auslastung der Zürcher Bäder und hängt neue Werte an ein Monats-Log an.

Quelle: Open Data Zürich, Datensatz ssd_spo_badi_aktuell (crowd-monitor.csv)
Ausgabe: data/YYYY-MM.csv  (eine Datei pro Monat, damit die Dateien klein bleiben)
"""
import csv
import io
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CSV_URL = "https://data.stadt-zuerich.ch/dataset/ssd_spo_badi_aktuell/download/crowd-monitor.csv"
API_URL = ("https://data.stadt-zuerich.ch/api/3/action/datastore_search"
           "?resource_id=c8c4e87f-28eb-4437-92df-aada5b35111c&limit=1000")
HEADERS = {"User-Agent": "badi-logger (GitHub Actions; private Auswertung)"}

DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "last.json"  # letzte retrievaltime pro Bad, gegen Duplikate
FIELDS = ["logged_at", "retrievaltime", "uid", "name", "currentfill", "occupancy_icons"]


def get(url: str) -> bytes:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as res:
                return res.read()
        except Exception as e:
            print(f"Versuch {attempt + 1} fehlgeschlagen ({url}): {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Konnte {url} nicht laden")


def fetch_rows() -> list[dict]:
    try:
        text = get(CSV_URL).decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))
    except Exception as e:
        print(f"CSV nicht verfügbar, versuche API: {e}")
        data = json.loads(get(API_URL))
        return data["result"]["records"]


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    now = datetime.now(timezone.utc)
    logged_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    out_file = DATA_DIR / f"{now:%Y-%m}.csv"

    new_rows = []
    for row in fetch_rows():
        key = row.get("uid") or row.get("name")
        rt = row.get("retrievaltime", "")
        if not key or state.get(key) == rt:
            continue  # unverändert seit dem letzten Lauf
        state[key] = rt
        new_rows.append({"logged_at": logged_at, **{f: row.get(f, "") for f in FIELDS[1:]}})

    if not new_rows:
        print("Keine neuen Werte.")
        return

    write_header = not out_file.exists()
    with out_file.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        w.writerows(new_rows)

    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    print(f"{len(new_rows)} neue Zeilen in {out_file}")


if __name__ == "__main__":
    main()
