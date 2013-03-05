# -*- coding: utf-8 -*-
# Copyright (c) 2013  Infrae. All rights reserved.
# See also LICENSE.txt



class Options(object):
    """Pluggable and flexible options access for exporter and importer.
    """
    __slots__ = ('_options', '_defaults')

    def __init__(self, options, defaults):
        if options is None:
            self._options = {}
        else:
            self._options = options
        self._defaults = defaults

    def __setattr__(self, key, value):
        if key in self.__slots__:
            super(Options, self).__setattr__(key, value)
        elif key in self._defaults:
            self._options[key] = value
        else:
            raise AttributeError(key)

    def __getattr__(self, key):
        if key in self._defaults:
            if key in self._options:
                return self._options[key]
            return self._defaults[key]
        raise AttributeError(key)
