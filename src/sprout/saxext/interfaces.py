
from zope.interface import Interface


class IExporterRegistry(Interface):
    pass


class IXMLProducer(Interface):
    """This adapter provides a XML version for a content.
    """

    def getSettings():
        """Return settings to use for the XML version.
        """
