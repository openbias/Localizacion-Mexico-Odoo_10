# -*- coding: utf-8 -*-

import tempfile
import base64
import os
import codecs

class TempFileTransaction:
    def __init__(self):
        self.tempfiles = []
        self.fds = []
 
    def _get_prefix(self, prefix):
        return "openerp_cfd_mx_"+prefix+"_"
        
    def create(self, prefix=""):
        fd, fname = tempfile.mkstemp(prefix=self._get_prefix(prefix))
        self.add_file(fname)
        self.fds.append(fd)
        return fname

    def decode_and_save(self, b64str, prefix=""):
        fname = self.create(prefix)
        f = open(fname, "wb")
        f.write(base64.b64decode(b64str))
        f.close()
        return fname
        
    def save(self, txt, prefix=""):
        fname = self.create(prefix)
        f = codecs.open(fname, "w", 'utf-8')
        f.write(txt)
        f.close()
        # with codecs.open(fname,'w',encoding='utf8') as f:
        #     f.write(txt.decode('utf-8'))
        return fname
        
    def load_and_encode(self, fname):
        f = open(fname, "r")
        return base64.b64encode(f.read())
        
    def load(self, fname):
        f = open(fname, "r")
        return f.read()
        
    def add_file(self, fname):
        self.tempfiles.append(fname)
        
    def clean(self):
        for fd in self.fds:
            try:
                os.close(fd)
            except:
                pass
        for fname in self.tempfiles:
            try:
                os.unlink(fname)
            except:
                pass
