#!/bin/bash

function die() {
    echo $1
    if [ -n "$2" ]; then
        cat $2
        rm -f $2
    fi
    exit 1
}

function checked_cmd() {
    errmsg=$1
    shift
    errlog=$(mktemp)
    $* > /dev/null 2> ${errlog} || die "${errmsg}" ${errlog}
    rm -f ${errlog}
}

function configure() {
    prefix=$1
    name=$2
    shift; shift
    echo "Configuring ${name}"
    checked_cmd "Error configuring ${name}" ./configure --prefix=${prefix} $*
}

function build_and_install() {
    name=$1
    echo "Building ${name}"
    checked_cmd "Error building ${name}" make
    echo "Installing ${name}"
    checked_cmd "Error installing ${name}" make install
}

function remove_fetched() {
    uri=$1
    rm -f $(basename ${uri})
}

function untar() {
    file=$1
    ext="$(echo ${file} | awk -F . '{ print $NF}')"
    if [ ${ext} = "gz" -o ${ext} = "tgz" ]; then
        tar="tar xzf"
    elif [ ${ext} = "bz2" ]; then
        tar="tar xjf"
    elif [ ${ext} = "tar" ]; then
        tar="tar xf"
    else
        die "Unknown tar extension"
    fi

    checked_cmd "Error extracting ${file}" ${tar} ${file}
}

function uncompress() {
    file=$1
    ext="$(echo ${file} | awk -F . '{ print $NF}')"
    if [ ${ext} = "gz" ]; then
        uc="gunzip"
    elif [ ${ext} = "bz2" ]; then
        uc="bunzip2"
    else
        die "Unknown compressed format"
    fi
    
    checked_cmd "Error extracting ${file}" ${uc} ${file}
}

function fetch_uri() {
    uri=$1
    args="-c --connect-timeout 5 -t 10"
    if [ -n "$2" ]; then
        args="${args} -O $2"
    fi
    wget ${args} ${uri} || die "Error fetching ${uri}"
}

function secure_fetch() {
    uri=$1
    tempfile=$(mktemp)
    fetch_uri ${uri} ${tempfile}
    mv ${tempfile} $(basename ${uri})
}

function fetch_and_extract() {
    uri=$1
    remove_fetched ${uri}
    fetch_uri ${uri}
    untar $(basename ${uri})
    remove_fetched ${uri}
}

function install_tgz() {
    prefix=$1
    name=$2
    uri=$3
    if [ -z "$4" ]; then
        dirname=${name}
    else
        dirname=$4
    fi
    cmd=$5
    srcdir=$6
    fetch_and_extract ${uri}
    cd ${dirname}/${srcdir}
    if [ -n "$cmd" ]; then
        ./$cmd
    fi
    configure ${prefix} ${name}
    build_and_install ${name}
    cd - > /dev/null
    rm -fr ${dirname}
}

function setup_environment () {
    base=$1
    #CFLAGS="-msse3 -O2 -fomit-frame-pointer -march=core2"
    CFLAGS="-I${base}/include -L${base}/lib"
    LDFLAGS="${CFLAGS} -Wl,-rpath,${base}/lib"
    PATH=${base}/bin:${PATH}

    export PATH CFLAGS LDFLAGS
}
