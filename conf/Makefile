sysconfdir ?= /etc/asl-usage
prefix ?= /usr
docdir ?= $(prefix)/share/doc/asl-usage

CONF_FILES = $(filter-out Makefile tmp , $(wildcard *))
CONF_INSTALLABLES = $(patsubst %, $(DESTDIR)$(sysconfdir)/%, $(CONF_FILES))
CONF_DOCABLES = $(patsubst %, $(DESTDIR)$(docdir)/%, $(CONF_FILES))

INSTALLABLES = $(CONF_INSTALLABLES) $(CONF_DOCABLES) 

.PHONY:	install
install:	$(INSTALLABLES)

$(DESTDIR)$(sysconfdir)/users:	users
	install -D -m 0640 $< $@

$(DESTDIR)$(sysconfdir)/%: %
	install -D -m 0644  $< $@

$(DESTDIR)$(docdir)/%: %
	install -D -m 0644  $< $@


