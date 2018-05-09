import json
import os
import pickle
import re
import uuid
from typing import Optional, Dict, Union, Any

from cachejar.signature import signature


class CacheError(Exception):
    pass


class CacheJar:
    cache_index_fname = 'index'

    def __init__(self, keeper: "CacheFactory", appid: str) -> None:
        """ Create an instance that represents cache_dir in cache_path

        :param keeper: owning singleton
        :param appid: application id that owns this jar (must be valid filename)
        """
        self.cache_directory = os.path.join(keeper.cache_root, appid)
        self._cache_directory_index = os.path.join(self.cache_directory, CacheJar.cache_index_fname)
        os.makedirs(self.cache_directory, exist_ok=True)
        if os.path.exists(self._cache_directory_index):
            self._load_index()
        else:
            # _cache maps from a file/url to a dictionary of signatures to a dictionary of application_ids to
            # pickled files.
            self._cache: Dict[str, Dict[str, Dict[str, str]]] = {}
            self._update_index()

    def update(self, name_or_url: str, obj: object, obj_id: Any) -> bool:
        """ Add or update an object in the cache.

        :param name_or_url: file or url associated with object
        :param obj: object that represents name
        :param obj_id: object (typically class) that represents the particular object
        :return: True if cache was updated, false if unable to or update is not needed
        """
        sig = signature(name_or_url)
        if sig is not None:
            entry = self._cache.setdefault(name_or_url, {})
            if sig not in entry or str(obj_id) not in entry[sig]:
                fname = 'A' + str(uuid.uuid4())
                fpath = os.path.join(self.cache_directory, fname)
                with open(fpath, 'wb') as f:
                    pickle.dump(obj, f)
                entry.setdefault(sig, {})[str(obj_id)] = fname
                self._update_index()
                return True
        return False

    def clean(self, *, name_or_url: Optional[str]=None, obj_id: Optional[Any]=None) -> int:
        """ Remove all older references for file or url name or obj_id

        :param name_or_url: file name or url.  If present, remove all non-current signatures from the cache.
        :param obj_id: object identifier.  If present, remove non-current signatures for this object or, if name_or_url
        is not supplied all signatures for obj_id from the cace
        :return: number of entries removed
        """
        nremoved = 0
        sig = signature(name_or_url) if name_or_url is not None else None
        for ename_or_url, entries in list(self._cache.items()):        # Lists to prevent dynamic update
            if name_or_url is None or ename_or_url == name_or_url:
                for esig, objs in list(entries.items()):
                    if sig is None or esig != sig:
                        for eobj_id, ename in list(objs.items()):
                            if obj_id is None or eobj_id == str(obj_id):
                                fpath = os.path.join(self.cache_directory, ename)
                                if os.path.exists(fpath):
                                    os.remove(fpath)
                                nremoved += 1
                                del objs[eobj_id]
                    if not objs:
                        del entries[esig]
            if not entries:
                del self._cache[ename_or_url]
        self._update_index()
        return nremoved

    def object_for(self, name_or_url: str, obj_id: Any) -> Optional[object]:
        """ Return the object representing the supplied URL or file name

        :param name_or_url: name of file or URI associated with the object
        :param obj_id: object identifier
        :return: object if exists and signature matches
        """
        if name_or_url not in self._cache:
            return None
        sig = signature(name_or_url)
        if sig is None or sig not in self._cache[name_or_url] or str(obj_id) not in self._cache[name_or_url][sig]:
            return None
        with open(os.path.join(self.cache_directory, self._cache[name_or_url][sig][str(obj_id)]), 'rb') as f:
            return pickle.load(f)

    def _update_index(self) -> None:
        """ Update the disk index from the memory file  """
        with open(self._cache_directory_index, 'w') as f:
            json.dump(self._cache, f, indent="  ")

    def _load_index(self) -> None:
        """ Update the memory file from the disk file  """
        with open(self._cache_directory_index, 'r') as f:
            try:
                self._cache = json.load(f)
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
        for entry in self._cache.values():
            for objects in entry.values():
                for fname in objects.values():
                    fpath = os.path.join(self.cache_directory, fname)
                    if os.path.exists(fpath):
                        os.remove(fpath)
        self._cache = {}
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
        for entry in os.listdir(self.cache_root):
            fpath = os.path.join(self.cache_root, entry)
            if os.path.isdir(fpath) and os.path.exists(os.path.join(fpath, 'index')):
                self._caches[entry] = CacheJar(self, entry)

    def clear(self, appid: Union[object, str], remove_completely: bool=False) -> None:
        """ Clear out all cache instances for appid """
        instance = self._caches.get(appid)
        if instance:
            if remove_completely:
                return self._remove_cache_dir(instance, appid)
            else:
                instance.clear()
            del self._caches[appid]

    def cachejar(self, appid: Union[object, str]) -> CacheJar:
        """ Return an instance of a cache for 'appid' """
        if appid not in self._caches:
            self._caches[appid] = CacheJar(self, appid)
        return self._caches[appid]

    @property
    def cache_root(self) -> str:
        """ Return path to a collection of one or more cache directories """
        return self._cache_root

    def cache_directory(self, appid: Union[object, str]) -> Optional[str]:
        """ Return the cache directory for appid

        :param appid: Application id
        """
        if appid in self._caches:
            return self._caches[appid].cache_directory
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
            os.removedirs(instance.cache_directory)
            del self._caches[appid]


""" The default cache factory. """
factory = CacheFactory()


def jar(appid: Union[object, str]) -> CacheJar:
    return factory.cachejar(appid)
