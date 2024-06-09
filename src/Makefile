prefix ?= /usr
exec_prefix ?= $(prefix)
bin_prefix ?= $(exec_prefix)/bin
pylibdir ?= $(exec_prefix)/lib/python3/dist-packages
mandir ?= $(prefix)/share/man

BINS = $(filter-out Makefile $(wildcard *.md) asl_usage tmp, $(wildcard *))
BINS_EXP = $(patsubst %, $(DESTDIR)$(bin_prefix)/%, $(BINS))

MANS_SRC = $(wildcard *.1.md)
MANS_EXP = $(patsubst %.md, $(DESTDIR)$(mandir)/man1/%, $(MANS_SRC))

PY_SRC = $(wildcard asl_usage/*/__init__.py)
PY_EXP = $(patsubst %, $(DESTDIR)$(pylibdir)/%, $(PY_SRC))

showpy:
	echo $(PY_EXP)

install: $(BINS_EXP) $(MANS_EXP) $(PY_EXP)

mans:	$(MANS_EXP)

$(DESTDIR)$(bin_prefix)/%:	%
	install -D -m 0755 $< $@

$(DESTDIR)$(mandir)/man1/%:	%.md
	mkdir -p $(DESTDIR)$(mandir)/man1
	pandoc $< -s -t man > $@

$(DESTDIR)$(pylibdir)/%:	%
	install -D -m 0644 $< $@	
