# Makefile to build all .tex files into the build directory

TEXFILES := $(wildcard *.tex)
BUILDDIR := build
OUTPUTDIR := output
PDFS := $(patsubst %.tex,$(BUILDDIR)/%.pdf,$(TEXFILES))
OUTPUT_PDFS := $(patsubst %.tex,$(OUTPUTDIR)/%.pdf,$(TEXFILES))
SVGFILES := $(wildcard svg/*.svg)
SVGPDFS := $(patsubst %.svg,%.pdf,$(SVGFILES))

all: $(BUILDDIR) $(OUTPUTDIR) $(SVGPDFS) $(PDFS) $(OUTPUT_PDFS)
	@# Clean up any PDFs that might have been generated in the main directory
	@rm -f *.pdf
	@rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(OUTPUTDIR):
	mkdir -p $(OUTPUTDIR)

# Convert SVG to PDF
svg/%.pdf: svg/%.svg
	inkscape --export-type=pdf --export-filename=$@ $< 2>/dev/null || \
	rsvg-convert -f pdf -o $@ $< 2>/dev/null || \
	(echo "Error: Neither inkscape nor rsvg-convert found. Please install one of them." && exit 1)

$(BUILDDIR)/%.pdf: %.tex $(SVGPDFS) | $(BUILDDIR)
	pdflatex -output-directory=$(BUILDDIR) -interaction=nonstopmode $<
	pdflatex -output-directory=$(BUILDDIR) -interaction=nonstopmode $<

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
	rm -rf $(BUILDDIR) $(OUTPUTDIR)
	rm -f *.pdf *.aux *.log *.nav *.out *.snm *.toc *.vrb

.PHONY: all clean
