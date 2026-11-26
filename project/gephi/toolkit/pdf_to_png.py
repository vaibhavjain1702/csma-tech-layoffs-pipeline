"""Rasterise Gephi Preview PDF exports to PNG (white background, >= 3000 px wide).

Gephi's PNG exporter cannot run with -Djava.awt.headless=true, so GephiRun exports the Preview
as PDF and this script renders page 1 of each PDF with MuPDF (PyMuPDF). The pixels are Gephi's
vector drawing; nothing is redrawn.

Usage: python pdf_to_png.py WIDTH_PX file1.pdf [file2.pdf ...]
Needs: pymupdf==1.24.10 (installed in a throwaway venv, not the system Python).
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF


def main() -> None:
    width = int(sys.argv[1])
    for p in sys.argv[2:]:
        pdf = Path(p)
        doc = fitz.open(pdf)
        page = doc[0]
        zoom = width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        out = pdf.with_suffix(".png")
        pix.save(out)
        print(f"{out.name}: {pix.width}x{pix.height}")


if __name__ == "__main__":
    main()
