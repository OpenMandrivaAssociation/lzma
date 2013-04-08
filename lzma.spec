%define oldlzmaver 4.32.7
%define major 0
%define libname %mklibname lzmadec %{major}
%define libdev %mklibname -d lzmadec

Summary:	LZMA utils
Name:		lzma
Version:	4.43
Release:	33
License:	GPL
Group:		Archiving/Compression
URL:		http://tukaani.org/lzma/
Source0:	http://tukaani.org/lzma/lzma-%{oldlzmaver}.tar.lzma
Source1:	http://ovh.dl.sourceforge.net/sourceforge/sevenzip/lzma443.tar.bz2
Source3:	sqlzma.h
# (blino) modified for 443, from sqlzma1-449.patch:
#   * adapted to lzma443 dist structure: s,/C/Compress/Lzma/,/C/7zip/Compress/LZMA_C/,; s,/CPP/7zip/Compress/LZMA_Alone/,/C/7zip/Compress/LZMA_Alone/,
#   * use sqlzma.mk makefiles for 443 (from from sqlzma1-443.patch)
#   * remove NCoderPropID::kNumThreads in comp.cc, it is invalid since we don't build LZMAEncoder.cpp with COMPRESS_MF_MT multithread support
Patch3:		lzma-4.32.4-sqlzma.patch

Patch4:		lzma-4.43-add-missing-header.patch
Patch5:		lzma-4.43-quiet.patch
Patch6:		lzma-4.43-update-version.patch
Patch7:		lzma-4.43-fix-fast-compression.patch
Patch8:		lzma-4.43-add-missing-gethandle.patch
Patch9:		lzma-4.32.4-text-tune.patch
# 4.32.2 has changes to sdk that we replace with newer, we apply these to the new
Patch12:	lzma-4.32.2-sdk-changes.patch
Patch16:	lzma-4.32.7-format_not_a_string_literal_and_no_format_arguments.diff
# for squashfs-lzma library
Patch17:	lzma-aarch64.patch
BuildRequires:	zlib-devel
BuildRequires:	dos2unix
BuildRequires:	diffutils

%description
LZMA provides very high compression ratio and fast decompression. The
core of the LZMA utils is Igor Pavlov's LZMA SDK containing the actual
LZMA encoder/decoder. LZMA utils add a few scripts which provide
gzip-like command line interface and a couple of other LZMA related
tools. Also provides:

- Average compression ratio 30% better than that of gzip and 15%
  better than that of bzip2.

- Decompression speed is only little slower than that of gzip, being
  two to five times faster than bzip2.

- In fast mode, compresses faster than bzip2 with a comparable
  compression ratio.

- Achieving the best compression ratios takes four to even twelve
  times longer than with bzip2. However. this doesn't affect
  decompressing speed.

- Very similar command line interface than what gzip and bzip2 have.

%package -n	%{libname}
Summary:	Libraries for decoding LZMA compression
Group:		System/Libraries
License:	LGPL
Provides:	%{_lib}%{name}%{major} = %{version}-%{release}

%description -n	%{libname}
Libraries for decoding LZMA compression.

%package -n	%{libdev}
Summary:	Devel libraries & headers for liblzmadec
Group:		Development/C
License:	LGPL
Provides:	liblzmadec-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}

%description -n %{libdev}
Devel libraries & headers for liblzmadec.

%package -n	dkms-%{name}
Summary:	Kernel modules for decoding LZMA compression
Group:		System/Kernel and hardware
License:	GPL
Requires(post):	dkms
Requires(preun):	dkms

%description -n	dkms-%{name}
Kernel modules for decoding LZMA compression.

%prep
%setup -q -n %{name}-%{oldlzmaver} -a1
%patch3 -p1 -b .sqlzma
cp %{SOURCE3} .
dos2unix *.txt

# ugly syncing with latest sdk
mv src/sdk src/sdk.old
cp -r C src/sdk
for i in `find src/sdk.old -name Makefile.\*`; do
	cp $i `echo $i|sed -e 's#sdk.old#sdk#g'`;
done

find src/sdk -name makefile|xargs rm -f

%patch4 -p1 -b .config_h
%patch5 -p1 -b .quiet
%patch6 -p0 -b .version
%patch7 -p0 -b .fast
%patch8 -p0 -b .gethandle
%patch9 -p1 -b .text
%patch12 -p1 -b .4.32.2
%patch16 -p1 -b .format_not_a_string_literal_and_no_format_arguments
%patch17 -p1 -b .aarch64

pushd C/7zip/Compress/LZMA_C
cp %{SOURCE3} kmod/
cp uncomp.c LzmaDecode.{c,h} LzmaTypes.h kmod/
perl -pi -e 's,^#include "\.\./(Lzma.*)",#include "$1",' kmod/*.{c,h}
cat > kmod/dkms.conf <<EOF
PACKAGE_NAME=%{name}
PACKAGE_VERSION=%{version}-%{release}
DEST_MODULE_LOCATION[0]="/kernel/lib/%{name}"
DEST_MODULE_LOCATION[1]="/kernel/lib/%{name}"
BUILT_MODULE_NAME[0]="sqlzma"
BUILT_MODULE_NAME[1]="unlzma"
AUTOINSTALL=yes
EOF
popd

%build
CFLAGS="%{optflags} -D_FILE_OFFSET_BITS=64 -O3" \
CXXFLAGS="%{optflags} -D_FILE_OFFSET_BITS=64 -O3" \
%configure2_5x
%make
%make CFLAGS="%{optflags} -c -Wall -pedantic -D _LZMA_PROB32  -DNDEBUG -include pthread.h -I../../../.." -C C/7zip/Compress/LZMA_C -f sqlzma.mk Sqlzma=../../../..
%make CFLAGS="%{optflags} -c -I ../../../" -C C/7zip/Compress/LZMA_Alone -f sqlzma.mk Sqlzma=../../../..

%install
rm -rf %{buildroot}
%makeinstall_std

install C/7zip/Compress/LZMA_*/*.a %{buildroot}%{_libdir}

mkdir -p %{buildroot}/usr/src/%{name}-%{version}-%{release}/
tar c -C C/7zip/Compress/LZMA_C/kmod . | tar x -C %{buildroot}/usr/src/%{name}-%{version}-%{release}/

rm -rf %{buildroot}{%{_bindir},%{_mandir}}

%check
make check

%post -n dkms-%{name}
set -x
/usr/sbin/dkms --rpm_safe_upgrade add -m %{name} -v %{version}-%{release}
/usr/sbin/dkms --rpm_safe_upgrade build -m %{name} -v %{version}-%{release}
/usr/sbin/dkms --rpm_safe_upgrade install -m %{name} -v %{version}-%{release}
:

%preun -n dkms-%{name}
set -x
/usr/sbin/dkms --rpm_safe_upgrade remove -m %{name} -v %{version}-%{release} --all
:

%files -n %{libname}
%{_libdir}/lib*.so.*

%files -n %{libdev}
%doc *.txt
%{_includedir}/*.h
%{_libdir}/*.so
%{_libdir}/*.a

%files -n dkms-%{name}
/usr/src/%{name}-%{version}-%{release}


%changelog
* Wed May 04 2011 Oden Eriksson <oeriksson@mandriva.com> 4.43-31mdv2011.0
+ Revision: 666119
- mass rebuild

* Fri Dec 03 2010 Oden Eriksson <oeriksson@mandriva.com> 4.43-30mdv2011.0
+ Revision: 606452
- rebuild

* Sun Mar 14 2010 Oden Eriksson <oeriksson@mandriva.com> 4.43-29mdv2010.1
+ Revision: 519035
- rebuild

* Thu Sep 03 2009 Christophe Fergeau <cfergeau@mandriva.com> 4.43-28mdv2010.0
+ Revision: 426022
- rebuild

* Fri Feb 27 2009 Olivier Blin <oblin@mandriva.com> 4.43-27mdv2009.1
+ Revision: 345446
- require dkms for dkms subpackage post scripts (fix installation in iurt chroot)

* Tue Dec 30 2008 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-26mdv2009.1
+ Revision: 321390
- ditch lzma util since it's now obsoleted by new xz util

* Sun Dec 21 2008 Oden Eriksson <oeriksson@mandriva.com> 4.43-25mdv2009.1
+ Revision: 317045
- fix build with -Werror=format-security (P16)

* Mon Aug 04 2008 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-24mdv2009.0
+ Revision: 262910
- update to lzma utils 4.32.7

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers

* Thu Apr 24 2008 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-23mdv2009.0
+ Revision: 197102
- rename library package to name consistent with library name (to
  make room for new liblzma from new lzma utils)

* Tue Apr 15 2008 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-22mdv2009.0
+ Revision: 194317
- fix deprecated string conversion (P15 from OpenSuSE)
- build lzma utils with -O3
- add diffutils to buildrequires (needed by test suite)
- switch to new lzma tarball from upstream

* Mon Jan 28 2008 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-21mdv2008.1
+ Revision: 159136
- lzma utils updated to 4.32.5
- use zcat in stead of gzcat in lzme (tv)

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Wed Dec 12 2007 Olivier Blin <oblin@mandriva.com> 4.43-20mdv2008.1
+ Revision: 119008
- fix sqlzma patch to really use lzma instead of zlib when possible, by not passing invalid multithread option since multithread support is disabled
- merge additional sqlzma makefiles in main sqlzma patch
- regenerate sqlzma patch with gendiff

* Wed Dec 12 2007 Olivier Blin <oblin@mandriva.com> 4.43-19mdv2008.1
+ Revision: 118764
- update sqlzma patch and header to be in sync with squashfs-tools (with workarounds to build with lzma443)

* Mon Dec 10 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-18mdv2008.1
+ Revision: 117014
- new release: lzma utils 4.32.6
- rediff text tune patch (P9)
- drop liblzmadec fix patch (P14, merged upstream)
- bashism in script requires bash as interpreter for lzme, also fix to
  work with BSD 'du' (thx to Anders F Bj?\195?\182rklund)

* Mon Dec 03 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-17mdv2008.1
+ Revision: 114648
- fix a bug in liblzmadec that could lead to crashes with KDE (P14)

* Fri Nov 30 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-16mdv2008.1
+ Revision: 114105
- update to lzma utils 4.32.3
- compile all with %%{optflags}
- run checks

  + Thierry Vignaud <tv@mandriva.org>
    - description is not about _patches_ on _anoter_ package

* Wed Nov 14 2007 Olivier Blin <oblin@mandriva.com> 4.43-15mdv2008.1
+ Revision: 108859
- build dkms-lzma
- run ldconfig in post/postun of library package

* Mon Nov 05 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 4.43-14mdv2008.1
+ Revision: 106110
- Added patch from Andrey Borzenkov that fixes #35309 (lzma always
  creates output with 0600 permissions).

* Sat Oct 27 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-13mdv2008.1
+ Revision: 102612
- update lzma utils to 4.32.2 (P12 is to sync newer sdk with changes to the
  old shipped with 4.32.2)
- drop P11 (merged upstream)
- fix include of sys/types.h in lzmadec.h for build without stdio (P11)

* Tue Jul 24 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-12mdv2008.0
+ Revision: 54873
- update to lzma utils 4.32.0beta4
- drop P10 (merged upstream)

* Mon Jul 23 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-11mdv2008.0
+ Revision: 54869
- fix output to stdout (P11, fixes #32058)

* Fri Jun 22 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-10mdv2008.0
+ Revision: 43072
- add special tuning for text files, parameter: '--text' (P9)

* Sun Jun 10 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-9mdv2008.0
+ Revision: 37873
- put back library as some tools provided relying on it still migth be of
  interest for some

* Sun Jun 10 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-7mdv2008.0
+ Revision: 37742
- drop liblzmadec as adviced by upstream, it'll be replaced by another lib anyways
- use default ratio (-7) for compression with lzma in stead of (-9) due to the huge
  amount of additional time and resources needed without much benefit added

* Fri Jun 08 2007 Per Ã˜yvind Karlsen <peroyvind@mandriva.org> 4.43-6mdv2008.0
+ Revision: 37504
- kill of debian patch, move relevant parts into separate patches and make them work
- fix version defined

* Thu Jun 07 2007 Anssi Hannula <anssi@mandriva.org> 4.43-5mdv2008.0
+ Revision: 36225
- rebuild with correct optflags

  + Per Ã˜yvind Karlsen <peroyvind@mandriva.org>
    - sync lzmp patch with debian:
      	o include <cstdlib> to be able to build with GCC 4.3. (Martin Michlmayr)
      	o use hc4 for -1 option, as hc3 is no more built in the SDK. (Lasse Collin)
    - don't always output copyright notice (P5 from PLD)
    - add missing config.h header to sdk (missing due to my fugly merge with latest sdk ;)


* Wed Mar 07 2007 Olivier Blin <oblin@mandriva.com> 4.43-2mdv2007.0
+ Revision: 134182
- buildrequires zlib-devel for squashfs-lzma library
- add uncompression static library (from squashfs-lzma.org)

* Mon Feb 12 2007 Per Ã˜yvind Karlsen <pkarlsen@mandriva.com> 4.43-1mdv2007.1
+ Revision: 118885
- update to 4.43 of sdk and 4.32.0beta3 of tools
  lzmash is now dead, replace with 'lzma'
  new lib for decoding
- Import lzma

* Sun Jan 08 2006 Giuseppe Ghibò <ghibo@mandriva.com> 4.32-1mdk
- updated lzma sdk to 4.32.
- added lzme (based on Thierry Vignaud's bzme).

* Sat Jan 07 2006 Giuseppe Ghibò <ghibo@mandriva.com> 4.27.1-1mdk
- initial Mandriva release.

