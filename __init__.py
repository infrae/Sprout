import os
import sys

# a bit hackish, but this allows using the Sprout package as a Zope
# product, it will add all dirs in the 'src' directory to the path,
# making them available as Python packages
srcpath = '%s/src' % (os.sep.join(os.path.split(__file__)[:-1]))
sys.path.append(srcpath)
for file in os.listdir(srcpath):
    filepath = '%s%s%s' % (srcpath, os.sep, file)
    if os.path.isdir(filepath) and not file == 'CVS':
        sys.path.append(filepath)

def initialize(context):
    pass
