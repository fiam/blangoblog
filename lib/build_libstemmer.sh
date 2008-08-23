#!/bin/bash

source ./functions.sh

LIBSTEMMER="libstemmer_c"
LIBSTEMMER_URI="http://snowball.tartarus.org/dist/${LIBSTEMMER}.tgz"

BASE=$(pwd)
fetch_and_extract ${LIBSTEMMER_URI}
cd ${LIBSTEMMER}
sed -i "s/-Iinclude/-Iinclude -O2 -fPIC/" Makefile
cat >> Makefile << EOF
libstemmer.so.0: \$(snowball_sources:.c=.o)
	\$(CC) -shared -Wl,-soname,libstemmer.so.0 -o libstemmer.so.0 \$^
EOF
make libstemmer.so.0 &&  \
mkdir -p ${BASE}/lib && \
cp -f libstemmer.so.0 ${BASE}/lib && \
ln -sf ${BASE}/lib/libstemmer.so.0 ${BASE}/lib/libstemmer.so
cd -
rm -fr ${LIBSTEMMER}
