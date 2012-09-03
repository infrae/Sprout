# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from setuptools import setup, find_packages
import os

version = '1.0.5'

tests_require = [
    'zope.testing',
    ]

setup(name='Sprout',
      version=version,
      description="Common Python library which contains reusable components, developed at Infrae.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "License :: OSI Approved :: BSD License",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Utilities",
        ],
      keywords='html sax parser xml',
      author='Martijn Faassen',
      author_email='info@infrae.com',
      url='http://infrae.com/download/Sprout',
      license='BSD, GPL and PythonLicence',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'zope.interface',
        'zope.component',
        'grokcore.component',
        ],
      test_suite = 'sprout',
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      )
