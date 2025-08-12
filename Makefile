# Makefile to build all .tex files into the build directory

TEXFILES := $(wildcard *.tex)
BUILDDIR := build
PDFS := $(patsubst %.tex,$(BUILDDIR)/%.pdf,$(TEXFILES))
SVGFILES := $(wildcard svg/*.svg)
SVGPDFS := $(patsubst %.svg,%.pdf,$(SVGFILES))

all: $(BUILDDIR) $(SVGPDFS) $(PDFS)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Convert SVG to PDF
svg/%.pdf: svg/%.svg
	inkscape --export-type=pdf --export-filename=$@ $< 2>/dev/null || \
	rsvg-convert -f pdf -o $@ $< 2>/dev/null || \
	(echo "Error: Neither inkscape nor rsvg-convert found. Please install one of them." && exit 1)

$(BUILDDIR)/%.pdf: %.tex $(SVGPDFS) | $(BUILDDIR)
	pdflatex -output-directory=$(BUILDDIR) $<

clean:
	rm -rf $(BUILDDIR)

.PHONY: all clean
