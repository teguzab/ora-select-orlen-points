# Punkty Orlen Paczka – Ora Select

Codziennie aktualizowana lista punktów odbioru Orlen Paczka (publiczne API `GiveMeAllLocationWithAllDataWithZipCode`, bez kluczy),
używana przez mapę wyboru punktu w koszyku sklepu oraselect.pl.

- `fetch_points.py` – pobiera punkty i zapisuje kompaktowy `orlen-points.json`
- `.github/workflows/update.yml` – uruchamia skrypt codziennie i czyści cache jsDelivr
- plik dla sklepu: `https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/orlen-points.json`
