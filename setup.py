from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='Sprout',
      version=version,
      description="Common Python library which contains reusable components, developed at Infrae.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='xml',
      author='Infrae',
      author_email='info@infrae.com',
      url='http://infrae.com/products/silva',
      license='BSD, GPL and PythonLicence',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',

      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
