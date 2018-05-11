import hashlib
import os
import ssl
import stat
import urllib.error
import urllib.request
from typing import Optional

# this allows us to read https files
ssl._create_default_https_context = ssl._create_unverified_context


def signature(name_or_url: str) -> str:
    """ Get a signature for a file that (theoretically) changes over time

    :param name_or_url: directory, file name or url
    :return: Signature
    """
    def file_signature(filepath) -> str:
        st = os.stat(filepath)
        return str((stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime))

    def dir_signature(dirname: str) -> str:
        sigstr = file_signature(dirname)
        for filename in sorted(os.listdir(dirname), key=os.path.normcase):
            sigstr += signature(os.path.join(dirname, filename))
        return hashlib.md5(sigstr.encode()).hexdigest()

    def url_signature() -> str:
        request = urllib.request.Request(name_or_url)
        request.get_method = lambda: 'HEAD'
        response = urllib.request.urlopen(request)
        return str((response.info()['Last-Modified'], response.info()['Content-Length'], response.info().get('ETag')))

    return url_signature() if '://' in name_or_url\
        else dir_signature(name_or_url) if os.path.isdir(name_or_url) \
        else file_signature(name_or_url)
