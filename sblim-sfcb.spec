#
# $Id: sblim-sfcb.spec,v 1.5 2010/06/23 10:31:02 vcrhonek Exp $
#
# Package spec for sblim-sfcb
#

Name: sblim-sfcb
Summary: Small Footprint CIM Broker
URL: http://sblim.wiki.sourceforge.net/
Version: 1.3.16
Release: 11%{?dist}
Group: Applications/System
License: EPL
Source0: http://downloads.sourceforge.net/sblim/%{name}-%{version}.tar.bz2
Source1: sfcb.service
# Missing man pages
Source2: sfcbdump.1.gz
Source3: sfcbinst2mof.1.gz
Source4: sfcbtrace.1.gz
# Patch0: moves log close to correct place
Patch0: sblim-sfcb-1.3.7-close_logging.patch
# Patch1: changes schema location to the path we use
Patch1: sblim-sfcb-1.3.9-sfcbrepos-schema-location.patch
# Patch2: fixes CMGetCharPtr macro
Patch2: sblim-sfcb-1.3.10-CMGetCharPtr.patch
# Patch3: adds missing includes
Patch3: sblim-sfcb-1.3.14-missing-includes.patch
# Patch4: Fix provider debugging - variable for stopping wait-for-debugger
# loop must be volatile
Patch4: sblim-sfcb-1.3.15-fix-provider-debugging.patch
# Patch5-7: already upstream, http://sourceforge.net/p/sblim/sfcb-tix/37/
Patch5: sblim-sfcb-1.3.16-invalid-read.patch
Patch6: sblim-sfcb-1.3.16-invalid-read2.patch
Patch7: sblim-sfcb-1.3.16-embedded-crash.patch
# Patch8: already upstream, http://sourceforge.net/p/sblim/sfcb-tix/44/
Patch8: sblim-sfcb-1.3.16-escape.patch
# Patch9: already upstream, http://sourceforge.net/p/sblim/sfcb-tix/49/
Patch9: sblim-sfcb-1.3.16-embedded-instance.patch
# Patch10: increase default value of maxMsgLen in sfcb.cfg
Patch10: sblim-sfcb-1.3.16-maxMsgLen.patch
# Patch11: fixes sfcbmofpp segfaults if mof contains line with end of
#   block comment without line ending after it, accepted by upstream
Patch11: sblim-sfcb-1.3.16-mofpp-segfault.patch
# Patch12: fixes rhbz#1047781, backported from upstream
Patch12: sblim-sfcb-1.3.16-fix-logger-for-long-lived-clients.patch
# Patch13: fixes rhbz#1067842, multilib issue with man page and config file
Patch13: sblim-sfcb-1.3.16-multilib-man-cfg.patch
Provides: cim-server = 0
Requires: cim-schema
BuildRequires: libcurl-devel
BuildRequires: zlib-devel
BuildRequires: openssl-devel
BuildRequires: pam-devel
BuildRequires: cim-schema
BuildRequires: bison flex
BuildRequires: sblim-cmpi-devel
BuildRequires: systemd
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%Description
Small Footprint CIM Broker (sfcb) is a CIM server conforming to the
CIM Operations over HTTP protocol.
It is robust, with low resource consumption and therefore specifically 
suited for embedded and resource constrained environments.
sfcb supports providers written against the Common Manageability
Programming Interface (CMPI).

%prep
%setup -q -T -b 0 -n %{name}-%{version}
%patch0 -p1 -b .close_logging
%patch1 -p1 -b .sfcbrepos-schema-location
%patch2 -p1 -b .CMGetCharPtr
%patch3 -p1 -b .missing-includes
%patch4 -p1 -b .fix-provider-debugging
%patch5 -p1 -b .invalid-read
%patch6 -p1 -b .invalid-read2
%patch7 -p1 -b .embedded-crash
%patch8 -p1 -b .escape
%patch9 -p1 -b .embedded-instance
%patch10 -p1 -b .maxMsgLen
%patch11 -p1 -b .mofpp-segfault
%patch12 -p1 -b .fix-logger-for-long-lived-clients
%patch13 -p1 -b .multilib-man-cfg

%build
%configure --enable-debug --enable-uds --enable-ssl --enable-pam --enable-ipv6 CFLAGS="$CFLAGS -D_GNU_SOURCE -fPIE -DPIE" LDFLAGS="$LDFLAGS -Wl,-z,now -pie"
 
make 

%install
make DESTDIR=$RPM_BUILD_ROOT install
rm $RPM_BUILD_ROOT/%{_sysconfdir}/init.d/sfcb
mkdir -p $RPM_BUILD_ROOT/%{_unitdir}
install -p -m644 %{SOURCE1} $RPM_BUILD_ROOT/%{_unitdir}/sblim-sfcb.service
# install man pages
mkdir -p %{buildroot}/%{_mandir}/man1/
cp %{SOURCE2} %{SOURCE3} %{SOURCE4} %{buildroot}/%{_mandir}/man1/
# remove unused static libraries and so files
rm -f $RPM_BUILD_ROOT/%{_libdir}/sfcb/*.la

echo "%defattr(-,root,root,-)" > _pkg_list

find $RPM_BUILD_ROOT/%{_datadir}/sfcb -type f | grep -v $RPM_BUILD_ROOT/%{_datadir}/sfcb/CIM >> _pkg_list
sed -i s?$RPM_BUILD_ROOT??g _pkg_list > _pkg_list_2
echo "%config(noreplace) %{_sysconfdir}/sfcb/*" >> _pkg_list
echo "%config(noreplace) %{_sysconfdir}/pam.d/*" >> _pkg_list
echo "%doc %{_datadir}/doc/*" >> _pkg_list
echo "%{_datadir}/man/man1/*" >> _pkg_list
echo "%{_unitdir}/sblim-sfcb.service" >> _pkg_list
echo "%{_localstatedir}/lib/sfcb" >> _pkg_list
echo "%{_bindir}/*" >> _pkg_list
echo "%{_sbindir}/*" >> _pkg_list
echo "%{_libdir}/sfcb/*.so.*" >> _pkg_list
echo "%{_libdir}/sfcb/*.so" >> _pkg_list

cat _pkg_list

%pre
/usr/bin/getent group sfcb >/dev/null || /usr/sbin/groupadd -r sfcb
/usr/sbin/usermod -a -G sfcb root > /dev/null 2>&1 || :

%post 
%{_datadir}/sfcb/genSslCert.sh %{_sysconfdir}/sfcb &>/dev/null || :
/sbin/ldconfig
%{_bindir}/sfcbrepos -f
%systemd_post sfcb.service

%preun
%systemd_preun sfcb.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart sfcb.service
if [ $1 -eq 0 ]; then
        /usr/sbin/groupdel sfcb > /dev/null 2>&1 || :;
fi;

%files -f _pkg_list

%changelog
* Tue Mar 04 2014 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-11
- Fix connection fails to openwsman with sfcbLocal frontend
  Resolves: #1047781
- Fix multilib issue with man page and config file
  Resolves: #1067842

* Mon Feb 10 2014 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-10
- Fix sfcbmofpp segfault
  Resolves: #1061749

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 1.3.16-9
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1.3.16-8
- Mass rebuild 2013-12-27

* Tue Oct 15 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-7
- Add version to cim-server virtual provides
  Resolves: #1018739

* Tue Aug 13 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-6
- Build require systemd for unitdir macro
  Resolves: #996119

* Mon Jun 24 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-5
- Increase default maxMsgLen
  Resolves: #967940

* Mon Jun 17 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-4
- Create missing man pages
- Add support for EmbeddedInstance qualifier
  Resolves: #919377

* Mon May 20 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-3
- Fix indCIMXmlHandler crash in IndCIMXMLHandlerInvokeMethod with Embedded Instances 
  Resolves: #957747
- Fix sfcb creates invalid XML with embedded object inside embedded object
  Resolves: #957742

* Tue Jan 29 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-2
- Fix URL in the spec file
- Remove unused devel part from the spec file
- Full relro support

* Tue Jan 08 2013 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.16-1
- Update to sblim-sfcb-1.3.16
- Fix provider debugging (patch by Radek Novacek)

* Thu Nov 29 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.15-5
- Comment patches

* Thu Sep 06 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.15-4
- Fix issues found by fedora-review utility in the spec file

* Thu Aug 23 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.15-3
- Use new systemd-rpm macros
  Resolves: #850307

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.15-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 19 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.15-1
- Update to sblim-sfcb-1.3.15

* Thu Jun 07 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.14-2
- Remove SysV init script

* Wed Apr 04 2012 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.14-1
- Update to sblim-sfcb-1.3.14

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct 12 2011 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.13-1
- Update to sblim-sfcb-1.3.13

* Wed Sep 07 2011 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.12-1
- Update to sblim-sfcb-1.3.12

* Wed Jun 15 2011 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.11-2
- Remove sfcb system group in post uninstall scriptlet
- Fix minor rpmlint warnings

* Thu May 26 2011 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.11-1
- Update to sblim-sfcb-1.3.11

* Mon May  9 2011 Bill Nottingham - 1.3.10-5
- fix systemd scriptlets for upgrade

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org>
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan  7 2011 Praveen K Paladugu <praveen_paladugu@dell.com> - 1.3.10-3
- Added the required scripting to manage the service with systemd

* Fri Jan  7 2011 Praveen K Paladugu <praveen_paladugu@dell.com> - 1.3.10-2
- Following the BZ#660072, added sfcb.service file for compliance with systemd
- Since sfcb's PAM authentication requires, the user to be in group sfcb, 
-    added the root user to "sfcb" group in %%pre section.

* Mon Dec  6 2010 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.10-1
- Update to sblim-sfcb-1.3.10
- Fix CMGetCharPtr macro (patch by Kamil Dudka)

* Mon Sep  6 2010 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.9-1
- Update to sblim-sfcb-1.3.9
- Compile with --enable-uds, i. e. enable unix domain socket local
  connect functionality
- Create sfcb system group (used by basic authentication with PAM)
  in pre install scriptlet
- Fix default location where sfcbrepos is looking for schema files
  and simplify sfcbrepos command in post install sciptlet
- Add missing soname files

* Wed Jun 23 2010 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.8-1
- Update to sblim-sfcb-1.3.8
- Fix unmatched calls of closeLogging() and startLogging()

* Thu Apr 22 2010 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.7-3
- Fix initscript

* Mon Mar 22 2010 Vitezslav Crhonek <vcrhonek@redhat.com> - 1.3.7-2
- Make sblim-sfcb post install scriptlet silent
- Fix value.c

* Wed Mar  3 2010 <vcrhonek@redhat.com> - 1.3.7-1
- Update to sblim-sfcb-1.3.7
- Fix dist tag in Release field

* Tue Sep 22 2009 <srinivas_ramanatha@dell.com> - 1.3.4-8
- Removed the devel package and moved the init script to right directory

* Wed Sep 16 2009 <srinivas_ramanatha@dell.com> - 1.3.4-7
- Modified the spec based on Praveen's comments

* Thu Sep 10 2009 <srinivas_ramanatha@dell.com> - 1.3.4-6
- Fixed the incoherent init script problem by renaming the init script

* Thu Sep 03 2009 <srinivas_ramanatha@dell.com> - 1.3.4-5
- added the devel package to fit in all the development files 
- Made changes to the initscript not to start the service by default

* Thu Jul 02 2009 <ratliff@austin.ibm.com> - 1.3.4-4
- added build requires for flex, bison, cim-schema suggested by Sean Swehla
- added sfcbrepos directive to post section

* Thu Jun 18 2009 <ratliff@austin.ibm.com> - 1.3.4-3
- re-ordered the top so that the name comes first
- added the la files to the package list
- removed the smp flags from make because that causes a build break
- updated spec file to remove schema and require the cim-schema package
- change provides statement to cim-server as suggested by Matt Domsch
- updated to upstream version 1.3.4 which was released Jun 15 2009

* Thu Oct 09 2008 <ratliff@austin.ibm.com> - 1.3.2-2
- updated spec file based on comments from Srini Ramanatha as below:
- updated the Release line to add dist to be consistent with sblim-sfcc
- updated the source URL

* Wed Oct 08 2008 <ratliff@austin.ibm.com> - 1.3.2-1
- updated upstream version and added CFLAGS to configure to work 
- around http://sources.redhat.com/bugzilla/show_bug.cgi?id=6545

* Fri Aug 08 2008 <ratliff@austin.ibm.com> - 1.3.0-1
- updated buildrequires to require libcurl-devel rather than curl-devel
- removed requires to allow rpm to automatically generate the requires
- removed echo to stdout
- removed paranoia check around cleaning BuildRoot per Fedora MUST requirements
- changed group to supress rpmlint complaint
- added chkconfig to enable sfcb by default when it is installed
- added patch0 to enable 1.3.0 to build on Fedora 9

* Fri Feb 09 2007  <mihajlov@dyn-9-152-143-45.boeblingen.de.ibm.com> - 1.2.1-0
- Updated for 1.2.1 content, enabled SSL, indications

* Wed Aug 31 2005  <mihajlov@dyn-9-152-143-45.boeblingen.de.ibm.com> - 0.9.0b-0
- Support for man pages added
