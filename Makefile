# Makefile to build all .tex files into the build directory

# Python venv for minted/latexminted
VENV := .venv
VENV_BIN := $(VENV)/bin
VENV_ACTIVATE := $(VENV_BIN)/activate
LATEXMINTED := $(VENV_BIN)/latexminted

TEXFILES := $(wildcard *.tex)
BUILDDIR := build
OUTPUTDIR := output
GENDIR := generated
PDFS := $(patsubst %.tex,$(BUILDDIR)/%.pdf,$(TEXFILES))
OUTPUT_PDFS := $(patsubst %.tex,$(OUTPUTDIR)/%.pdf,$(TEXFILES))
SVGFILES := $(wildcard svg/*.svg)
SVGPDFS := $(patsubst %.svg,%.pdf,$(SVGFILES))
FIGSVGFILES := $(wildcard figures/*.svg)
FIGPDFS := $(patsubst figures/%.svg,$(GENDIR)/%.pdf,$(FIGSVGFILES))

all: $(BUILDDIR) $(OUTPUTDIR) $(GENDIR) $(SVGPDFS) $(FIGPDFS) $(PDFS) $(OUTPUT_PDFS)
	@# Clean up any PDFs that might have been generated in the main directory
	@rm -f *.pdf
	@rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb

# Create venv and install latexminted + pygments
# Patches fix Python 3.13+ argparse compatibility (https://github.com/gpoore/minted/issues/463)
# and minted.sty v3.6 / latexminted v0.6 version mismatch (tokenmerge KeyError)
$(VENV_ACTIVATE):
	python3 -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install latexminted Pygments
	@# Fix Python 3.13+ argparse compatibility in cmdline.py
	$(VENV_BIN)/python -c "import pathlib; f=next(pathlib.Path('$(VENV)').rglob('latexminted/cmdline.py')); t=f.read_text(); f.write_text(t.replace('def __init__(self, *, prog: str):', 'def __init__(self, *, prog: str, **kwargs):').replace('super().__init__(\\n            prog=prog,\\n            allow_abbrev=False,\\n            formatter_class=argparse.RawTextHelpFormatter\\n        )', 'kwargs.update(allow_abbrev=False, formatter_class=argparse.RawTextHelpFormatter); super().__init__(prog=prog, **kwargs)'))"
	@# Fix tokenmerge KeyError in command_highlight.py
	$(VENV_BIN)/python -c "import pathlib; f=next(pathlib.Path('$(VENV)').rglob('latexminted/command_highlight.py')); t=f.read_text(); f.write_text(t.replace('filter_opts[filter_name]', 'filter_opts.get(filter_name)'))"

$(LATEXMINTED): $(VENV_ACTIVATE)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(OUTPUTDIR):
	mkdir -p $(OUTPUTDIR)

$(GENDIR):
	mkdir -p $(GENDIR)

# Convert SVG to PDF
svg/%.pdf: svg/%.svg
	rsvg-convert -f pdf -o $@ $<

# Convert figures SVG to PDF in generated directory
$(GENDIR)/%.pdf: figures/%.svg | $(GENDIR)
	rsvg-convert -f pdf -o $@.tmp $< && \
	(pdfcrop $@.tmp $@ > /dev/null 2>&1 && rm $@.tmp || mv $@.tmp $@)

# Build PDF with venv in PATH for latexminted
$(BUILDDIR)/%.pdf: %.tex $(SVGPDFS) $(FIGPDFS) $(LATEXMINTED) | $(BUILDDIR)
	PATH="$(CURDIR)/$(VENV_BIN):$$PATH" pdflatex -shell-escape -output-directory=$(BUILDDIR) -interaction=nonstopmode $<
	PATH="$(CURDIR)/$(VENV_BIN):$$PATH" pdflatex -shell-escape -output-directory=$(BUILDDIR) -interaction=nonstopmode $<
	PATH="$(CURDIR)/$(VENV_BIN):$$PATH" pdflatex -shell-escape -output-directory=$(BUILDDIR) -interaction=nonstopmode $<

# Copy PDFs from build to output directory
# Use .SECONDARY to prevent deletion of intermediate build PDFs
.SECONDARY: $(PDFS)
$(OUTPUTDIR)/%.pdf: $(BUILDDIR)/%.pdf | $(OUTPUTDIR)
	@if [ ! -f "$<" ]; then \
		echo "Error: $< doesn't exist, but Make thinks it does. Run 'make clean' and try again."; \
		exit 1; \
	fi
	cp $< $@

clean:
	rm -rf $(BUILDDIR) $(OUTPUTDIR) $(GENDIR)
	rm -f *.pdf *.aux *.log *.nav *.out *.snm *.toc *.vrb

.PHONY: all clean
