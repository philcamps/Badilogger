# Badi-Logger Zürich

Loggt alle 15 Minuten die aktuelle Auslastung der Zürcher Bäder aus dem Open-Data-Datensatz
[ssd_spo_badi_aktuell](https://data.stadt-zuerich.ch/dataset/ssd_spo_badi_aktuell).

- `scrape.py` lädt die Daten und hängt neue Werte an `data/YYYY-MM.csv` an
- `.github/workflows/scrape.yml` startet das Script automatisch
- Zeiten in `logged_at` sind UTC; `retrievaltime` kommt unverändert aus der Quelle
