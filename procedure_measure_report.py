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


def load_recent_developments():
    if not DIP_SQLITE_PATH:
        raise RuntimeError("DIP_SQLITE_PATH ist nicht gesetzt - wird für den Attach der Rohdaten benötigt")

    con = duckdb.connect(DUCKDB_PATH, read_only=True)
    con.execute(f"ATTACH '{DIP_SQLITE_PATH}' AS dip_raw (TYPE SQLITE, READ_ONLY)")
    result = con.execute("select * from main.mart_fruehwarnsystem").fetchall()
    columns = [description[0] for description in con.description]
    con.close()
    return [dict(zip(columns, row)) for row in result]


def calculate_kpis(developments):
    affected_procedures = {entry["vorgang_id"] for entry in developments}
    return {
        "anzahl_vorgaenge": len(affected_procedures),
        "anzahl_aenderungen": len(developments),
    }


def build_gemini_prompt(developments):
    items = [
        {
            "vorgang": entry["vorgang_titel"],
            "vorgangstyp": entry["vorgangstyp"],
            "beratungsstand": entry["beratungsstand"],
            "schritt": entry["vorgangsposition_titel"],
            "datum": str(entry["position_datum"]),
            "urheber": entry["urheber"],
            "beschluesse": entry["beschluesse"],
        }
        for entry in developments
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


def format_detail_line(entry):
    line = (
        f"- **{entry['vorgang_titel']}** ({entry['vorgangstyp']}, {entry['beratungsstand']}): "
        f"{entry['vorgangsposition_titel']} am {entry['position_datum']}"
    )
    if entry["urheber"]:
        line += f" — Urheber: {entry['urheber']}"
    if entry["beschluesse"]:
        line += f" — Beschluss: {entry['beschluesse']}"
    return line


def write_report(kpis, summary, developments):
    REPORT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    path = REPORT_DIR / f"fruehwarnsystem_{today}.md"

    lines = [
        f"# Frühwarnsystem Rente/Altersvorsorge – {today}",
        "",
        "## Kennzahlen (letzte 3 Tage)",
        f"- Betroffene Vorgänge: {kpis['anzahl_vorgaenge']}",
        f"- Vorgangsschritte/Änderungen: {kpis['anzahl_aenderungen']}",
        "",
        "## Zusammenfassung",
        summary,
        "",
        "## Details",
    ]
    lines.extend(format_detail_line(entry) for entry in developments)

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def create_early_warning_report():
    developments = load_recent_developments()
    kpis = calculate_kpis(developments)

    if not developments:
        summary = "Keine Änderungen in den letzten 3 Tagen."
    elif GEMINI_KEY:
        summary = request_gemini_summary(build_gemini_prompt(developments))
    else:
        summary = (
            "GEMINI_KEY nicht gesetzt — automatische Zusammenfassung übersprungen, "
            "Details siehe unten."
        )

    path = write_report(kpis, summary, developments)
    print(f"Frühwarnsystem-Bericht geschrieben: {path}")
    return path


if __name__ == "__main__":
    create_early_warning_report()