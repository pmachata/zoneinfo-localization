LANGUAGES := $(wildcard po/*.po)
TARGETS := $(LANGUAGES:po/%=gen/%)
PYTHON = python

all: $(TARGETS)

gen:
	mkdir gen

gen/%.po: po/%.po gen
	$(PYTHON) src/comp.py $< > $@
