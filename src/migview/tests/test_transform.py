import unittest
import tempfile
from path import path
from migview import transform
from migview import converter

class TestTransform(unittest.TestCase):

    def setUp(self):
        return

    def tearDown(self):
        pass

    def test_01_base_class_transform(self):
        self.assertEquals(
            ('content', 'content', 'Content'),
            transform.transform(('edit', 'Content')))

    def test_02_base_class_transform_register(self):
        transform.transform_register(
            ('foo', 'bar'),
            ('content', 'content', 'Foo'))
        self.assertEquals(
            ('content', 'content', 'Foo'),
            transform.transform(('foo', 'bar')))

    def test_03_node_class_transform(self):
        self.assertEquals(
            ('content', 'foo', 'Foo'),
            transform.transform(('edit', 'Content', 'Foo')))

    def test_04_node_class_transform(self):
        self.assertEquals(
            ('content', 'bar', 'Bar'),
            transform.transform(('edit', 'Content', 'Bar')))

    def test_05_node_class_multiword_transform(self):
        self.assertEquals(
            ('content', 'hoihoi', 'HoiHoi'),
            transform.transform(('edit', 'Content', 'HoiHoi')))
        
class TestBrowserTree(unittest.TestCase):

    def setUp(self):
        self.test_dir = getViewsPath()
        self.top_view = converter.DirectoryView(self.test_dir, None)
        self.browser_tree = transform.BrowserTree('Products.Silva')
        return

    def tearDown(self):
        pass

    def test_04_createModuleForClassPath(self):
        b = self.browser_tree
        module = b.createModuleForClassPath(
            ('content', 'content', 'ContentView'))
        self.assertEquals('content', module.getName())
        p = b.getBrowserPackage()
        module = p.getPackage('content').getModule('content')
        self.assertEquals('content', module.getName())

    def test_05_addClassForDirectoryView(self):
        b = self.browser_tree
        top_dv = self.top_view
        b.addClassForDirectoryView(top_dv)
        p = b.getBrowserPackage()
        self.assert_(p.hasModule('base'))
        self.assert_(p.getModule('base').hasClass('BaseView'))

    def test_06_addClassForDirectoryView2(self):
        b = self.browser_tree
        top_dv = self.top_view
        dv = top_dv['edit']
        b.addClassForDirectoryView(dv)
        p = b.getBrowserPackage()
        self.assert_(p.hasModule('edit'))
        self.assert_(p.getModule('edit').hasClass('EditView'))
        
    def test_07_addClassForDirectoryView3(self):
        b = self.browser_tree
        top_dv = self.top_view
        dv = top_dv['edit']['Content']
        b.addClassForDirectoryView(dv)
        p = b.getBrowserPackage()
        self.assert_(p.hasPackage('content'))
        self.assert_(p.getPackage('content').hasModule('content'))
        self.assert_(
            p.getPackage('content').getModule('content').
            hasClass('ContentView'))

class TestBrowserSave(unittest.TestCase):

    def setUp(self):
        self.test_dir = getViewsPath()
        self.top_view = converter.DirectoryView(self.test_dir, None)
        self.temp_dir = path(tempfile.mkdtemp())
        self.browser_tree = transform.BrowserTree('Products.Silva')
        self.browser_tree.addClassesForDirectoryViewTree(self.top_view)
        self.package = self.browser_tree.getBrowserPackage()
        self.package.save(self.temp_dir)
        return

    def tearDown(self):
        self.temp_dir.rmtree()
        pass


    def test_01_browser_tree_construction(self):
        browser = self.temp_dir / 'browser'
        content = browser / 'content'
        container = browser / 'container'
        asset = browser / 'asset'
        self.assert_(browser.isdir())
        self.assert_(content.isdir())
        self.assert_(container.isdir())
        self.assert_(asset.isdir())

    def test_02_base_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile

class BaseView:

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

InitializeClass(BaseView)
"""
        #
        module_path = self.temp_dir / 'browser' / 'base.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)

    def test_03_edit_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from Products.Silva.browser.base import BaseView

class EditView(BaseView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test1')
    test1 = PageTemplateFile("edit_pt/test1.pt", globals())

    security.declareProtected('View management screens', 'test2')
    test2 = PageTemplateFile("edit_pt/test2.pt", globals())

    security.declareProtected('View management screens', 'test3')
    test3 = PageTemplateFile("edit_pt/test3.pt", globals())

    security.declareProtected('View management screens', 'testpy')
    def testpy(self):
        return "python test"

InitializeClass(EditView)
"""
        module_path = self.temp_dir / 'browser' / 'edit.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)

    def test_04_content_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from Products.Silva.browser.edit import EditView

class ContentView(EditView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_foo')
    def get_foo(self):
        return 'foo'

InitializeClass(ContentView)
"""
        module_path = self.temp_dir / 'browser' / 'content' / 'content.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)

    def test_05_bar_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from Products.Silva.browser.content.content import ContentView

class BarView(ContentView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_bar')
    def get_bar(self):
        return 'bar'

InitializeClass(BarView)
"""
        module_path = self.temp_dir / 'browser' / 'content' / 'bar.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)

    def test_06_foo_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from Products.Silva.browser.content.content import ContentView
from Products.Silva.browser.public import PublicView

class FooView(ContentView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_data')
    def get_data(self):
        return 'data'

InitializeClass(FooView)

class FooPublicView(PublicView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'test1')
    def test1(self):
        return 'Foo/test1'

InitializeClass(FooPublicView)
"""
        module_path = self.temp_dir / 'browser' / 'content' / 'foo.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)


    def test_07_qux_module(self):
        expected = """\
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Formulator.FormulatorFormFile import FormulatorFormFile
from Products.Silva.browser.content.content import ContentView
from Products.Silva.browser.public import PublicView
from Products.Silva.browser.add import AddView

class QuxView(ContentView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_qux')
    def get_qux(self):
        return 'qux'

InitializeClass(QuxView)

class QuxPublicView(PublicView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_public_qux')
    def get_public_qux(self):
        return 'public qux'

InitializeClass(QuxPublicView)

class QuxAddView(AddView):

    security = ClassSecurityInfo()

    security.declareProtected('View management screens', 'get_add_qux')
    def get_add_qux(self):
        return 'add qux'

InitializeClass(QuxAddView)
"""
        module_path = self.temp_dir / 'browser' / 'content' / 'qux.py'
        created = module_path.bytes()
        self.assertEquals(expected, created)

# XXX doesn't work properly yet as module to import from is not
# calculated correctly
##     def test_08_foo_group_module(self):
##         expected = """\
## from Products.Silva.browser.asset.groups import GroupsView
## from Products.Silva.browser.asset.groups import GroupsAddView

## class FooGroupView(GroupsView):

##     def get_foo_group_edit(self):
##         return 'edit foo group'

## class FooGroupAddView(GroupsAddView):

##     def get_foogroup(self):
##         return 'foo group'
## """
##         module_path = self.temp_dir / 'browser' / 'asset' / 'foogroup.py'
##         created = module_path.bytes()
##         self.assertEquals(expected, created)

def getViewsPath():
    return path(__file__).splitpath()[0] / 'views'

def test_suite():
    suite = unittest.TestSuite()
    for testcase in [TestTransform, TestBrowserTree, TestBrowserSave]:
        suite.addTest(unittest.makeSuite(testcase))
    return suite
    
if __name__ == '__main__':
    unittest.main()
