#!/bin/bash
# $Id:$

ROOT=`dirname $0`/../..
RES=`dirname $0`/res
VERSION=`grep 'VERSION =' $ROOT/setup.py | cut -d "'" -f2`

rm -rf $ROOT/build

# Create AVbin files
mkdir -p $ROOT/build/avbin
rsync -a /usr/local/lib/libavbin.dylib $ROOT/build/avbin/
cp /usr/local/lib/`ls -l /usr/local/lib/libavbin.dylib | \
    sed 's/.* -> \(.*\)$/\1/'` $ROOT/build/avbin/
chmod a+rx $ROOT/build/avbin/*
chown root $ROOT/build/avbin/*
chgrp wheel $ROOT/build/avbin/*

PYTHONPATH=`dirname $0`:$PYTHONPATH
export PYTHONPATH

python $ROOT/setup.py bdist_mpkg \
    --background=$RES/background.pdf \
    --readme=$RES/readme.rtf \
    --keep-temp

if [ $? != 0 ]; then
    exit 1
fi

MPKG=$ROOT/dist/pyglet-$VERSION.mpkg

DMG_BUILD=$ROOT/build/dmg
DMG=$ROOT/dist/pyglet-$VERSION.dmg

rm -f $DMG
rm -rf $DMG_BUILD

mkdir -p $DMG_BUILD
mv $MPKG $DMG_BUILD/
hdiutil create -srcfolder $DMG_BUILD -volname pyglet-$VERSION $DMG
#hdiutil internet-enable -yes $DMG
