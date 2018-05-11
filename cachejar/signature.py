import os
import ssl
import stat
import urllib.error
import urllib.request
from typing import Optional

# this allows us to read https files
ssl._create_default_https_context = ssl._create_unverified_context


def signature(name_or_url: str) -> str:
    """ Get a size / modification signature from a file or URL

    :param name_or_url: file name or url
    :return: Signature
    """
    def file_signature() -> str:
        st = os.stat(name_or_url)
        return str((stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime))

    def url_signature() -> str:
        request = urllib.request.Request(name_or_url)
        request.get_method = lambda: 'HEAD'
        response = urllib.request.urlopen(request)
        return str((response.info()['Last-Modified'], response.info()['Content-Length'], response.info().get('ETag')))

    return url_signature() if '://' in name_or_url else file_signature()
