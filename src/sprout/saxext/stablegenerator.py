import warnings

warnings.warn("sprout.saxext.stablegenerator.StableXMLGenerator is "
              "deprecated. Use sprout.saxext.generator.XMLGenerator instead.",
              DeprecationWarning, 2)

from sprout.saxext.generator import XMLGenerator as StableXMLGenerator
