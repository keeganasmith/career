from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List
import re

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Cell:
    x: int
    y: int
    ch: str


def _clean_text(s: str) -> str:
    # Normalize whitespace while preserving actual unicode characters
    s = s.replace("\u00a0", " ")  # NBSP -> space
    return re.sub(r"\s+", " ", s).strip()


def _parse_cells_from_published_doc_html(html: str) -> List[Cell]:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table is None:
        raise ValueError("No <table> found in the document HTML. Is this a *published* Google Doc URL?")

    rows = table.find_all("tr")
    if not rows or len(rows) < 2:
        raise ValueError("Table has no data rows.")

    cells: List[Cell] = []

    # Skip header row (assumed first)
    for tr in rows[1:]:
        tds = tr.find_all(["td", "th"])
        if len(tds) < 3:
            continue

        x_txt = _clean_text(tds[0].get_text())
        ch_txt = _clean_text(tds[1].get_text())
        y_txt = _clean_text(tds[2].get_text())

        if not x_txt or not y_txt:
            continue

        try:
            x = int(x_txt)
            y = int(y_txt)
        except ValueError:
            # If a weird non-numeric slips in, ignore the row
            continue

        # Character cell might contain a single Unicode character.
        # If it contains multiple characters, take the first non-space.
        ch = ch_txt if ch_txt else " "
        if len(ch) > 1:
            # Prefer first non-space char; otherwise first char.
            non_space = next((c for c in ch if c != " "), ch[0])
            ch = non_space

        cells.append(Cell(x=x, y=y, ch=ch))

    if not cells:
        raise ValueError("No valid (x, char, y) rows parsed from the table.")

    return cells


def print_secret_message_grid(published_google_doc_url: str) -> None:
    """
    Fetch a *published* Google Doc URL that contains a table with:
      x-coordinate | Character | y-coordinate

    Print the reconstructed grid, filling unspecified positions with spaces.
    """
    resp = requests.get(published_google_doc_url, timeout=30)
    resp.raise_for_status()

    cells = _parse_cells_from_published_doc_html(resp.text)

    max_x = max(c.x for c in cells)
    max_y = max(c.y for c in cells)

    grid: List[List[str]] = [[" " for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for c in cells:
        if 0 <= c.x <= max_x and 0 <= c.y <= max_y:
            grid[max_y - c.y][c.x] = c.ch

    for row in grid:
        print("".join(row))


print_secret_message_grid(" https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub")
