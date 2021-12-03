#!/bin/bash
curdir=$(pwd)
if [ ! -z "$1" ]
  then
    echo $1
    cd $1
fi

workdir=${PWD##*/}
tempd=$(mktemp -d)

git log --all --pretty=format:'%ai,%s' --author="$(git config user.name)" > $tempd/name_log.csv
git log --all --pretty=format:'%ai,%s' --author="<$(git config user.email)>" > $tempd/email-log.csv

cd $curdir

cat $tempd/*.csv | sort -u > "log_export_$workdir.csv"
rm -rf $tempd
