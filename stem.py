from ctypes import CDLL, POINTER, Structure, c_char_p, c_int
from threading import Lock

from django.conf import settings

if hasattr(settings, 'LIBSTEMMER_PATH') and settings.LIBSTEMMER_PATH:
    library_path = settings.LIBSTEMMER_PATH
else:
    library_path = 'libstemmer.so'

try:
    libstemmer = CDLL(library_path)
    HAS_LIBSTEMMER = True
except OSError:
    HAS_LIBSTEMMER = False

class CStemmer(Structure):
    pass

if HAS_LIBSTEMMER:
    libstemmer.sb_stemmer_new.argtypes = [c_char_p, c_char_p]
    libstemmer.sb_stemmer_new.restype = POINTER(CStemmer)

    libstemmer.sb_stemmer_stem.argtypes = [POINTER(CStemmer), c_char_p, c_int]
    libstemmer.sb_stemmer_stem.restype = c_char_p

    libstemmer.sb_stemmer_delete.argtypes = [POINTER(CStemmer)]
    libstemmer.sb_stemmer_delete.restype = None

class Stemmer(object):
    def __init__(self, lang, encoding=None):
        self.stemmer = libstemmer.sb_stemmer_new(lang, encoding)
        if not self.stemmer:
            raise RuntimeError('Lang "%s" is not supported by this stemmer' % lang)

        self.mutex = Lock()

    def __del__(self):
        libstemmer.sb_stemmer_delete(self.stemmer)
        # No need to call the parent class, since object.__del__ does not exist

    def stem(self, word):
        if isinstance(word, unicode):
            w = word.encode('utf8')
        else:
            w = word

        # sb_stemmer_stem stemmer is not thread safe
        self.mutex.acquire()
        stem = libstemmer.sb_stemmer_stem(self.stemmer, w.lower(), len(w))
        self.mutex.release()
        return stem

