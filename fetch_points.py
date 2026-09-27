#!/usr/bin/env python3
"""Pobiera wszystkie punkty Orlen Paczka i zapisuje kompaktowy orlen-points.json.

Metoda GiveMeAllLocationWithAllDataWithZipCode jest publiczna (bez PartnerID/Key).
Tylko biblioteka standardowa - działa lokalnie i w GitHub Actions.

Format wyjścia:
{
  "updated": "2026-09-27T10:00:00Z",
  "fields": ["psd","code","lat","lng","type","street","zip","city","hours","desc"],
  "types": {"APM": "Automat paczkowy", ...},
  "hours": ["Pn-Pt:00:00-24:00, ...", ...],   # point[8] to indeks w tej liście
  "points": [[...], ...]
}
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

URL = "https://api.orlenpaczka.pl/WebServicePwRProd/WebServicePwR.asmx"
NS = "https://91.242.220.103/WebServicePwR"
METHOD = "GiveMeAllLocationWithAllDataWithZipCode"
MIN_POINTS = 5000  # zabezpieczenie: nie nadpisuj pliku, jeśli API zwróci śmieci

TYPES = {
    "APM": "Automat paczkowy",
    "PPP": "Punkt partnerski",
    "PKN": "Stacja ORLEN",
    "PPK": "Punkt odbioru",
}

ENVELOPE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    f'<soap:Body><{METHOD} xmlns="{NS}"/></soap:Body></soap:Envelope>'
)


def fetch() -> bytes:
    req = urllib.request.Request(
        URL,
        data=ENVELOPE.encode(),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{NS}/{METHOD}"',
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def clean(s: str) -> str:
    return " ".join((s or "").split())


def street_title(s: str) -> str:
    # API zwraca ulice WIELKIMI LITERAMI - ładniej w UI
    s = clean(s)
    return s.title() if s.isupper() else s


def parse(xml: bytes) -> list:
    points = []
    for row in ET.fromstring(xml).iter("LocationWithAllData2"):
        d = {c.tag: (c.text or "") for c in row}
        if d.get("Available", "T") != "T":
            continue
        try:
            lat = round(float(d["Latitude"]), 5)
            lng = round(float(d["Longitude"]), 5)
        except (KeyError, ValueError):
            continue
        street = street_title(d.get("StreetName"))
        nr = clean(d.get("BuildingNumber"))
        points.append([
            clean(d.get("PSD")),
            clean(d.get("DestinationCode")),
            lat,
            lng,
            clean(d.get("PointType")),
            f"{street} {nr}".strip(),
            clean(d.get("Zipcode")),
            clean(d.get("City")),
            clean(d.get("OpeningHours")),
            clean(d.get("Location")),
        ])
    points.sort(key=lambda p: (p[7], p[5]))
    return points


def dedupe_hours(points: list) -> list:
    # godziny powtarzają się tysiące razy - zamieniamy je na indeks do listy
    hours = sorted({p[8] for p in points})
    index = {h: i for i, h in enumerate(hours)}
    for p in points:
        p[8] = index[p[8]]
    return hours


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "orlen-points.json")
    points = parse(fetch())
    if len(points) < MIN_POINTS:
        print(f"Za mało punktów ({len(points)}) - nie nadpisuję {out}", file=sys.stderr)
        return 1
    hours = dedupe_hours(points)
    data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": ["psd", "code", "lat", "lng", "type", "street", "zip", "city", "hours", "desc"],
        "types": TYPES,
        "hours": hours,
        "points": points,
    }
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Zapisano {len(points)} punktów do {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
