import json
import os
import pickle
import re
import uuid
from typing import Optional, Dict, Any

import jsonasobj
from jsonasobj.jsonobj import as_json

from cachejar.signature import signature


class CacheError(Exception):
    pass


class CacheIndex(jsonasobj.JsonObj):

    class CacheEntry(jsonasobj.JsonObj):
        def __init__(self, sig: Optional[str]=None):
            self.signature = sig
            self.cached_objects: Dict[str, str] = jsonasobj.JsonObj()        # Obj_id --> filename
            super().__init__()

    def __init__(self):
        super().__init__()


class CacheJar:
    cache_index_fname = 'index'

    def __init__(self, keeper: "CacheFactory", appid: str) -> None:
        """ Create an instance that represents cache_dir in cache_path

        :param keeper: owning singleton
        :param appid: application id that owns this jar. Must be convertable into a valid file name.
        """
        self.cache_directory = os.path.join(keeper.cache_root, appid)
        self._cache_directory_index = os.path.join(self.cache_directory, CacheJar.cache_index_fname)
        self._globally_disabled = keeper.disabled
        self._locally_disabled = False
        os.makedirs(self.cache_directory, exist_ok=True)
        if os.path.exists(self._cache_directory_index):
            self._load_index()
        else:
            # _cache maps from a file/url to a CacheEntry, shich is a signature and a set of cached objects
            self._cache = CacheIndex()
            self._update_index()

    @property
    def disabled(self) -> bool:
        return self._globally_disabled or self._locally_disabled

    @disabled.setter
    def disabled(self, val: bool) -> None:
        self._locally_disabled = val

    def _keeper_disabled(self, val: bool) -> None:
        """ Change globally disabled setting """
        self._globally_disabled = val

    @staticmethod
    def _identity(obj_id: Any, *parms: Any, **kwparms: Any):
        return str(obj_id) + (str(parms) if parms else '') + (str(kwparms) if kwparms else '')

    def object_for(self, name_or_url: str, obj_id: Any, *parms: Any, **kwparms: Any) -> Optional[object]:
        """ Return the object representing the supplied URL or file name

        :param name_or_url: name of file or URI associated with the object
        :param obj_id: object identifier
        :param parms: object parameters
        :param kwparms: keyword parameters if any
        :return: object if exists and signature matches
        """
        if name_or_url in self._cache and not self.disabled:
            sig = signature(name_or_url)
            if sig != self._cache[name_or_url].signature:
                self._clear_cache_entry(name_or_url, sig)
            obj_identity = self._identity(obj_id, *parms, **kwparms)
            if obj_identity in self._cache[name_or_url].cached_objects:
                with open(os.path.join(self.cache_directory,
                                       self._cache[name_or_url].cached_objects[obj_identity]), 'rb') as f:
                    return pickle.load(f)
        return None

    def update(self, name_or_url: str, obj: object, obj_id: Any, *parms: Any, **kwparms: Any) -> bool:
        """ Add or update an object in the cache.

        :param name_or_url: file or url associated with object
        :param obj: object that represents name
        :param obj_id: stringifiable object that uniquely represents the item
        :param parms: additional parameters that render object unique
        :param kwparms: keyword params as well
        :return: True if cache was updated, false if unable to or update is not needed
        """
        if self.disabled:
            return False
        obj_identity = obj_identity = self._identity(obj_id, *parms, **kwparms)
        sig = signature(name_or_url)
        if name_or_url not in self._cache:
            self._cache[name_or_url] = CacheIndex.CacheEntry(sig)
        if sig != self._cache[name_or_url].signature:
            self._clear_cache_entry(name_or_url, sig)

        if obj_identity not in self._cache[name_or_url].cached_objects:
            fname = 'A' + str(uuid.uuid4())
            fpath = os.path.join(self.cache_directory, fname)
            with open(fpath, 'wb') as f:
                pickle.dump(obj, f)
            self._cache[name_or_url].cached_objects[obj_identity] = fname
            self._update_index()
            return True
        return False

    def _clear_cache_entry(self, name_or_url: str, new_signature: Optional[str], update_index=True) -> None:
        """ Remove all cache files for the supplied cache entry

        :param name_or_url: entry to clear
        :param new_signature: signature to replace (None means remove entire entry)
        :param update_index: False means we'll catch the update later on
        """
        cache_entry = self._cache[name_or_url]
        for _, fname in cache_entry.cached_objects._items():
            fpath = os.path.join(self.cache_directory, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
        if new_signature:
            self._cache[name_or_url] = CacheIndex.CacheEntry(new_signature)
        else:
            del self._cache[name_or_url]
        if update_index:
            self._update_index()

    def clean(self, name_or_url: str=None, obj_id: Any=None, *parms: Any, **kwparms: Any) -> int:
        """ Remove outdated entries for file or url name or obj_id

        :param name_or_url: File name or url. If present, just remove entries for this file
        :param obj_id: object identifier.  If present, remove entries for it combined with the parameters.
        :param parms: positional parameters.
        :param kwparms: named parameters
        :return: number of entries removed
        """
        nremoved = 0
        obj_identity = obj_identity = self._identity(obj_id, *parms, **kwparms) if obj_id is not None else None
        for ename_or_url, cache_entry in list(self._cache._items()):        # Lists to prevent dynamic update
            if name_or_url is None or ename_or_url == name_or_url:
                for cached_obj_id, fname in list(cache_entry.cached_objects._items()):
                    if obj_identity is None or obj_identity == cached_obj_id:
                        fpath = os.path.join(self.cache_directory, fname)
                        if os.path.exists(fpath):
                            os.remove(fpath)
                        nremoved += 1
                        del self._cache[ename_or_url].cached_objects[cached_obj_id]
                    if not self._cache[ename_or_url].cached_objects:
                        del self._cache[ename_or_url]
        self._update_index()
        return nremoved

    def _update_index(self) -> None:
        """ Update the disk index from the memory file  """
        with open(self._cache_directory_index, 'w') as f:
            f.write(as_json(self._cache))

    def _load_index(self) -> None:
        """ Update the memory file from the disk file  """
        with open(self._cache_directory_index, 'r') as f:
            try:
                self._cache = jsonasobj.load(f)
            except json.decoder.JSONDecodeError:
                self._cache = None
        if self._cache is None:
            raise CacheError(f"cache index has been damaged. Remove {self.cache_directory} and try again")

    def clear(self) -> None:
        """ Clear all cache entries for directory.  If it appears to be a "pure" directory (e.g. it has a valid
        cache index in it, remove and recreate the directory itself to get rid of any orphan entries.

        """
        # Safety - if there isn't a cache directory file, this probably isn't a valid cache
        if not os.path.exists(self._cache_directory_index):
            raise CacheError("Attempt to clear a non-existent cache")

        self._load_index()            # This will fail if the index is not valid
        for name_or_url in list(self._cache):
            self._clear_cache_entry(name_or_url, None, update_index=False)
        self._cache = CacheIndex()
        self._update_index()
        self._load_index()            # Verify that update was successful


class CacheFactory:
    """ Preserve an instance of a cache, allowing applications to reference it as necessary.
    """
    _default_cache_root: str = os.path.abspath(os.path.join(os.path.expanduser('~'), '.cachejar'))

    def __init__(self, cache_root: str=_default_cache_root):
        """ Construct a cache factory instance based on cache root """
        self._caches: Dict[str, CacheJar] = {}  # Map from application to cache
        self._cache_root = cache_root
        os.makedirs(self.cache_root, exist_ok=True)
        self._disabled = False
        for entry in os.listdir(self.cache_root):
            fpath = os.path.join(self.cache_root, entry)
            if os.path.isdir(fpath) and os.path.exists(os.path.join(fpath, 'index')):
                self._caches[entry] = CacheJar(self, entry)

    @property
    def disabled(self) -> bool:
        """ True means caching is globally disabled """
        return self._disabled

    @disabled.setter
    def disabled(self, val: bool) -> None:
        self._disabled = val
        for entry in self._caches.values():
            entry._keeper_disabled(val)

    def clear(self, appid: Any, remove_completely: bool=False) -> None:
        """ Clear out all cache instances for appid """
        appid_str = str(appid)
        instance = self._caches.get(appid_str)
        if instance:
            if remove_completely:
                self._remove_cache_dir(instance, appid_str)
            else:
                instance.clear()

    def cachejar(self, appid: any) -> CacheJar:
        """ Return an instance of a cache for 'appid' """
        appid_str = str(appid)
        if not appid_str:
            raise ValueError("Application id must be supplied")
        if appid_str not in self._caches:
            self._caches[appid_str] = CacheJar(self, appid_str)
        return self._caches[appid_str]

    @property
    def cache_root(self) -> str:
        """ Return path to a collection of one or more cache directories """
        return self._cache_root

    def cache_directory(self, appid: Any) -> Optional[str]:
        """ Return the cache directory for appid

        :param appid: Application id
        """
        appid_str = str(appid)
        if appid_str in self._caches:
            return self._caches[appid_str].cache_directory
        else:
            return None

    def _remove_cache_dir(self, instance: CacheJar, appid: str) -> None:
        foreign_files = []
        for fname in os.listdir(instance.cache_directory):
            if fname == CacheJar.cache_index_fname or re.match(
                    r'A[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$', fname):
                os.remove(os.path.join(instance.cache_directory, fname))
            else:
                foreign_files.append(fname)
        if foreign_files:
            raise CacheError(f"Unable to remove {self.cache_directory} - non-cache files are present")
        else:
            os.rmdir(instance.cache_directory)
            del self._caches[appid]


""" The default cache factory. """
factory = CacheFactory()


def jar(appid: Any) -> CacheJar:
    """ The default jar accessor. """
    return factory.cachejar(appid)
