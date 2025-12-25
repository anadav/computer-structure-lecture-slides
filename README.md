# Computer Structure Course - Beamer Presentations

LaTeX Beamer slides for Computer Structure course (2360267).

## Prerequisites

- **TeX Live** (via Homebrew): `brew install texlive`
- **Python 3** (any version, including 3.13+)
- **rsvg-convert** (for SVG to PDF): `brew install librsvg`
- **pdfcrop** (included with TeX Live)

## Building

```bash
make                           # Build all presentations
make build/lecture_01_intro.pdf  # Build a specific lecture
make clean                     # Remove all build artifacts
```

Output PDFs are placed in `output/` directory.

## Minted (Syntax Highlighting)

The presentations use the `minted` package for syntax-highlighted code blocks. This requires:

1. **latexminted** Python package
2. **Pygments** for syntax highlighting

The Makefile automatically:
- Creates a Python virtual environment (`.venv/`)
- Installs `latexminted` and `Pygments`
- Applies patches for compatibility issues (see below)

### Known Issues & Patches

The Makefile applies two patches to work around upstream bugs:

1. **Python 3.13+ argparse compatibility** ([gpoore/minted#463](https://github.com/gpoore/minted/issues/463))
   - Python 3.13+ changed the `argparse` API, breaking `latexminted`
   - Fix: Modify `ArgParser.__init__()` to accept `**kwargs`

2. **minted.sty v3.6 / latexminted v0.6 version mismatch**
   - `latexminted` expects `tokenmerge` filter option that older `minted.sty` doesn't provide
   - Fix: Use `.get()` instead of direct dict access for filter options

These patches are applied automatically when the venv is created. If you encounter issues, try:

```bash
rm -rf .venv
make
```

## Project Structure

```
.
├── Makefile              # Build system
├── *.tex                 # Lecture source files
├── figures/              # SVG figures (converted to PDF)
├── svg/                  # Additional SVG files
├── build/                # Intermediate build files
├── output/               # Final PDF outputs
├── generated/            # Generated PDFs from figures
└── .venv/                # Python virtual environment
```
