%global ver_maj 24
%global ver_min 08
%global ver_rel 0

%define oldlzmaver 4.32.7
%define major 0
%define libname %mklibname lzmadec %{major}
%define devname %mklibname -d lzmadec

Summary:	LZMA utils
Name:		lzma
Version:	%{ver_maj}.%{ver_min}
Release:	1
License:	GPLv2
Group:		Archiving/Compression
Url:		https://tukaani.org/lzma/
Source0:	https://downloads.sourceforge.net/project/sevenzip/LZMA%20SDK/lzma%{ver_maj}%{ver_min}.7z
#Source3:	sqlzma.h
# (blino) modified for 443, from sqlzma1-449.patch:
#   * adapted to lzma443 dist structure: s,/C/Compress/Lzma/,/C/7zip/Compress/LZMA_C/,; s,/CPP/7zip/Compress/LZMA_Alone/,/C/7zip/Compress/LZMA_Alone/,
#   * use sqlzma.mk makefiles for 443 (from from sqlzma1-443.patch)
#   * remove NCoderPropID::kNumThreads in comp.cc, it is invalid since we don't build LZMAEncoder.cpp with COMPRESS_MF_MT multithread support
#Patch3:		lzma-4.32.4-sqlzma.patch
#Patch4:		lzma-4.43-add-missing-header.patch
#Patch5:		lzma-4.43-quiet.patch
#Patch6:		lzma-4.43-update-version.patch
#Patch7:		lzma-4.43-fix-fast-compression.patch
#Patch8:		lzma-4.43-add-missing-gethandle.patch
#Patch9:		lzma-4.32.4-text-tune.patch
# 4.32.2 has changes to sdk that we replace with newer, we apply these to the new
#Patch12:	lzma-4.32.2-sdk-changes.patch
#Patch16:	lzma-4.32.7-format_not_a_string_literal_and_no_format_arguments.diff
# for squashfs-lzma library
#Patch17:	lzma-aarch64.patch
BuildRequires:	diffutils
BuildRequires:	dos2unix
BuildRequires:	pkgconfig(zlib)
BuildRequires:	7zip

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
%autosetup -p1 -c -n lzma-sdk
	
rm -rv bin


#install -p -m 0644 %{SOURCE1} .

%build
pushd CPP/7zip/Bundles/LzmaCon
make -f makefile.gcc clean all CXXFLAGS_EXTRA="%{build_cxxflags}" CFLAGS_WARN="%{build_cflags}" LDFLAGS_STATIC_2="%{build_cxxflags}"
popd

%install
install -dm0755 %{buildroot}%{_libdir}
install -pm0755 CPP/7zip/Bundles/LzmaCon/liblzmasdk.so.%{ver_maj}.%{ver_min}.%{ver_rel} %{buildroot}%{_libdir}
pushd %{buildroot}%{_libdir}
ln -s liblzmasdk.so.%{ver_maj}.%{ver_min}.%{ver_rel} liblzmasdk.so.%{ver_maj}
ln -s liblzmasdk.so.%{ver_maj}.%{ver_min}.%{ver_rel} liblzmasdk.so
popd
install -dm0755 %{buildroot}/%{_includedir}/lzma
find -iname '*.h' | xargs -I {} install -m0644 -D {} %{buildroot}/%{_includedir}/lzma-sdk/{}
#contains only Windows related headers so for fedora useless
rm -rv %{buildroot}/usr/include/lzma-sdk/CPP/Windows


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

