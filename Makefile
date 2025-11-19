# Makefile to build all .tex files into the build directory

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

$(BUILDDIR)/%.pdf: %.tex $(SVGPDFS) $(FIGPDFS) | $(BUILDDIR)
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
	rm -rf $(BUILDDIR) $(OUTPUTDIR) $(GENDIR)
	rm -f *.pdf *.aux *.log *.nav *.out *.snm *.toc *.vrb

.PHONY: all clean
