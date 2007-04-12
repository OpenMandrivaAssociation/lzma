%define	name	lzma
%define	version	4.43
%define	release	%mkrel 2
%define	oldlzmaver	4.32.0beta3
%define	major	0
%define	libname	%mklibname lzmadec %{major}

Summary: 	LZMA utils
Name: 		%{name}
Version: 	%{version}
Release: 	%{release}
License: 	GPL
Group:		Archiving/Compression
Source0:	http://tukaani.org/lzma/lzma-%{oldlzmaver}.tar.gz
Source1:	http://ovh.dl.sourceforge.net/sourceforge/sevenzip/lzma443.tar.bz2
Source2:	lzme.bz2
Source3:	sqlzma.h
#Patch0:	lzma-432-makefile.patch.bz2
#Patch1:	lzma-432-makefile-sdknew.patch.bz2
Patch2:		lzma-4.43-lzmp.patch
Patch3:		sqlzma1-443.patch
# for squashfs-lzma library
BuildRequires:	zlib-devel
BuildRequires:	dos2unix
URL:		http://tukaani.org/lzma/
Buildroot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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

- The patch for GNU tar integrates LZMA compression with the tar
  command in the same way as with gzip and bzip2.

%package -n	%{libname}
Summary:	Libraries for decoding LZMA compression
Group:		System/Libraries
License:	LGPL

%description -n %{libname}
Libraries for decoding LZMA compression.

%package -n	%{libname}-devel
Summary:	Devel libraries & headers for liblzmadec
Group:		Development/C
License:	LGPL
Provides:	liblzmadec-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Requires:	%{libname} = %{version}

%description -n %{libname}-devel
Devel libraries & headers for liblzmadec.

%prep
%setup -q -n %{name}-%{oldlzmaver} -a1
#%patch0 -p1 -b .427
#%patch1 -p1 -b .427_sdk
%patch2 -p1
%patch3 -p1 -b .liblzma_r
bzcat %{SOURCE2} > lzme
cp %{SOURCE3} .
dos2unix *.txt

# ugly syncing with latest sdk
mv src/sdk src/sdk.old
cp -r C src/sdk
for i in `find src/sdk.old -name Makefile.\*`; do
	cp $i `echo $i|sed -e 's#sdk.old#sdk#g'`;
done
find src/sdk -name makefile|xargs rm -f

%build
CFLAGS="%{optflags} -D_FILE_OFFSET_BITS=64" \
CXXFLAGS="%{optflags} -D_FILE_OFFSET_BITS=64 -DPACKAGE_VERSION=\\\"%{oldlzmaver}\\\"" \
%configure2_5x
%make
%make -C C/7zip/Compress/LZMA_C -f sqlzma.mk Sqlzma=../../../..
%make -C C/7zip/Compress/LZMA_Alone -f sqlzma.mk Sqlzma=../../../..

%install
rm -rf %{buildroot}
%makeinstall_std
install -m755 lzme %{buildroot}%{_bindir}
rm -f %{buildroot}%{_libdir}/*.la
#symlink to provide backward compatibility for stuff still using old 'lzmash' script
ln -s lzma %{buildroot}%{_bindir}/lzmash
install C/7zip/Compress/LZMA_*/*.a %{buildroot}%{_libdir}

%post -n %{libname} -p /sbin/ldconfig
%postun -n %{libname} -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc README THANKS
%{_bindir}/*
%{_mandir}/man1/*

%files -n %{libname}
%defattr(-,root,root)
%{_libdir}/lib*.so.*

%files -n %{libname}-devel
%defattr(644,root,root,755)
%doc *.txt
%defattr(-,root,root)
%{_includedir}/*.h
%{_libdir}/*.so
%{_libdir}/*.a


