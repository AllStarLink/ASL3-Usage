#
# Build variables
#
SRCNAME 	= ASL3-Usage
PKGNAME		= asl-usage
RELVER 		= 1.1.0
DEBVER 		= 1
RELPLAT		?= deb$(shell lsb_release -rs 2> /dev/null)

prefix		?= /usr
docdir		?= $(prefix)/share/doc/$(PKGNAME)


BUILDABLES = \
	src 

instconf ?= yes
ifeq ($(instconf),yes)
BUILDABLES += conf
endif

ifdef DESTDIR
FULL_DESTDIR = $(shell readlink -f $(DESTDIR))
endif

ROOT_FILES = LICENSE README.md aslusage.sql
ROOT_INSTALLABLES = $(patsubst %, $(FULL_DESTDIR)$(docdir)/%, $(ROOT_FILES))

default:
	@echo This does nothing because of dpkg-buildpkg - use 'make install'

install: $(ROOT_INSTALLABLES)
	@echo FULL_DESTDIR=$(FULL_DESTDIR)
	@echo ROOT_INSTALLABLES=$(ROOT_INSTALLABLES)
	$(foreach dir, $(BUILDABLES), $(MAKE) -C $(dir) install DESTDIR=$(FULL_DESTDIR);)

$(FULL_DESTDIR)$(docdir)/%: %
	install -D -m 0644  $< $@

verset:
	perl -pi -e 's/\@\@HEAD-DEVELOP\@\@/$(RELVER)/g' `grep -rl @@HEAD-DEVELOP@@ src/`

deb:	debclean debprep
	debchange --distribution stable --package $(PKGNAME) \
		--newversion $(EPOCHVER)$(RELVER)-$(DEBVER).$(RELPLAT) \
		"Autobuild of $(EPOCHVER)$(RELVER)-$(DEBVER) for $(RELPLAT)"
	dpkg-buildpackage -b 
	git checkout debian/changelog

debchange:
	debchange -v $(RELVER)-$(DEBVER)
	debchange -r

debprep:	debclean
	(cd .. && \
		rm -f $(PKGNAME)-$(RELVER) && \
		rm -f $(PKGNAME)-$(RELVER).tar.gz && \
		rm -f $(PKGNAME)_$(RELVER).orig.tar.gz && \
		ln -s $(SRCNAME) $(PKGNAME)-$(RELVER) && \
		tar --exclude=".git" -h -zvcf $(PKGNAME)-$(RELVER).tar.gz $(PKGNAME)-$(RELVER) && \
		ln -s $(PKGNAME)-$(RELVER).tar.gz $(PKGNAME)_$(RELVER).orig.tar.gz )

debclean:
	rm -f ../$(PKGNAME)_$(RELVER)*
	rm -f ../$(PKGNAME)-$(RELVER)*
	rm -rf debian/$(PKGNAME)
	rm -f debian/files
	rm -rf debian/.debhelper/
	rm -f debian/debhelper-build-stamp
	rm -f debian/*.substvars
	rm -rf debian/$(SRCNAME)/ debian/.debhelper/
	rm -f debian/debhelper-build-stamp debian/files debian/$(SRCNAME).substvars
	rm -f debian/*.debhelper debian/*.debhelper.log
	

