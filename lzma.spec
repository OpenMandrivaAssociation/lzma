%define oldlzmaver 4.32.7
%define major 0
%define libname %mklibname lzmadec %{major}
%define devname %mklibname -d lzmadec

Summary:	LZMA utils
Name:		lzma
Version:	4.43
Release:	37
License:	GPLv2
Group:		Archiving/Compression
Url:		http://tukaani.org/lzma/
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
BuildRequires:	diffutils
BuildRequires:	dos2unix
BuildRequires:	pkgconfig(zlib)

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
License:	LGPLv2
Provides:	%{_lib}%{name}%{major} = %{version}-%{release}

%description -n	%{libname}
Libraries for decoding LZMA compression.

%package -n	%{devname}
Summary:	Devel libraries & headers for liblzmadec
Group:		Development/C
License:	LGPLv2
Provides:	liblzmadec-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}-%{release}

%description -n %{devname}
Devel libraries & headers for liblzmadec.

%package -n	dkms-%{name}
Summary:	Kernel modules for decoding LZMA compression
Group:		System/Kernel and hardware
Requires(post,preun):	dkms

%description -n	dkms-%{name}
Kernel modules for decoding LZMA compression.

%prep
%setup -qn %{name}-%{oldlzmaver} -a1
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
%{_libdir}/liblzmadec.so.%{major}*

%files -n %{devname}
%doc *.txt
%{_includedir}/*.h
%{_libdir}/*.so
%{_libdir}/*.a

%files -n dkms-%{name}
/usr/src/%{name}-%{version}-%{release}

