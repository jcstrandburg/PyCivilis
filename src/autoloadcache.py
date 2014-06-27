"""This module provides an auto-loading cache utility class"""

class AutoLoadCache(object):
    """Utility class that maintains a cache, auto loading missing entries via the supplied loader"""

    def __init__(self, loader):
        """Initializes with the supplied loader"""
        self._cache = {}
        self._loader = loader
        
    def get(self, key):
        """Returns the entry associated with the given key, 
        loading it if it's not already present
        """
        try:
            return self._cache[key]
        except KeyError:
            self.set( key, self._loader._cache_load(key))
            return self._cache[key]

    def set(self, key, value):
        """Sets the cache entry for the given key with the given value"""
        self._cache[key] = value
        
    def remove(self, key):
        """Removes the key from the cache"""
        del( self._cache[key])