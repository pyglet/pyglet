InstallationCheck = dict(
    postjaguar=(
        u"#!/bin/sh\nexit 112\n",
        u'"16" = "This package requires Mac OS X 10.3 or later";',
    ),
    prepanther=(u"""#!/bin/sh
#
# We use IFRequirementDicts anyway and "parse" it to find where expect
# Python to be.  It's remotely possible that Python is not installed
# at all, so this is a horrendously evil and ugly shell script.
#

IPATH=`grep -A 1 SpecArgument $1/Contents/Info.plist | grep string | sed 's/^.*<string>\(.*\)<\/string>.*$/\1/g'`
if ((test -z $IPATH) || (test -e $IPATH)); then exit 0; fi
echo "Error during InstallationCheck"
echo "Package: $1"
echo "Expected path not found: $IPATH"
exit 112
""",
        u'"16" = "This package requires MacPython to be installed";',
    ),
)
