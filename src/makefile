#
# @author Jean-Lou Dupont
#
#
PRJ=rb_squeezebox
PKG=squeezebox

PYTHON=`which python`
RBP=/usr/lib/rhythmbox/plugins

all:
	@echo "make install"
	@echo "make clean"
	@echo "make buildsrc"

clean:
	@rm -f $(DESTDIR)$(RBP)/$(PKG)/*.pyc
		
install:
	@install -d $(DESTDIR)$(RBP)/$(PKG)
	@install -d $(DESTDIR)$(RBP)/$(PKG)/agents
	@install -d $(DESTDIR)$(RBP)/$(PKG)/helpers
	@install -d $(DESTDIR)$(RBP)/$(PKG)/system
	
	@install -D $(CURDIR)/$(PKG)/*.py                  $(DESTDIR)$(RBP)/$(PKG)/
	@install -D $(CURDIR)/$(PKG)/agents/*.py           $(DESTDIR)$(RBP)/$(PKG)/agents
	@install -D $(CURDIR)/$(PKG)/helpers/*.py          $(DESTDIR)$(RBP)/$(PKG)/helpers
	@install -D $(CURDIR)/$(PKG)/system/*.py           $(DESTDIR)$(RBP)/$(PKG)/system
	
	#@install -D $(CURDIR)/$(PKG)/*.glade               $(DESTDIR)$(RBP)/$(PKG)/	
	@install -D $(CURDIR)/$(PKG)/$(PKG).rb-plugin      $(DESTDIR)$(RBP)/$(PKG)/$(PKG).rb-plugin
	@python -m compileall ${DESTDIR}$(RBP)/$(PKG)
	
buildsrc:
	debuild -S