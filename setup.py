"""Setup script.

Run "python3 setup --help-commands" to list all available commands and their
descriptions.
"""
import os
import re
import sys
from abc import abstractmethod
from subprocess import CalledProcessError, call, check_call

from setuptools import Command, find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.test import test as TestCommand

if 'bdist_wheel' in sys.argv:
    raise RuntimeError("This setup.py does not support wheels")

if 'VIRTUAL_ENV' in os.environ:
    BASE_ENV = os.environ['VIRTUAL_ENV']
else:
    BASE_ENV = '/'

ETC_FILES = ['etc/kytos/kytos.conf', 'etc/kytos/logging.ini']


class SimpleCommand(Command):
    """Make Command implementation simpler."""

    user_options = []

    @abstractmethod
    def run(self):
        """Run when command is invoked.

        Use *call* instead of *check_call* to ignore failures.
        """
        pass

    def initialize_options(self):
        """Set defa ult values for options."""
        pass

    def finalize_options(self):
        """Post-process options."""
        pass


class Linter(SimpleCommand):
    """Code linters."""

    description = 'run Pylama on Python files'

    def run(self):
        """Run linter."""
        self.lint()

    @staticmethod
    def lint():
        """Run pylama and radon."""
        files = 'setup.py tests kytos'
        print('Pylama is running. It may take several seconds...')
        cmd = 'pylama ' + files
        try:
            check_call(cmd, shell=True)
        except CalledProcessError as e:
            print('FAILED: please, fix the error(s) above.')
            sys.exit(e.returncode)


class Test(TestCommand):
    """Run doctest and linter besides tests/*."""

    def run(self):
        """First, tests/*."""
        super().run()
        print('Running examples in documentation')
        check_call('make doctest -C docs/', shell=True)
        Linter.lint()


class Cleaner(SimpleCommand):
    """Custom clean command to tidy up the project root."""

    description = 'clean build, dist, pyc and egg from package and docs'

    def run(self):
        """Clean build, dist, pyc and egg from package and docs."""
        call('rm -vrf ./build ./dist ./*.pyc ./*.egg-info', shell=True)
        call('make -C docs clean', shell=True)


class DevelopMode(develop):
    """Recommended setup for developers.

    Instead of copying the files to the expected directories, a symlink is
    created on the system aiming the current source code.
    """

    def run(self):
        """Install the package in a developer mode."""
        super().run()
        for _file in ETC_FILES:
            self.create_path(_file)

    @staticmethod
    def create_path(file_name):
        """Method used to create the configurations files using develop."""
        etc_kytos_dir = os.path.join(BASE_ENV, 'etc/kytos')

        current_directory = os.path.dirname(__file__)
        src = os.path.join(os.path.abspath(current_directory), file_name)
        dst = os.path.join(BASE_ENV, file_name)

        if not os.path.exists(etc_kytos_dir):
            os.makedirs(etc_kytos_dir)

        if not os.path.exists(dst):
            os.symlink(src, dst)


requirements = [i.strip() for i in open("requirements.txt").readlines()]
napps_dir = os.path.join(BASE_ENV, 'var/lib/kytos/napps/.installed')

# We are parsing the metadata file as if it was a text file because if we
# import it as a python module, necessarily the kytos.core module would be
# initialized, which means that kyots/core/__init__.py would be run and, then,
# kytos.core.controller.Controller would be called and it will try to import
# some modules that are dependencies from this project and that were not yet
# installed, since the requirements installation from this project hasn't yet
# happened.
meta_file = open("kytos/core/metadata.py").read()
metadata = dict(re.findall(r"(__[a-z]+__)\s*=\s*'([^']+)'", meta_file))

if not os.path.exists(napps_dir):
    os.makedirs(napps_dir, exist_ok=True)

setup(name='kytos',
      version=metadata.get('__version__'),
      description=metadata.get('__description__'),
      url=metadata.get('__url__'),
      author=metadata.get('__author__'),
      author_email=metadata.get('__author_email__'),
      license=metadata.get('__license__'),
      test_suite='tests',
      install_requires=requirements,
      dependency_links=[
          'https://github.com/cemsbr/python-daemon/tarball/latest_release'
          '#egg=python-daemon-2.1.2'
      ],
      scripts=['bin/kytosd'],
      include_package_data=True,
      data_files=[(os.path.join(BASE_ENV, 'etc/kytos'), ETC_FILES)],
      packages=find_packages(exclude=['tests']),
      cmdclass={
          'develop': DevelopMode,
          'lint': Linter,
          'clean': Cleaner,
          'test': Test
      },
      zip_safe=False,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3.6',
          'Topic :: System :: Networking',
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Environment :: No Input/Output (Daemon)',
      ])
