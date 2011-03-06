#
# @author Jean-Lou Dupont
#  http://www.systemical.com/
#
# Makefile for releasing the project
#

## <<< CUSTOMIZE HERE
PRJ=rb_squeezebox
PKG=rb-squeezebox
DOC=http:\/\/www.systemical.com\/doc\/opensource\/rb_squeezebox
## >>>

VERSION:=`cat VERSION`
DATE=`date +'%a, %d %B %Y %T %z'`

DEFAULT_DISTRO=maverick

ifeq ($(DIST),)
	DIST=${DEFAULT_DISTRO}
endif

all:
	@echo "Version: ${VERSION}"
	@echo "Options:"
	@echo "  clean, orig"
	@echo "  ppa, pb, up"

clean:
	@echo "Cleaning - Version: ${VERSION}"
	@rm -r -f /tmp/$(PRJ)
	
orig:
	@echo "Cleaning - Version: ${VERSION}"
	@rm -r -f /tmp/$(PRJ)

	@echo "* Preparing for packaging -- Version: ${VERSION}, Distribution: ${DIST}"
	@echo "-------------------------"
	@echo ""
	@echo "mkdir directories ( /tmp/$(PRJ)/${DIST}/$(PRJ)-$(VERSION) )"
	@mkdir -p "/tmp/$(PRJ)/${DIST}"
	@mkdir -p "/tmp/$(PRJ)/${DIST}/$(PRJ)-$(VERSION)"
	
	@echo "Copying package folder"
	@rsync -r --exclude=*.git* src/ "/tmp/$(PRJ)/${DIST}/$(PRJ)-$(VERSION)"

	@echo "Copying debian folder"
	@rsync -r --exclude=*.svn* packages/debian "/tmp/$(PRJ)/${DIST}/$(PRJ)-$(VERSION)"
	@echo "Copying packaging makefile"
	@cp makefile "/tmp/$(PRJ)/${DIST}/makefile"
	@cp VERSION "/tmp/$(PRJ)/${DIST}/VERSION"
		
	@echo "Adjusting debian/changelog to DIST & VERSION"
	@cat packages/debian/changelog | sed "s/_DIST_/${DIST}/g" | sed "s/_VERSION_/${VERSION}/g" | sed "s/_PRJ_/${PRJ}/g" | sed "s/_DATE_/${DATE}/g" > "/tmp/${PRJ}/${DIST}/${PRJ}-${VERSION}/debian/changelog"

	@echo "Adjusting debian/control to DIST & VERSION"
	@cat packages/debian/control   | sed "s/_DIST_/${DIST}/g" | sed "s/_VERSION_/${VERSION}/g" | sed "s/_PRJ_/${PRJ}/g" | sed "s/_PKG_/${PKG}/g" | sed "s/_DOC_/${DOC}/g" | sed "s/_DATE_/${DATE}/g" > "/tmp/${PRJ}/${DIST}/${PRJ}-${VERSION}/debian/control"		
	
	@echo "** SUCCESS: folder ready: /tmp/$(PRJ)/${DIST}"
	@echo "*** DON'T FORGET TO UPDATE debian/changelog ***"

	@echo "!!! Have you updated debian/changelog ?"

	@echo "Running 'debuild'"
	@cd "/tmp/$(PRJ)/${DIST}/$(PRJ)-$(VERSION)" && debuild -S
	
up:
	@echo "UPLOADING TO PPA"
	@cd "/tmp/$(PRJ)/${DIST}/" && dput ppa:jldupont/jldupont *.changes


pb:
	@echo " ----------------------------- "
	@echo " RUNNING PBUILDER "
	@cd "/tmp/$(PRJ)/${DIST}/" && sudo DIST=${DIST} pbuilder build *.dsc

.PHONY: orig pb
