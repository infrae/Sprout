import os
import sys

# this allows the sprout package to be installed as a Zope product.
# It will add the src directory to the PYTHONPATH
product_dir, filename = os.path.split(__file__)
src_path = os.path.join(product_dir, 'src')
sys.path.append(src_path)

def initialize(context):
    pass
