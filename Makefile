NLSPACKAGE = timezones

PO_FILES := $(wildcard po/*.po)
LANGUAGES := $(PO_FILES:po/%.po=%)
TARGETS := $(LANGUAGES:%=gen/%.po)

MSGMERGE = msgmerge
PYTHON = python
TZDIR = tzdata

all: $(TARGETS)

po/$(NLSPACKAGE).h: src/harvest.py $(filter-out %.sh %.tab, $(wildcard $(TZDIR)/*))
	$(PYTHON) src/harvest.py $(TZDIR) > $@

po/$(NLSPACKAGE).pot: Makefile po/$(NLSPACKAGE).h
	cd po; \
	xgettext --default-domain=$(NLSPACKAGE) \
		--add-comments --keyword=C_:1c,2 --keyword=N_ $(NLSPACKAGE).h; \
	if cmp -s $(NLSPACKAGE).po $(NLSPACKAGE).pot; then \
		rm -f $(NLSPACKAGE).po; \
	else \
		mv $(NLSPACKAGE).po $(NLSPACKAGE).pot; \
	fi; \

po/%.po: TEMP_POT=$(@:%.po=%.pot)
po/%.po: po/$(NLSPACKAGE).pot
	if $(MSGMERGE) $@ $< > $(TEMP_POT) ; then \
		mv -f $(TEMP_POT) $@ ; \
		echo "$(MSGMERGE) of $* succeeded" ; \
	else \
		echo "$(MSGMERGE) of $* failed" ; \
		rm -f $(TEMP_POT) ; \
	fi

update-po: $(PO_FILES)

gen:
	mkdir gen

gen/%.po: po/%.po gen
	$(PYTHON) src/comp.py $< $@

gen/%.mo: gen/%.po
	msgfmt -o $@ $<

clean:
	-rm -f */*mo *~
	-rm -Rf gen
