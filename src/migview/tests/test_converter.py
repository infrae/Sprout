from sets import Set
import unittest
import tempfile

from path import path
from migview.converter import DirectoryView, PythonScript, Class,\
     Module, Package, Context

class TestConverter(unittest.TestCase):

    def setUp(self):
        self.test_dir = getViewsPath()
        self.top_view = DirectoryView(self.test_dir, None)
        return

    def tearDown(self):
        pass

    def _script_test(self, script_path, expected):
        python_script = PythonScript(script_path, None)
        created = python_script.createMethod().generateCodeString()
        self.assertEquals(expected, created)
        return

    def _class_test(self, dir_view, expected):
        created = dir_view.createClass().generateCodeString()
        self.assertEquals(expected, created)
        return

    def test_01_init(self):
        self.assertEquals('views', self.top_view.getPythonName())
        return

    def test_02_child_views(self):
        expected = Set(['edit', 'public', 'add'])
        result = Set([dv.getPythonName() for dv in
                      self.top_view.getDirectoryViews()])
        self.assertEquals(expected, result)
        return

    def test_03_child_templates(self):
        expected = Set(['test1', 'test2', 'test3'])
        view = DirectoryView(self.test_dir / 'edit', None)
        result = Set([pt.getPythonName() for pt in view.getPageTemplates()])
        self.assertEquals(expected, result)
        return

    def test_03_1_get_root(self):
        view = DirectoryView(self.test_dir, None)
        self.assertEquals(view.getTuplePath(), view.getRoot().getTuplePath())
        self.assertEquals(view.getTuplePath(),
                          view['edit']['Content'].getRoot().getTuplePath())
        
        
    def test_04_method(self):
        expected = """\
security.declareProtected('View management screens', 'test_script01')
def test_script01(self):
    return 'a'
"""
        self._script_test(self.test_dir / 'test_script01.py', expected)
        return

    def test_05_method_with_parameter(self):
        expected = """\
security.declareProtected('View management screens', 'test_script02')
def test_script02(self, test):
    return test
"""
        self._script_test(self.test_dir / 'test_script02.py', expected)
        return

    def test_06_method_with_parameter_and_default_values(self):
        expected = """\
security.declareProtected('View management screens', 'test_script03')
def test_script03(self, test='test'):
    return test
"""
        self._script_test(self.test_dir / 'test_script03.py', expected)
        return

    def test_07_method_with_parameter_and_binding(self):
        expected = """\
security.declareProtected('View management screens', 'test_script04')
def test_script04(self, test):
    return test
"""
        self._script_test(self.test_dir / 'test_script04.py', expected)
        return

    def test_08_method_with_context(self):
        expected = """\
security.declareProtected('View management screens', 'test_script05')
def test_script05(self):
    req = self.REQUEST
    return req
"""
        self._script_test(self.test_dir / 'test_script05.py', expected)
        return

    def test_09_method_with_container(self):
        expected = """\
security.declareProtected('View management screens', 'test_script06')
def test_script06(self):
    req = self.REQUEST
    return req
"""
        self._script_test(self.test_dir / 'test_script06.py', expected)
        return

    def test_20_class_methods(self):
        expected = """\
class views:

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test_script01')
    def test_script01(self):
        return 'a'

    security.declareProtected('View management screens', 'test_script02')
    def test_script02(self, test):
        return test

    security.declareProtected('View management screens', 'test_script03')
    def test_script03(self, test='test'):
        return test

    security.declareProtected('View management screens', 'test_script04')
    def test_script04(self, test):
        return test

    security.declareProtected('View management screens', 'test_script05')
    def test_script05(self):
        req = self.REQUEST
        return req

    security.declareProtected('View management screens', 'test_script06')
    def test_script06(self):
        req = self.REQUEST
        return req

InitializeClass(views)
"""
        self._class_test(self.top_view, expected)
        return

    def test_21_class_methods_bases(self):
        expected = """\
class Foo(public):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test1')
    def test1(self):
        return 'Foo/test1'

InitializeClass(Foo)
"""
        self._class_test(self.top_view['public']['Foo'], expected)
        return

    def test_22_class_methods_attribs(self):
        # __name__ attribute does not need to be generated, as
        # PageTemplateFile automatically generates this from the path
        expected = """\
class edit(views):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test1')
    test1 = PageTemplateFile("tmp/test1.pt", globals())

    security.declareProtected('View management screens', 'test2')
    test2 = PageTemplateFile("tmp/test2.pt", globals())

    security.declareProtected('View management screens', 'test3')
    test3 = PageTemplateFile("tmp/test3.pt", globals())

    security.declareProtected('View management screens', 'testpy')
    def testpy(self):
        return "python test"

InitializeClass(edit)
"""
        self._class_test(self.top_view['edit'], expected)
        return

    def test_22_1_empty_class(self):
        expected = """\
class Empty(edit):

    security = ClassSecurityInfo()

InitializeClass(Empty)
"""
        self._class_test(self.top_view['edit']['Empty'], expected)
        return

    def test_22a_extraneous_whitespace(self):
        # there are extra newlines at the end of the get_add_qux
        # python script
        expected = """\
class Qux(add):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_add_qux')
    def get_add_qux(self):
        return 'add qux'

InitializeClass(Qux)
"""
        self._class_test(self.top_view['add']['Qux'], expected)

    def test_22b_formulator_attribs(self):
          expected = """\
class FormContent(edit):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'foo')
    foo = FormulatorFormFile("tmp/foo.form", globals())

InitializeClass(FormContent)
"""
          self._class_test(self.top_view['edit']['FormContent'], expected)
          return
        
    def test_23_module_import(self):
        expected = """\
import foo
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
"""
        mod = Module('modfoo')
        mod.addImport('foo')
        created = mod.generateCodeString()
        self.assertEquals(expected, created)
        return

    def test_24_module_from_import(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from bar import foo
"""
        mod = Module('modfoo')
        mod.addFromImport('bar', 'foo')
        created = mod.generateCodeString()
        self.assertEquals(expected, created)
        return

    def test_25_module_both_import(self):
        expected = """\
import baz
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from bar import foo
"""
        mod = Module('modfoo')
        mod.addImport('baz')
        mod.addFromImport('bar', 'foo')
        created = mod.generateCodeString()
        self.assertEquals(expected, created)
        return

    def test_26_module_class(self):
        expected = """\
import baz
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from bar import foo

class edit(views):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test1')
    test1 = PageTemplateFile("tmp/test1.pt", globals())

    security.declareProtected('View management screens', 'test2')
    test2 = PageTemplateFile("tmp/test2.pt", globals())

    security.declareProtected('View management screens', 'test3')
    test3 = PageTemplateFile("tmp/test3.pt", globals())

    security.declareProtected('View management screens', 'testpy')
    def testpy(self):
        return "python test"

InitializeClass(edit)
"""
        mod = Module('modfoo')
        mod.addImport('baz')
        mod.addFromImport('bar', 'foo')
        klass = self.top_view['edit'].createClass()
        mod.addClass(klass)
        # explicitly create context
        context = Context(0, path('/tmp'))
        created = mod.generateCodeString(context)
        self.assertEquals(expected, created)
        return

    def test_27_module_save(self):
        mod = Module('modfoo')
        mod.addImport('baz')
        mod.addFromImport('bar', 'foo')
        klass = self.top_view['edit'].createClass()
        mod.addClass(klass)

        d = path(tempfile.mkdtemp())
        try:
            mod.save(d)
            self.assert_((d / 'modfoo.py').isfile())
            files_dir = d / 'modfoo_pt'
            self.assert_(files_dir.isdir())
            self.assert_((files_dir / 'test1.pt').isfile())
            self.assert_((files_dir / 'test2.pt').isfile())
            self.assert_((files_dir / 'test3.pt').isfile())
        finally:
            d.rmtree()

    def test_28_package_save(self):
        package = Package('packagefoo')
        mod = Module('modfoo')
        mod.addImport('baz')
        mod.addFromImport('bar', 'foo')
        klass = self.top_view['edit'].createClass()
        mod.addClass(klass)
        package.addModule(mod)
        
        d = path(tempfile.mkdtemp())
        try:
            package.save(d)
            package_dir = d / 'packagefoo'
            self.assert_(package_dir.isdir())
            self.assert_((package_dir / '__init__.py').isfile())
            self.assert_((package_dir / 'modfoo.py').isfile())
            files_dir = package_dir / 'modfoo_pt'
            self.assert_(files_dir.isdir())
            self.assert_((files_dir / 'test1.pt').isfile())
            self.assert_((files_dir / 'test2.pt').isfile())
            self.assert_((files_dir / 'test3.pt').isfile())
        finally:
            d.rmtree()

    def test_29_directory_tuple_path(self):
        self.assertEquals(('edit',), self.top_view['edit'].getTuplePath())
        self.assertEquals((), self.top_view.getTuplePath())
        self.assertEquals(('public',), self.top_view['public'].getTuplePath())
        self.assertEquals(('edit', 'Content'),
                          self.top_view['edit']['Content'].getTuplePath())

    def test_30_has_module(self):
        package = Package('foo')
        self.assert_(not package.hasModule('bar'))
        package.addModule(Module('bar'))
        self.assert_(package.hasModule('bar'))

    def test_31_get_module(self):
        package = Package('foo')
        self.assertRaises(KeyError, package.getModule, 'bar')
        package.addModule(Module('bar'))
        self.assertEquals('bar', package.getModule('bar').getName())

    def test_32_has_package(self):
        package = Package('foo')
        self.assert_(not package.hasPackage('bar'))
        package.addPackage(Package('bar'))
        self.assert_(package.hasPackage('bar'))

    def test_33_get_package(self):
        package = Package('foo')
        self.assertRaises(KeyError, package.getPackage, 'bar')
        package.addPackage(Package('bar'))
        self.assertEquals('bar', package.getPackage('bar').getName())

    def test_34_has_class(self):
        module = Module('foo')
        self.assert_(not module.hasClass('Bar'))
        klass = Class('Bar', ['Baz'])
        module.addClass(klass)
        self.assert_(module.hasClass('Bar'))

def getViewsPath():
    return path(__file__).splitpath()[0] / 'views'

def test_suite():
    s = unittest.makeSuite(TestConverter, 'test_')
    return s

if __name__ == '__main__':
    unittest.main()
