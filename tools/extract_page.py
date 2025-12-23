#!/usr/bin/env python3
"""Extract a single page from a PDF as an image for quick preview."""

import argparse
import subprocess
import sys
from pathlib import Path


def extract_page(pdf_path: Path, page_num: int, output_path: Path | None = None) -> Path:
    """Extract a page from PDF using pdftoppm (comes with poppler)."""
    if not pdf_path.exists():
        print(f"Error: {pdf_path} does not exist", file=sys.stderr)
        sys.exit(1)

    if output_path is None:
        output_path = pdf_path.with_suffix(f".page{page_num}.png")

    # Use sips (macOS built-in) via PDF rendering, or pdftoppm if available
    try:
        # Try pdftoppm first (better quality)
        result = subprocess.run(
            ["pdftoppm", "-png", "-f", str(page_num), "-l", str(page_num),
             "-singlefile", str(pdf_path), str(output_path.with_suffix(""))],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Extracted page {page_num} to {output_path}")
            return output_path
    except FileNotFoundError:
        pass

    # Fallback: use sips to convert entire PDF (macOS)
    try:
        # Create temp dir for extraction
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["sips", "-s", "format", "png", str(pdf_path),
                 "--out", str(output_path), "-z", "1200", "1600"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"Extracted to {output_path}")
                return output_path
    except FileNotFoundError:
        pass

    # Last resort: use ImageMagick convert
    try:
        result = subprocess.run(
            ["convert", "-density", "150", f"{pdf_path}[{page_num - 1}]",
             str(output_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Extracted page {page_num} to {output_path}")
            return output_path
    except FileNotFoundError:
        pass

    print("Error: No PDF extraction tool found (tried pdftoppm, sips, convert)", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Extract a page from PDF as PNG')
    parser.add_argument('pdf', type=Path, help='Input PDF file')
    parser.add_argument('page', type=int, help='Page number (1-indexed)')
    parser.add_argument('-o', '--output', type=Path, help='Output PNG path')

    args = parser.parse_args()
    extract_page(args.pdf, args.page, args.output)


if __name__ == '__main__':
    main()
