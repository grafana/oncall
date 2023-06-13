#!/usr/bin/env bash
# https://gist.github.com/maxpoletaev/4ed25183427a2cd7e57a

case "$OSTYPE" in
    darwin*)  PLATFORM="OSX" ;;
    linux*)   PLATFORM="LINUX" ;;
    bsd*)     PLATFORM="BSD" ;;
    *)        PLATFORM="UNKNOWN" ;;
esac

replace() {
    if [[ "$PLATFORM" == "OSX" || "$PLATFORM" == "BSD" ]]; then
        sed -i "" "$1" "$2"
    elif [ "$PLATFORM" == "LINUX" ]; then
        sed -i "$1" "$2"
    fi
}

if grep -q $1 $3; then
    # file contains string, lets replace it
    # https://stackoverflow.com/a/42667816 - why we need the -i ''
    replace "s~$1=.*~$1=$2~g" $3
else
    # file doesn't contain string, lets append it
    echo "$1=$2" >> $3
fi
