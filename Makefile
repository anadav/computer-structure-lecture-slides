# Makefile to build all .tex files into the build directory

TEXFILES := $(wildcard *.tex)
BUILDDIR := build
PDFS := $(patsubst %.tex,$(BUILDDIR)/%.pdf,$(TEXFILES))

all: $(BUILDDIR) $(PDFS)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(BUILDDIR)/%.pdf: %.tex | $(BUILDDIR)
	pdflatex -output-directory=$(BUILDDIR) $<

clean:
	rm -rf $(BUILDDIR)

.PHONY: all clean
