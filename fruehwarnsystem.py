import json
import os
from datetime import date
from pathlib import Path

import duckdb
import requests

DUCKDB_PATH = os.environ.get("DIP_DUCKDB_PATH", "dip_analytics.duckdb")
DIP_SQLITE_PATH = os.environ.get("DIP_SQLITE_PATH")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
GEMINI_MODEL = "gemini-3.6-flash"
REPORT_DIR = Path(os.environ.get("DIP_REPORT_DIR", "reports"))


def load_letzte_entwicklungen():
    if not DIP_SQLITE_PATH:
        raise RuntimeError("DIP_SQLITE_PATH ist nicht gesetzt - wird für den Attach der Rohdaten benötigt")

    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    con.execute(f"ATTACH '{DIP_SQLITE_PATH}' AS dip_raw (TYPE SQLITE, READ_ONLY)")
    ergebnis = con.execute("select * from main.mart_fruehwarnsystem").fetchall()
    spalten = [beschreibung[0] for beschreibung in con.description]
    con.close()
    return [dict(zip(spalten, zeile)) for zeile in ergebnis]


def berechne_kpis(entwicklungen):
    betroffene_vorgaenge = {eintrag["vorgang_id"] for eintrag in entwicklungen}
    return {
        "anzahl_vorgaenge": len(betroffene_vorgaenge),
        "anzahl_aenderungen": len(entwicklungen),
    }


def baue_gemini_prompt(entwicklungen):
    items = [
        {
            "vorgang": eintrag["vorgang_titel"],
            "vorgangstyp": eintrag["vorgangstyp"],
            "beratungsstand": eintrag["beratungsstand"],
            "schritt": eintrag["vorgangsposition_titel"],
            "datum": str(eintrag["position_datum"]),
            "urheber": eintrag["urheber"],
            "beschluesse": eintrag["beschluesse"],
        }
        for eintrag in entwicklungen
    ]
    return (
        "Du erstellst ein taegliches Fruehwarnsystem-Briefing zu parlamentarischen Vorgaengen "
        "im Themenbereich Rente/Altersvorsorge fuer die letzten 3 Tage.\n"
        "Fasse die wesentlichen Entwicklungen zusammen. Nenne fuer jede relevante Entwicklung, "
        "welche Fraktion oder Institution (Urheber) sie vorangetrieben hat und welche Position "
        "damit vertreten wird (z.B. Antrag eingebracht, Ueberweisung an Ausschuss, Beschluss "
        "gefasst mit welchem Ergebnis). Gruppiere nach Vorgang, wenn mehrere Schritte denselben "
        "Vorgang betreffen. Schreibe in klarem, sachlichem Deutsch, maximal 400 Woerter. "
        "Erwaehne explizit, wenn zu einer Entwicklung kein Urheber bekannt ist, statt ihn zu erfinden.\n\n"
        f"Rohdaten:\n{json.dumps(items, ensure_ascii=False, indent=2, default=str)}"
    )


def request_gemini_summary(prompt):
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_KEY, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def formatiere_detailzeile(eintrag):
    zeile = (
        f"- **{eintrag['vorgang_titel']}** ({eintrag['vorgangstyp']}, {eintrag['beratungsstand']}): "
        f"{eintrag['vorgangsposition_titel']} am {eintrag['position_datum']}"
    )
    if eintrag["urheber"]:
        zeile += f" — Urheber: {eintrag['urheber']}"
    if eintrag["beschluesse"]:
        zeile += f" — Beschluss: {eintrag['beschluesse']}"
    return zeile


def schreibe_bericht(kpis, zusammenfassung, entwicklungen):
    REPORT_DIR.mkdir(exist_ok=True)
    heute = date.today().isoformat()
    pfad = REPORT_DIR / f"fruehwarnsystem_{heute}.md"

    zeilen = [
        f"# Frühwarnsystem Rente/Altersvorsorge – {heute}",
        "",
        "## Kennzahlen (letzte 3 Tage)",
        f"- Betroffene Vorgänge: {kpis['anzahl_vorgaenge']}",
        f"- Vorgangsschritte/Änderungen: {kpis['anzahl_aenderungen']}",
        "",
        "## Zusammenfassung",
        zusammenfassung,
        "",
        "## Details",
    ]
    zeilen.extend(formatiere_detailzeile(eintrag) for eintrag in entwicklungen)

    pfad.write_text("\n".join(zeilen), encoding="utf-8")
    return pfad


def fruehwarnsystem_erstellen():
    entwicklungen = load_letzte_entwicklungen()
    kpis = berechne_kpis(entwicklungen)

    if not entwicklungen:
        zusammenfassung = "Keine Änderungen in den letzten 3 Tagen."
    elif GEMINI_KEY:
        zusammenfassung = request_gemini_summary(baue_gemini_prompt(entwicklungen))
    else:
        zusammenfassung = (
            "GEMINI_KEY nicht gesetzt — automatische Zusammenfassung übersprungen, "
            "Details siehe unten."
        )

    pfad = schreibe_bericht(kpis, zusammenfassung, entwicklungen)
    print(f"Frühwarnsystem-Bericht geschrieben: {pfad}")
    return pfad


if __name__ == "__main__":
    fruehwarnsystem_erstellen()