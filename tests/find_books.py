# Rode com: python .\tests\find_books.py --query "romance brasileiro" "harry potter" --max-per-query 8

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coleta dados de livros usando a Google Books API e imprime JSON no formato:
[
  {
    "bookName": "...",
    "authorName": "...",
    "publisherName": "...",
    "publishedDate": "...",
    "description": "..."
  },
  ...
]

Uso:
  python books_fetch.py --query "harry potter" "machado de assis" --max-per-query 10
  python books_fetch.py --isbn 9788535914849 9786580211159 --out livros.json
"""

import argparse
import json
import sys
import time
import urllib.parse
from typing import Dict, List, Set, Tuple

import requests

GB_BASE = "https://www.googleapis.com/books/v1/volumes"

def fetch_google_books(q: str, max_items: int = 10) -> List[Dict]:
    """Busca livros para uma query `q` (palavra-chave ou 'isbn:XXXX')."""
    results = []
    fetched = 0
    start_index = 0

    # Google Books retorna no máx. 40 por página
    while fetched < max_items:
        remaining = max_items - fetched
        max_results = min(40, remaining)
        params = {
            "q": q,
            "printType": "books",
            "maxResults": max_results,
            "startIndex": start_index,
            # opcional: filtro por idioma, ex: "langRestrict": "pt"
        }
        r = requests.get(GB_BASE, params=params, timeout=20)
        r.raise_for_status()
        payload = r.json()
        items = payload.get("items", []) or []
        if not items:
            break

        for it in items:
            info = (it.get("volumeInfo") or {})
            title = (info.get("title") or "").strip()
            authors = info.get("authors") or []
            author_str = ", ".join([a.strip() for a in authors if a]) if authors else ""
            publisher = (info.get("publisher") or "").strip()
            pub_date = (info.get("publishedDate") or "").strip()
            desc = (info.get("description") or "").strip()

            # Mapeia para o formato pedido
            results.append({
                "bookName": title,
                "authorName": author_str,
                "publisherName": publisher,
                "publishedDate": pub_date,
                "description": desc,
            })

        count = len(items)
        fetched += count
        start_index += count
        # Pequena pausa para ser gentil com a API pública
        time.sleep(0.15)

        if count == 0:
            break

    return results

def dedupe(items: List[Dict]) -> List[Dict]:
    """Remove duplicatas por (bookName, authorName), ignorando caixa e espaços extras."""
    seen: Set[Tuple[str, str]] = set()
    out: List[Dict] = []
    for it in items:
        key = ( (it.get("bookName","") or "").strip().lower(),
                (it.get("authorName","") or "").strip().lower() )
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def main():
    ap = argparse.ArgumentParser(description="Coletor de livros (Google Books -> JSON).")
    ap.add_argument("--query", nargs="*", help="Termos de busca (ex.: 'harry potter' 'machado de assis').")
    ap.add_argument("--isbn", nargs="*", help="Lista de ISBNs (ex.: 9788535914849 9786580211159).")
    ap.add_argument("--max-per-query", type=int, default=10, help="Máximo de resultados por termo (default: 10).")
    ap.add_argument("--out", help="Arquivo de saída .json (se omitido, imprime no stdout).")
    args = ap.parse_args()

    if not args.query and not args.isbn:
        print("Informe ao menos --query ou --isbn.", file=sys.stderr)
        sys.exit(2)

    all_items: List[Dict] = []

    # Busca por termos
    for q in args.query or []:
        q_norm = q.strip()
        if not q_norm:
            continue
        all_items.extend(fetch_google_books(q_norm, max_items=args.max_per_query))

    # Busca por ISBN
    for code in args.isbn or []:
        code = code.strip()
        if not code:
            continue
        all_items.extend(fetch_google_books(f"isbn:{code}", max_items=1))

    # Deduplica
    final_items = dedupe(all_items)

    # Saída JSON (texto) — pronto para usar no seu cadastro
    text = json.dumps(final_items, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"OK! {len(final_items)} registros salvos em {args.out}")
    else:
        print(text)

if __name__ == "__main__":
    main()


