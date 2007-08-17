#!/bin/bash
# $Id:$

ROOT=`dirname $0`/../..
RES=`dirname $0`/res
VERSION=`grep 'VERSION =' $ROOT/setup.py | cut -d "'" -f2`

# Create AVbin files
mkdir -p $ROOT/build/avbin
rsync -a /usr/lib/libavbin.dylib $ROOT/build/avbin/
cp /usr/lib/`ls -l /usr/lib/libavbin.dylib | sed 's/.* -> \(.*\)$/\1/'` \
    $ROOT/build/avbin/

python $ROOT/setup.py bdist_mpkg \
    --background=$RES/background.pdf \
    --readme=$RES/readme.rtf 
MPKG=$ROOT/dist/pyglet-$VERSION.mpkg

DMG_BUILD=$ROOT/build/dmg
DMG=$ROOT/dist/pyglet-$VERSION.dmg

rm -f $DMG
rm -rf $DMG_BUILD

mkdir -p $DMG_BUILD
mv $MPKG $DMG_BUILD/
hdiutil create -srcfolder $DMG_BUILD -volname pyglet-$VERSION $DMG
#hdiutil internet-enable -yes $DMG
