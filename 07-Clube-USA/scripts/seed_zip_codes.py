#!/usr/bin/env python3
"""
Seed da tabela zip_codes com centroides de ZIPs dos EUA.

Fonte dos dados: simplemaps.com/data/us-zips (Free Tier, licença MIT)
URL de download: https://simplemaps.com/static/data/us-zips/1.86/basic/simplemaps_uszips_basicv1.86.zip

Como usar:
1. Baixe o CSV em: https://simplemaps.com/data/us-zips (botão "Download Basic")
2. Extraia o arquivo uszips.csv do zip
3. Execute:
   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/seed_zip_codes.py uszips.csv

Opcional — filtrar por estado (ex: apenas FL, NY, NJ, MA, TX, CA, GA):
   python scripts/seed_zip_codes.py uszips.csv --states FL,NY,NJ,MA,TX,CA,GA

O script é idempotente: re-executar apenas atualiza registros existentes (upsert).
"""
import argparse
import csv
import os
import sys
from pathlib import Path

try:
    from supabase import create_client
except ImportError:
    print("Erro: instale as dependências primeiro: pip install supabase", file=sys.stderr)
    sys.exit(1)

BATCH_SIZE = 500
REQUIRED_COLUMNS = {"zip", "lat", "lng", "city", "state_id"}


def parse_args():
    parser = argparse.ArgumentParser(description="Seed zip_codes table from simplemaps CSV")
    parser.add_argument("csv_path", help="Caminho para o arquivo uszips.csv")
    parser.add_argument(
        "--states",
        default="",
        help="Filtrar estados (ex: FL,NY,NJ). Vazio = todos os estados.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Apenas valida o CSV sem inserir")
    return parser.parse_args()


def load_rows(csv_path: str, states_filter: set[str]) -> list[dict]:
    path = Path(csv_path)
    if not path.exists():
        print(f"Arquivo não encontrado: {csv_path}", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            print(f"Colunas faltando no CSV: {missing}", file=sys.stderr)
            print(f"Colunas encontradas: {reader.fieldnames}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            state = row.get("state_id", "").strip().upper()
            if states_filter and state not in states_filter:
                continue
            try:
                lat = float(row["lat"])
                lon = float(row["lng"])
            except (ValueError, KeyError):
                continue
            zip_code = row["zip"].strip().zfill(5)
            if not zip_code or len(zip_code) != 5:
                continue
            rows.append({
                "zip": zip_code,
                "city": row.get("city", "").strip() or None,
                "state": state,
                "latitude": lat,
                "longitude": lon,
            })

    return rows


def seed(rows: list[dict], dry_run: bool = False) -> None:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        print("Erro: defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY como env vars.", file=sys.stderr)
        sys.exit(1)

    total = len(rows)
    print(f"Total de ZIPs a inserir/atualizar: {total}")

    if dry_run:
        print("Dry run — nenhum dado foi inserido.")
        return

    db = create_client(url, key)
    inserted = 0
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        db.table("zip_codes").upsert(batch, on_conflict="zip").execute()
        inserted += len(batch)
        print(f"  {inserted}/{total} inseridos...", end="\r")

    print(f"\nConcluído: {inserted} ZIPs no banco.")


def main():
    args = parse_args()
    states_filter = {s.strip().upper() for s in args.states.split(",") if s.strip()}
    if states_filter:
        print(f"Filtrando estados: {sorted(states_filter)}")

    rows = load_rows(args.csv_path, states_filter)
    if not rows:
        print("Nenhuma linha válida encontrada no CSV. Verifique o arquivo e os filtros.")
        sys.exit(1)

    seed(rows, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
