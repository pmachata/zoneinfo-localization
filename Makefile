INSTALL= /usr/bin/install -c
INSTALL_PROGRAM= ${INSTALL}
INSTALL_DATA= ${INSTALL} -m 644
INSTALLNLSDIR=$(PREFIX)/share/locale

MSGMERGE = msgmerge

NLSPACKAGE = timezones

CATALOGS = $(shell ls *.po | sed 's/po/mo/')

#POTFILES  = ../timeconfig.c

all: $(NLSPACKAGE).pot $(CATALOGS)

$(NLSPACKAGE).pot:
	xgettext --default-domain=$(NLSPACKAGE) \
		--add-comments --keyword=_ --keyword=N_ $(POTFILES)
	echo >> $(NLSPACKAGE).po
	for a in `cd /usr/share/zoneinfo; find . -type f -or -type l | grep '^./[A-Z]' | egrep -v "(/right/)|(/posix/)" | sort | cut -d '/' -f 2- `; do printf "msgid \"%s\"\nmsgstr \"\"\n\n" $$a ; done >> $(NLSPACKAGE).po
	if cmp -s $(NLSPACKAGE).po $(NLSPACKAGE).pot; then \
	    rm -f $(NLSPACKAGE).po; \
	else \
	    mv $(NLSPACKAGE).po $(NLSPACKAGE).pot; \
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
	mkdir -p $(INSTROOT)/usr/share/locale
	for n in $(CATALOGS); do \
	    l=`basename $$n .mo`; \
	    $(INSTALL) -m 755 -d $(INSTROOT)/usr/share/locale/$$l; \
	    $(INSTALL) -m 755 -d $(INSTROOT)/usr/share/locale/$$l/LC_MESSAGES; \
	    if [ -f $$n ]; then \
	        $(INSTALL) -m 644 $$n $(INSTROOT)/usr/share/locale/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	    fi; \
	done

%.mo: %.po
	msgfmt -o $@ $<
