INSTALL= /usr/bin/install -c
INSTALL_PROGRAM= ${INSTALL}
INSTALL_DATA= ${INSTALL} -m 644
INSTALLNLSDIR=$(PREFIX)/share/locale

MSGMERGE = msgmerge

NLSPACKAGE = timezones

CATALOGS = $(shell ls *.po | sed 's/po/mo/')

POTFILES  = $(NLSPACKAGE).h

all: $(NLSPACKAGE).pot $(CATALOGS)

$(NLSPACKAGE).pot::
	cp -dpf $(NLSPACKAGE) $(NLSPACKAGE).new
	chmod u+rw $(NLSPACKAGE).new
	for tzfile in `cd /usr/share/zoneinfo; find . -type f -or -type l | grep '^./[A-Z]' | egrep -v "(/right/)|(/posix/)" | sort | cut -d '/' -f 2- `; do \
		echo "$$tzfile"; \
	done | while read tz; do \
		if ! fgrep -x -q "$$tz" $(NLSPACKAGE); then \
			echo "$$tz"; \
		fi; \
	done >> $(NLSPACKAGE).new
	sort -u $(NLSPACKAGE).new > $(NLSPACKAGE).new.new
	mv -f $(NLSPACKAGE).new.new $(NLSPACKAGE).new
	if ! cmp -s $(NLSPACKAGE) $(NLSPACKAGE).new; then \
		mv $(NLSPACKAGE).new $(NLSPACKAGE); \
		for tz in `cat $(NLSPACKAGE)`; do \
			echo "N_(\"$$tz\");"; \
		done > timezones.h; \
		xgettext --default-domain=$(NLSPACKAGE) \
			--add-comments --keyword=_ --keyword=N_ $(POTFILES); \
		if cmp -s $(NLSPACKAGE).po $(NLSPACKAGE).pot; then \
	    	rm -f $(NLSPACKAGE).po; \
		else \
	    	mv $(NLSPACKAGE).po $(NLSPACKAGE).pot; \
		fi; \
	else \
		rm -f $(NLSPACKAGE).new; \
	fi

update-po: Makefile
	$(MAKE) $(NLSPACKAGE).pot
	catalogs='$(CATALOGS)'; \
	for cat in $$catalogs; do \
		lang=`echo $$cat | sed 's/.mo//'`; \
		if $(MSGMERGE) $$lang.po $(NLSPACKAGE).pot > $$lang.pot ; then \
			mv -f $$lang.pot $$lang.po ; \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi \
	done

refresh-po: Makefile
	catalogs='$(CATALOGS)'; \
	for cat in $$catalogs; do \
		lang=`echo $$cat | sed 's/.mo//'`; \
		if $(MSGMERGE) $$lang.po $(NLSPACKAGE).pot > $$lang.pot ; then \
			mv -f $$lang.pot $$lang.po ; \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi \
	done

clean:
#	rm -f *mo $(NLSPACKAGE).pot *~
	rm -f *mo *~

distclean: clean
	rm -f .depend Makefile

depend:

install: $(CATALOGS)
	mkdir -p $(DESTDIR)/usr/share/locale
	for n in $(CATALOGS); do \
	    l=`basename $$n .mo`; \
	    $(INSTALL) -m 755 -d $(DESTDIR)/usr/share/locale/$$l; \
	    $(INSTALL) -m 755 -d $(DESTDIR)/usr/share/locale/$$l/LC_MESSAGES; \
	    if [ -f $$n ]; then \
	        $(INSTALL) -m 644 $$n $(DESTDIR)/usr/share/locale/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	    fi; \
	done

%.mo: %.po
	msgfmt -o $@ $<

MSGCONV=msgconv -t utf-8

force-utf8:
	@catalogs='$(CATALOGS)'; \
	for cat in $$catalogs; do \
		lang=`echo $$cat | sed 's/.mo//'`; \
		if $(MSGCONV) $$lang.po > $$lang.po.utf8 ; then \
			mv -f $$lang.po.utf8 $$lang.po ; \
			echo "$(MSGCONV) of $$lang succeeded" ; \
		else \
			echo "$(MSGCONV) of $$lang failed" ; \
			rm -f $$lang.po.utf8 ; \
		fi \
	done

report:
	@catalogs='$(CATALOGS)'; \
	for cat in $$catalogs; do \
		lang=`echo $$cat | sed 's/.mo//'`; \
		echo -n "$$lang.po: " ; \
		msgfmt --statistics -o /dev/null $$lang.po ; \
	done
