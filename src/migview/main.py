# main body of a script to migrate Silva old-style views code
# to new-style class view code

import converter, transform
from optparse import OptionParser
from path import path

def main():
    usage ="usage: %prog [-v] product_dotted_name views_path output_path"
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error("incorrect number of arguments")
    product_dotted_name = args[0]
    views_path = path(args[1])
    output_path = path(args[2])
    convert(product_dotted_name, views_path, output_path, options.verbose)

def convert(product_dotted_name, views_path, output_path, verbose=False):
    if verbose:
        print "Reading directory view at:", views_path
    top_view = converter.DirectoryView(views_path, None)
    if verbose:
        print "Transforming to browser tree"
    browser_tree = transform.BrowserTree(product_dotted_name)
    browser_tree.addClassesForDirectoryViewTree(top_view)
    if verbose:
        print "Saving transformed views to:", output_path
    package = browser_tree.getBrowserPackage()
    package.save(output_path)
    if verbose:
        print "Transform successful"
        
if __name__ == '__main__':
    main()
    
