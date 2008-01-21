"""bdist_mpkg.cmd_bdist_mpkg

Implements the Distutils 'bdist_mpkg' command (create an OS X "mpkg"
binary distribution)."""

import os
import sys
import zipfile

from setuptools import Command

from distutils.util import get_platform, byte_compile
from distutils.dir_util import remove_tree, mkpath
from distutils.errors import *
from distutils import log

from bdist_mpkg import pkg, tools, plists
from bdist_mpkg.util import copy_tree

INSTALL_SCHEME_DESCRIPTIONS = dict(
    purelib = u'(Required) Pure Python modules and packages',
    platlib = u'(Required) Python modules, extensions, and packages',
    headers = u'(Optional) Header files for development',
    scripts = u'(Optional) Scripts to use from the Unix shell',
    data    = u'(Optional) Additional data files (sometimes documentation)',
)

class bdist_mpkg (Command):

    description = "create a Mac OS X mpkg distribution for Installer.app"

    user_options = [
        ('pkg-base=', None,
         "base directory for creating pkg (defaults to \"mpkg\" "
         "under --bdist-base"),
        ('bdist-base=', None,
         "bdist base directory"),
        ('build-base=', None,
         "build base directory"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O2]"),
        ('component-directory=', None,
         "component directory for packages relative to the mpkg "
         "(defaults to ./Contents/Packages)"),
        ('keep-temp', 'k',
         "keep the pseudo-installation tree around after creating "
         "the distribution archive"),
        ('open', None,
         'Open with Installer.app after building'),
        ('readme=', None,
         'readme text file to be used in pkg (defaults to ReadMe)'),
        ('license=', None,
         'license text file to be used in pkg (defaults to License or COPYING)'),
        ('welcome=', None,
         'welcome text file to be used in pkg (defaults to Welcome)'),
        ('background=', None,
         'background image to be used in pkg (defaults to background)'),
        ('dist-dir=', 'd',
         "directory to put final built pkg distributions in"),
        ('zipdist', 'z',
         "build a zip containing the package in dist"),
        ('skip-build', None,
         "skip rebuilding everything (for testing/debugging)"),
    ]

    boolean_options = ['skip-build', 'keep-temp', 'open', 'zipdist']

    def initialize_options (self):
        self.skip_build = False
        self.keep_temp = False
        self.open = False
        self.template = None
        self.readme = None
        self.license = None
        self.welcome = None
        self.background = None
        self.bdist_base = None
        self.build_base = None
        self.pkg_base = None
        self.dist_dir = None
        self.plat_name = None
        self.zipdist = False
        self.optimize = 2
        self.component_directory = './Contents/Packages'
        self.scheme_command = {}
        self.scheme_map = {}
        self.packages = []
        self.scheme_descriptions = {}
        self.scheme_root = {}
        self.scheme_copy = {}
        self.scheme_subprojects = {}
        self.command_schemes = None
        self.custom_schemes = None
        self.packagesdir = None
        self.metapackagename = None
        self.macosx_version = tools.sw_vers()

    def get_command_obj(self, name):
        return self.distribution.get_command_obj(name)

    def get_name(self):
        return self.distribution.get_name()

    def get_version(self):
        return self.distribution.get_version()

    def make_fullplatcomponents(self, *args):
        lst = [s.replace('-', '_') for s in args]
        lst.extend([
            'py' + sys.version[:3],
            'macosx' + '.'.join(map(str, self.macosx_version.version[:2])),
        ])
        return lst

    def get_fullplatname(self):
        return '-'.join(
            self.make_fullplatcomponents(self.get_name(), self.get_version()))

    def get_command_schemes(self):
        rval = self.command_schemes
        if rval is None:
            rval = {}
            for scheme, cmd in self.scheme_command.iteritems():
                rval.setdefault(cmd, []).append(scheme)
            self.command_schemes = rval
        return rval

    def finalize_options (self):
        if not isinstance(self.optimize, int):
            self.optimize = int(self.optimize)
        self.set_undefined_options('build', ('build_base', 'build_base'))
        self.reinitialize_command('build').build_base =  self.build_base
        self.set_undefined_options('bdist',
            ('bdist_base', 'bdist_base'),
            ('dist_dir', 'dist_dir'),
            ('plat_name', 'plat_name'),
        )
        if self.pkg_base is None:
            self.pkg_base = os.path.join(self.bdist_base, 'mpkg')

        if self.custom_schemes is None:
            self.custom_schemes = {}
        for scheme, desc in self.custom_schemes.iteritems():
            if 'description' in desc:
                self.scheme_descriptions[scheme] = desc['description']
            if 'prefix' in desc:
                self.scheme_map[scheme] = desc['prefix']
            if 'source' in desc:
                self.scheme_copy[scheme] = desc['source']

        install = self.get_finalized_command('install')
        for scheme, description in INSTALL_SCHEME_DESCRIPTIONS.iteritems():
            self.scheme_command.setdefault(scheme, 'install')
            self.scheme_descriptions.setdefault(scheme, description)
            self.scheme_map.setdefault(scheme,
                os.path.realpath(getattr(install, 'install_' + scheme)))

        if tools.is_framework_python():
            if self.get_scheme_prefix('scripts').startswith(sys.prefix):
                self.scheme_map['scripts'] = '/usr/local/bin'
            if self.get_scheme_prefix('data').startswith(sys.prefix):
                self.scheme_map['data'] = '/usr/local/share'

        self.finalize_package_data()

    def finalize_package_data(self):
        if self.license is None:
            for attempt in ('License', 'COPYING'):
                self.license = pkg.try_exts(attempt, exts=pkg.TEXT_EXTS)
                if self.license is not None:
                    break

        if self.readme is None:
            self.readme = pkg.try_exts('ReadMe', exts=pkg.TEXT_EXTS)

        if self.welcome is None:
            self.welcome = pkg.try_exts('Welcome', exts=pkg.TEXT_EXTS)

        if self.background is None:
            self.background = pkg.try_exts('background', exts=pkg.IMAGE_EXTS)

        if self.template is None:
            if self.macosx_version < '10.3':
                self.template = 'prepanther'
            else:
                self.template = 'postjaguar'

        self.metapackagename = self.get_fullplatname() + '.mpkg'
        self.pseudoinstall_root = self.get_pseudoinstall_root()
        self.packagesdir = os.path.join(
            self.get_metapackage(),
            self.component_directory
        )


    def run_extra(self):
        """
        Subclass and add stuff here to add entries to scheme_map
        """
        pass

    def scheme_hook(self, scheme, pkgname, version, files, common,
            prefix, pkgdir):
        """
        Subclass and do stuff with the scheme post-packaging
        """
        pass

    def run_subprojects(self):
        for scheme,setupfile in self.scheme_subprojects.iteritems():
            self.run_subproject(scheme, setupfile)

    def run_subproject(self, scheme, setupfile):
        if os.path.isdir(setupfile):
            setupfile = os.path.join(setupfile, 'setup.py')
        build_base = os.path.abspath(os.path.join(self.build_base, scheme))
        dist_dir = os.path.abspath(self.packagesdir)
        args = [
            'bdist_mpkg', '--build-base=' + build_base,
            '--dist-dir=' + dist_dir
        ]
        if self.keep_temp:
            args.append('--keep-temp')
        pkg = self.sub_setup(setupfile, args).get_command_obj(
            'bdist_mpkg').metapackagename
        if pkg is not None:
            self.packages.append((pkg, self.get_scheme_status(scheme)))

    def sub_setup(self, setupfile, args):
        setupfile = os.path.abspath(setupfile)
        srcdir = os.path.dirname(setupfile)
        old_path = list(sys.path)
        sys.path.insert(0, srcdir)
        cwd = os.getcwd()
        os.chdir(srcdir)
        try:
            return tools.run_setup(setupfile, args)
        finally:
            sys.path[:] = old_path
            os.chdir(cwd)

    def get_finalized_install_command(self):
        install = self.reinitialize_command('install', reinit_subcommands=1)
        self.get_command_obj('build').build_base = self.build_base
        for scheme in self.get_command_schemes()['install']:
            prefix = self.get_scheme_install_prefix(scheme)
            setattr(install, 'install_' + scheme, prefix)
        install.single_version_externally_managed = 1
        install.root = self.pkg_base
        install.skip_build = self.skip_build
        install.warn_dir = 0
        install.compile = 0
        install.ensure_finalized()
        return install

    def run_install(self):
        install = self.get_finalized_install_command()
        data = self.get_finalized_command('install_data')
        data.root = os.path.join(data.root, 'data')
        install.run()
        self.byte_compile()

    def byte_compile(self):
        for scheme in ('platlib', 'purelib'):
            scheme_dir = self.get_scheme_dir(scheme)
            if os.path.exists(scheme_dir):
                self.byte_compile_scheme(scheme)

    def byte_compile_scheme(self, scheme):
        files, common, prefix = self.get_scheme_root(scheme)
        install_root = self.get_scheme_dir(scheme)

        byte_compile(
            files,
            optimize=0,
            force=self.force,
            prefix=install_root,
            dry_run=self.dry_run,
        )
        if self.optimize > 0:
            byte_compile(
                files,
                optimize=self.optimize,
                force=self.force,
                prefix=install_root,
                verbose=self.verbose,
                dry_run=self.dry_run,
            )

    def run_adminperms(self):
        tools.adminperms(self.pkg_base,
            verbose=self.verbose, dry_run=self.dry_run)

    def mkpath(self, fn):
        mkpath(fn, dry_run=self.dry_run, verbose=self.verbose)

    def get_scheme_info(self, scheme):
        return ()

    def get_scheme_pkgname(self, scheme):
        return '-'.join(self.make_fullplatcomponents(
            self.get_name(), scheme,
        ))

    def get_scheme_pkgfile(self, scheme):
        return '-'.join(self.make_fullplatcomponents(
            self.get_name(),
            scheme,
            self.get_version(),
        )) + '.pkg'

    def get_pseudoinstall_root(self):
        return os.path.join(self.dist_dir, self.metapackagename)

    def get_schemes(self):
        return self.scheme_map.keys()

    def get_scheme_prefix(self, scheme):
        return self.scheme_map.get(scheme)

    def get_scheme_install_prefix(self, scheme):
        prefix = self.get_scheme_prefix(scheme)
        if prefix.startswith(os.sep):
            prefix = prefix[len(os.sep):]
        return os.path.join(scheme, prefix)

    def get_scheme_install_target(self, scheme):
        return os.path.join(
            self.pkg_base,
            self.get_scheme_install_prefix(scheme),
        )

    def get_scheme_dir(self, scheme):
        return os.path.join(self.pkg_base, scheme)

    def get_scheme_root(self, scheme):
        rval = self.scheme_root.get(scheme)
        if rval is None:
            rval = self.scheme_root[scheme] = tools.find_root(
                self.get_scheme_dir(scheme),
            )
        return rval

    def get_scheme_description(self, scheme):
        description = self.scheme_descriptions.get(scheme)
        if description is None:
            return None
        files, common, prefix = self.get_scheme_root(scheme)
        if prefix is not None:
            description += u'\nInstalled to: ' + tools.unicode_path(prefix)
        return description

    def get_metapackage(self):
        return self.get_pseudoinstall_root()

    def get_metapackage_info(self):
        return dict(
            IFRequirementDicts=[plists.python_requirement(self.get_name())],
            IFPkgFlagComponentDirectory=tools.unicode_path(
                self.component_directory
            ),
        )

    def get_scheme_version(self, scheme):
        return self.get_version()

    def get_scheme_status(self, scheme):
        return 'selected'

    def make_scheme_package(self, scheme):
        files, common, prefix = self.get_scheme_root(scheme)
        pkgname = self.get_scheme_pkgname(scheme)
        pkgfile = self.get_scheme_pkgfile(scheme)
        self.packages.append((pkgfile, self.get_scheme_status(scheme)))
        pkgdir = os.path.join(self.packagesdir, pkgfile)
        self.mkpath(pkgdir)
        version = self.get_scheme_version(scheme)

        pkg.make_package(self,
            pkgname, version,
            files, common, prefix,
            pkgdir,
            self.get_scheme_info(scheme),
            self.get_scheme_description(scheme),
        )

        self.scheme_hook(scheme, pkgname, version, files, common, prefix,
            pkgdir)

    def make_metapackage(self):
        pkg.make_metapackage(self,
            self.get_name(),
            self.get_version(),
            self.packages,
            self.get_metapackage(),
            self.get_metapackage_info(),
        )

    def remove_temp(self):
        remove_tree(self.pkg_base, dry_run=self.dry_run)

    def run_open(self):
        TOOL = '/usr/bin/open'
        os.spawnv(os.P_NOWAIT, TOOL, [TOOL, self.get_metapackage()])

    def run_commands(self):
        for command in self.get_command_schemes():
            if command != 'install':
                self.run_command(command)

    def run_copy(self):
        for scheme, source in self.scheme_copy.iteritems():
            log.info("copying files for scheme %s" % (scheme,))
            target = self.get_scheme_install_target(scheme)
            self.copy_tree(source, target)

    def run(self):
        log.info("installing to %s" % (self.pkg_base,))
        self.run_install()
        self.run_commands()
        self.run_subprojects()
        self.run_copy()
        self.run_extra()
        self.run_adminperms()

        # And make an archive relative to the root of the
        # pseudo-installation tree.
        self.mkpath(self.packagesdir)

        name = self.get_name()
        version = self.get_version()

        for scheme in self.get_schemes():
            schemedir = self.get_scheme_dir(scheme)
            if not os.path.exists(schemedir):
                # if the scheme dir doesn't already exist,
                # nothing was installed there
                # installation should be done in run_extra or by the
                # install command
                log.info("nothing to be installed for scheme %s" % (scheme,))
                continue
            self.make_scheme_package(scheme)

        self.make_metapackage()

        if not self.keep_temp:
            self.remove_temp()
        if self.zipdist:
            self.run_zipdist()
        if self.open:
            self.run_open()

    def run_zipdist(self):
        zipname = self.get_fullplatname()
        outzip = os.path.join(self.dist_dir, zipname + '.zip')
        z = zipfile.ZipFile(outzip, mode='w', compression=zipfile.ZIP_DEFLATED)
        log.info('Creating %s', outzip)
        mpkg = self.get_metapackage()
        zipbase = os.path.join(zipname, os.path.basename(mpkg))
        mpkgroot = os.path.join(mpkg, '')
        for root, dirs, files in os.walk(mpkgroot):
            for fn in files:
                fn = os.path.join(root, fn)
                arcfn = os.path.join(zipbase, fn[len(mpkgroot):])
                compression = zipfile.ZIP_DEFLATED
                if os.path.splitext(fn)[1] == '.gz':
                    compression= zipfile.ZIP_STORED
                z.write(fn, arcfn, compression)

        # ZipFile always marks the files' attributes to be interpreted as if
        # they came from a Windows host. This interferes with some software
        # (namely unzip(1) from Info-Zip) from extracting executables with the
        # proper file attributes. So manually fix the appropriate attributes on
        # each of the ZipInfo's to specify the host system as a UNIX.
        for zinfo in z.filelist:
            zinfo.create_system = 3 # UNIX

        z.close()

    def copy_tree(self, infile, outfile, preserve_mode=1,
            preserve_times=1, preserve_symlinks=1, condition=None):
        """
        Copy an entire directory tree respecting verbose, dry-run,
        and force flags.

        This version doesn't bork on existing symlinks
        """
        update = not self.force
        dry_run = self.dry_run
        verbose = self.verbose
        return copy_tree(
            infile, outfile,
            preserve_mode, preserve_times, preserve_symlinks,
            update, verbose, dry_run, condition
        )
