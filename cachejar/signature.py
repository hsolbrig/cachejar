import os
import ssl
import stat
import urllib.error
import urllib.request
from typing import Optional

# this allows us to read https files
ssl._create_default_https_context = ssl._create_unverified_context


def signature(name_or_url: str) -> Optional[str]:
    """ Get a size / modification signature from a file or URL

    :param name_or_url: file name or url
    :return: Signature or None if unable to locate it
    """
    def file_signature() -> Optional[str]:
        try:
            st = os.stat(name_or_url)
        except FileNotFoundError:
            return None
        return str((stat.S_IFMT(st.st_mode), st.st_size, st.st_mtime))

    def url_signature() -> Optional[str]:
        request = urllib.request.Request(name_or_url)
        request.get_method = lambda: 'HEAD'
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError:
            return None
        return str((response.info()['Last-Modified'], response.info()['Content-Length'], response.info().get('ETag')))

    return None if not isinstance(name_or_url, str) else url_signature() if '://' in name_or_url else file_signature()
