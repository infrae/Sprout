from converter import Package, Module

class BrowserTree:
    def __init__(self, product_dotted_name):
        browser = Package('browser')
        content = Package('content')
        container = Package('container')
        asset = Package('asset')
        browser.addPackage(content)
        browser.addPackage(container)
        browser.addPackage(asset)
        self.browser = browser
        self.product_dotted_name = product_dotted_name + '.browser.'
        self._nested_public = {}
        self._nested_add = { 'Groups' : 'Groups' }
        
    def getBrowserPackage(self):
        return self.browser

    def createModuleForClassPath(self, class_path):
        module_step = class_path[-2]
        class_step = class_path[-1]
        package_steps = class_path[:-2]
        package = self.browser
        for name in package_steps:
            package = package.getPackage(name)
        if not package.hasModule(module_step):
            package.addModule(Module(module_step))
        return package.getModule(module_step)

    def addClassForDirectoryView(self, directory_view):
        view_type = 'View'
        class_path = transform(directory_view.getTuplePath())
        if directory_view.hasParent():
            parent_class_path = transform(
                directory_view.getParent().getTuplePath())
        else:
            parent_class_path = None
        module = self.createModuleForClassPath(class_path)
        
        if parent_class_path is not None:
            dotted_name = (self.product_dotted_name +
                           '.'.join(parent_class_path[:-1]))
            base_class = parent_class_path[-1] + view_type
            base_classes = [base_class]
            module.addFromImport(dotted_name, base_class)
        else:
            base_classes = []

        class_base_name = class_path[-1]
        klass = directory_view.createClassHelper(
            class_base_name + view_type,
            base_classes)
        module.addClass(klass)
        # add a public and add class too
        self.addPublicClass(directory_view, class_base_name, module)
        self.addAddClass(directory_view, class_base_name, module)

    def getBaseClassInfo(self, parent_class_path):
        dotted_name = (self.products_dotted_name +
                       '.'.join(parent_class_path[:-1]))
        base_class = parent_class_path[-1] + view_type
        return dotted_name, base_class

    def addPublicClass(self, directory_view, class_base_name, module):
        """Given a directory view, create and add PublicView to module.
        """
        self._addAddOrPublicClass(directory_view, class_base_name,
                                  module, 'public', self._nested_public)
        
    def addAddClass(self, directory_view, class_base_name, module):
        """Given a directory view, create and add AddView to module.
        """
        self._addAddOrPublicClass(directory_view, class_base_name,
                                  module, 'add', self._nested_add)

    def _addAddOrPublicClass(self, directory_view, class_base_name, module,
                             view_type, nested):
        # get the directory view for this directory view
        dv = self._getAddOrPublicDirectoryView(
            directory_view, view_type, nested)
        if dv is None:
            return
        # given directory view, create class for it
        klass = self._createAddOrPublicClass(dv, class_base_name, view_type)
        # add import statement
        module.addFromImport(self.product_dotted_name + view_type,
                             klass.getBaseClasses()[0])
        module.addClass(klass)

    def _getAddOrPublicDirectoryView(self, directory_view, view_type, nested):
        root = directory_view.getRoot()
        if not directory_view.hasParent():
            return
        # get name of directory view
        name = directory_view.getPythonName()
        # get name of parent
        parent_name = directory_view.getParent().getPythonName()
        # some add views are nested, find view they're nested in
        nested_dv = nested.get(parent_name, None)
        try:
            if not nested_dv:
                return root[view_type][name]
            else:
                return root[view_type][nested_dv][name]
        except KeyError:
            # can't find view
            return None

    def _createAddOrPublicClass(self, directory_view, class_base_name,
                                view_type):
        view_type_name = view_type.capitalize() + 'View'
        class_name = class_base_name + view_type_name
        base_class_name = directory_view.getParent().getPythonName().capitalize()
        if base_class_name in ['Public', 'Add']:
            base_class = base_class_name + 'View'
        else:
            base_class = base_class_name + view_type_name
        return directory_view.createClassHelper(class_name, [base_class])

    def addClassesForDirectoryViewTree(self, directory_view):
        """Add classes (only base classes and edit classes).
        """
        # don't translate any add or public views, but do translate
        # base classes.
        # Add and public views are added automatically.
        dv_path = directory_view.getTuplePath()
        if len(dv_path) > 1 and dv_path[0] in ('public', 'add'):
            return
        self.addClassForDirectoryView(directory_view)
        for dv in directory_view.getDirectoryViews():
            self.addClassesForDirectoryViewTree(dv)
        
BASE_CLASS_TRANSFORMS = {
    () : ('base', 'Base'),
    ('edit',) : ('edit', 'Edit'),
    ('public',) : ('public', 'Public'),
    ('add',) : ('add', 'Add'),
    ('edit', 'Content') : ('content', 'content', 'Content'),
    ('edit', 'VersionedContent') : ('content', 'versioned', 'VersionedContent'),
    ('edit', 'Container') : ('container', 'container', 'Container'),
    ('edit', 'Asset') : ('asset', 'asset', 'Asset'),
    }

class TransformerRegistry:
    """Registry mapping directory view paths (in tuple form) to class path.

    It can transform base classes and classes in the 'edit' tree. It
    shouldn't be used to look up transforms for the 'public' and 'add'
    trees.
    
    This is implemented as a singleton, use transform and transform_register
    top level functions.
    """
    def __init__(self, d):
        self._dict = {}
        self._dict.update(d)
        
    def register(self, directory_view_path, class_path):
        self._dict[directory_view_path] = class_path

    def getBaseClassPath(self, directory_view_path):
        """Get the path to a base class of directory view.

        Directory view is indicated by direcory view path.
        """
        base_dv = directory_view_path[:-1]
        while 1:
            base_class_path = self._dict.get(base_dv)
            if base_class_path is not None:
                return base_class_path
            base_dv = base_dv[:-1]
        assert 0, "Should never reach this"
        
    def transform(self, directory_view_path):
        # first see whether we have a direct mapping (it's a base class)
        class_path = self._dict.get(directory_view_path)
        if class_path is not None:
            return class_path

        # now we must be handling an edit view
        assert directory_view_path[0] == 'edit'
        # find the class of directory view we're in
        base_class_path = self.getBaseClassPath(directory_view_path)    
        # okay, we want our module and class to be in the same package
        package_path = base_class_path[:-2]
        # now generate module name based on directory view name
        module_name = directory_view_path[-1].lower()
        # and generate class base name
        class_base_name =  directory_view_path[-1]
        # and construct the whole path
        return package_path + (module_name, class_base_name)
    
_transformer_registry = TransformerRegistry(BASE_CLASS_TRANSFORMS)

transform = _transformer_registry.transform
transform_register = _transformer_registry.register

    
