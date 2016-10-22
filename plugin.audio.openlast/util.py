# -*- coding: utf-8 -*-

import errno
import os
import unicodedata
import urllib

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def build_url(baseUrl, query):
    return baseUrl + '?' + urllib.urlencode(query)


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.fd = None
        self.pid = os.getpid()

    def acquire(self):
        try:
            # Remove file if it's not removed before
            try:
                os.remove(self.filename)
            except OSError as e:
                if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                    raise

            self.fd = os.open(self.filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Only needed to let readers know who's locked the file
            os.write(self.fd, "%d" % self.pid)
            return 1    # return ints so this can be used in older Pythons
        except OSError:
            self.fd = None
            return 0

    def release(self):
        if not self.fd:
            return 0
        try:
            os.close(self.fd)
            os.remove(self.filename)
            return 1
        except OSError:
            return 0

    def __del__(self):
        self.release()
