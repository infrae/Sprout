
from path import path

__metaclass__ = type

INDENT = ' ' * 4

class DirectoryViewItem:

    def __init__(self, path, parent):
        """

          path : initialized path object
          parent : the parent DirectoryView of this view
        """
        self._path = path
        self._parent = parent

    def getPythonName(self):
        """Return the name of the directory item as a python name.
        """
        return self._path.namebase

    def getParent(self):
        return self._parent

    def hasParent(self):
        return self._parent is not None
    
    def getRoot(self):
        item = self
        while 1:
            if not item.hasParent():
                return item
            item = item.getParent()
        
class DirectoryView (DirectoryViewItem):

    def getDirectoryViews(self):
        """Return all subdirectory views contained in this directory view.
        """
        return [ DirectoryView(dir, self) for dir in self._path.dirs()
                 if dir.name != 'CVS']

    def getTuplePath(self):
        """Get a tuple representation of the path from root of DirectoryViews
        to this one.
        """
        l = []
        node = self
        while 1:
            if node._parent is None:
                break
            l.append(node.getPythonName())
            node = node._parent
        l.reverse()
        return tuple(l)
        
    def __getitem__(self, name):
        if name == 'CVS':
            raise KeyError, 'Invalid item %s' % name
        item_path = self._path / name
        if not item_path.exists():
            raise KeyError, 'Item %s does not exist!' % name
        if item_path.isdir():
            return DirectoryView(item_path, self)
        ext = item_path.ext
        if ext == '.py':
            return PythonScript(item_path, self)
        elif ext == '.pt':
            return PageTemplate(item_path, self)
        elif ext == '.form':
            return FormulatorForm(item_path, self)
        raise KeyError, 'Unknown item type %s' % ext

    def _getDirectoryItems(self, pattern, klass):
        """Return all files as DirectoryViewItem instances.
        """
        return [ klass(filename, self) for filename in
                 self._path.files(pattern) ]

    def getPythonScripts(self):
        """Return all python scripts as PythonScript instances.
        """
        return self._getDirectoryItems('*.py', PythonScript)

    def getPageTemplates(self):
        """Return all page templates as PageTemplate instances.
        """
        return self._getDirectoryItems('*.pt', PageTemplate)

    def getFormulatorForms(self):
        """Return all Formulator forms  as FormulatorForm instances.
        """
        return self._getDirectoryItems('*.form', FormulatorForm)

    def createClass(self):
        """Create a class for this view.
        """
        if self._parent:
            base_classes = [ self._parent.getPythonName() ]
        else:
            base_classes = []
        return self.createClassHelper(self.getPythonName(), base_classes)

    def createClassHelper(self, name, base_classes):
        klass = Class(name, base_classes)
    
        for pt in self.getPageTemplates():
            klass.addClassAttribute(pt.createPageTemplateClassAttribute())
            klass.addFile(pt.createPageTemplateFile())

        for form in self.getFormulatorForms():
            klass.addClassAttribute(form.createFormulatorFormClassAttribute())
            klass.addFile(form.createFormulatorFormFile())
            
        for script in  self.getPythonScripts():
            klass.addMethod(script.createMethod())

        return klass
    
class PythonScript(DirectoryViewItem):

    def __init__(self, path, parent):
        super(PythonScript, self).__init__(path, parent)
        self._parameter_str = None
        self._body_lines = None
        self._parse()

    def _parse(self):
        """parse the referenced script file
        """
        result = []
        parameter_str = ''
        param_len = len('##parameters=')
        for line in self._path.lines(retain=False):
            if line.startswith('##parameters='):
                parameter_str = line[param_len:]
                continue
            if line.startswith('##'):
                continue
            line = line.rstrip()
            line = line.replace('context', 'self')
            line = line.replace('container.REQUEST', 'self.REQUEST')
            result.append(line)
        self._parameter_str = parameter_str
        # pop off any extraneous empty lines at the end
        while result[-1].strip() == '':
            result.pop()
        self._body_lines = result
        return

    def getParameterString(self):
        return self._parameter_str

    def getBodyLines(self):
        return self._body_lines

    def createMethod(self):
        """Create a Method instance out of this python script.
        """
        return Method(self.getPythonName(), self.getParameterString(),
                      self.getBodyLines())

class PageTemplate(DirectoryViewItem):
    def __init__(self, path, parent):
        super(PageTemplate, self).__init__(path, parent)
        self._lines = path.lines()

    def createPageTemplateClassAttribute(self):
        return PageTemplateClassAttribute(self.getPythonName())

    def createPageTemplateFile(self):
        return File(self.getPythonName() + '.pt', self._lines)
    
class FormulatorForm(DirectoryViewItem):
    def __init__(self, path, parent):
        super(FormulatorForm, self).__init__(path, parent)
        self._lines = path.lines()

    def createFormulatorFormClassAttribute(self):
        return FormulatorFormClassAttribute(self.getPythonName())

    def createFormulatorFormFile(self):
        return File(self.getPythonName() + '.form', self._lines)

class Context:
    """Context object that keeps track of indentation level.
    It can also be used to track the directory in which files are going
    to be saved, necessary to create the right PageTemplateClassAttribute code.
    """
    def __init__(self, level, files_dir):
        self.level = level
        self.files_dir = files_dir

    def indented(self):
        return Context(self.level + 1, self.files_dir)
    
class Code:

    def __init__(self, name):
        self._name = name
        return

    def getName(self):
        return self._name
    
    def generateCodeString(self, context=None):
        if context is None:
            context = Context(0, path('/tmp'))
        return '\n'.join(self.generateCodeLines(context)) + '\n'

    def __cmp__ ( self, other ):
        return cmp(self._name, other._name)

class Package (Code):

    def __init__(self, name):
        super(Package, self).__init__(name)
        self._modules = {}
        self._packages = {}

    def addModule(self, module):
        self._modules[module._name] = module

    def addPackage(self, package):
        self._packages[package._name] = package

    def hasModule(self, name):
        return self._modules.has_key(name)

    def getModule(self, name):
        return self._modules[name]

    def hasPackage(self, name):
        return self._packages.has_key(name)

    def getPackage(self, name):
        return self._packages[name]
    
    def save(self, destination_dir):
        """Create a package in the specified directory.
        """
        ppath = destination_dir / self._name
        ppath.mkdir()
        init_path = ppath / '__init__.py'
        init_path.write_lines(['# this is a package'])
        for module in self._modules.values():
            module.save(ppath)
        for package in self._packages.values():
            package.save(ppath)
            
class Module (Code):

    def __init__(self, name):
        super(Module, self).__init__(name)
        self._classes = []
        self._imports = []
        self._from_imports = []
        self.addFromImport('AccessControl', 'ClassSecurityInfo')
        self.addFromImport('Globals', 'InitializeClass')
        self.addFromImport('Products.PageTemplates.PageTemplateFile',
                           'PageTemplateFile')
        self.addFromImport('Products.Formulator.FormulatorFormFile',
                           'FormulatorFormFile')
        
    def addClass(self, klass):
        if self.hasClass(klass._name):
            raise KeyError, 'Class name %s already used.' % klass._name
        self._classes.append(klass)

    def hasClass(self, name):
        for c in self._classes:
            if c._name == name:
                return True
        return False

    def addImport(self, dotted_name):
        self._imports.append(dotted_name)
        return

    def addFromImport(self, dotted_name, name):
        self._from_imports.append( (dotted_name, name) )
        return

    def generateCodeLines(self, context):
        """Generate the lines of code for a module, indented to level in
        context.
        """
        result = []
        # XXX eventually include doc-strings
        # generate import statements first
        for imp in self._imports:
            result.append('import %s' % imp)
        # generate from ... import statements
        for imp in self._from_imports:
            result.append('from %s import %s' % imp)
        # output class definitions
        for klass in self._classes:
            result.append('')
            result.extend(klass.generateCodeLines(context))
        return result

    def needFilesDirectory(self):
        for klass in self._classes:
            if klass.getFiles():
                return True
        return False
    
    def save(self, destination_dir):
        """Create a module in the specified directory.
        """
        mpath = destination_dir / (self._name + '.py')
        if self.needFilesDirectory():
            files_dirname = self._name + '_pt'
            fpath = destination_dir / files_dirname
            fpath.mkdir()
            context = Context(0, fpath)
        else:
            context = Context(0, None)
        mpath.write_lines(self.generateCodeLines(context))
        for klass in self._classes:
            for file in klass.getFiles():
                file.save(fpath)
                
class Class (Code):

    def __init__(self, name, base_names):
        super(Class, self).__init__(name)
        self._base_names = base_names
        self._methods = []
        self._class_attributes = []
        self._files = []
        
    def addMethod(self, method):
        self._methods.append(method)

    def addClassAttribute(self, attr):
        self._class_attributes.append(attr)

    def addFile(self, file):
        self._files.append(file)

    def getFiles(self):
        return self._files

    def getBaseClasses(self):
        return self._base_names
    
    def _getClassLine(self):
        """Return the class ... line as string.
        """
        if self._base_names:
            return "class %s(%s):" % (self._name, ', '.join(self._base_names))
        else:
            return "class %s:" % self._name

    def addInitializeClass(self, result, context):
        result.append('')
        result.append(indentLine('InitializeClass(%s)' % self._name, context))
        
    def generateCodeLines(self, context):
        """Generate the lines of code for a class,
        indented to level in context.
        """
        result = [indentLine(self._getClassLine(), context)]
        indented_context = context.indented()
        result.append('')
        result.append(indentLine('security = ClassSecurityInfo()',
                                 indented_context))
        # handle the case where the class is empty
        if not self._class_attributes and not self._methods:
            self.addInitializeClass(result, context)
            return result
        attributes = self._class_attributes[:]
        attributes.sort()
        # class has attributes and/or methods
        for class_attribute in attributes:
            result.append('')
            result.extend(class_attribute.generateCodeLines(indented_context))
        methods = self._methods[:]
        methods.sort()
        for method in methods:
            result.append('')
            result.extend(method.generateCodeLines(indented_context))
        self.addInitializeClass(result, context)
        return result

class Method (Code):

    def __init__(self, name, parameter_str, body_lines):
        super(Method, self).__init__(name)
        self._parameter_str = parameter_str
        self._body_lines = body_lines

    def _getDefLine(self):
        """Return the def ... line as string.

        Will include the complete parameter list and without indentation.
        """
        if self._parameter_str:
            return "def %s(self, %s):" % (self._name, self._parameter_str)
        else:
            return "def %s(self):" % self._name

    def _getSecurityLine(self):
        """Return the declareProtected line as string.
        """
        return ("security.declareProtected('View management screens', '%s')" %
                self._name)
        
    def generateCodeLines(self, context):
        """Generate the lines of code for a method,
        indented to level in context.
        """
        result = [
            indentLine(self._getSecurityLine(), context),
            indentLine(self._getDefLine(), context)]
        result.extend(indentLines(self._body_lines, context.indented()))
        return result

class ZopeClassAttribute(Code):
    def __init__(self, name):
        self._name = name

    def _getSecurityLine(self):
        """Return the declareProtected line as string.
        """
        return ("security.declareProtected('View management screens', '%s')" %
                self._name)

    def _generateCodeLinesHelper(self, context, factory_name, extension):
        files_dir = context.files_dir
        filepath = "%s/%s.%s" % (files_dir.name, self._name, extension)
        # __name__ does not need to be generated as this is
        # based on the filepath anyway
        rhs = '%s("%s", globals())' % (factory_name, filepath)
        return [
            indentLine(self._getSecurityLine(), context),
            indentLine('%s = %s' % (self._name, rhs), context)]

class PageTemplateClassAttribute(ZopeClassAttribute):
    # doesn't inherit from ClassAttribute because we can't know rhs on
    # construction time

    def __init__(self, name):
        self._name = name
        
    def generateCodeLines(self, context):
        return self._generateCodeLinesHelper(
            context, 'PageTemplateFile', 'pt')
    
class FormulatorFormClassAttribute(ZopeClassAttribute):
    def __init__(self, name):
        self._name = name

    def generateCodeLines(self, context):
        return self._generateCodeLinesHelper(
            context, 'FormulatorFormFile', 'form')
    
class File:
    def __init__(self, name, lines):
        self._name = name
        self._lines = lines

    def save(self, destination_dir):
        """Create a module in the specified directory.
        """
        (destination_dir / self._name).write_lines(self._lines)

def indentLine(line, context):
    level = context.level
    if not line:
        return line
    return INDENT * level + line

def indentLines(lines, context):
    return [indentLine(line, context) for line in lines]
