import os
import glob
from bottle import abort

class Resolver(object):

    def resolve_identifier(self, identifier, app):
        raise NotImplementedError

class FileSystemResolver(Resolver):
    identifiers = {}

    def __init__(self, app):
        self.identifiers = {}

        self.UPLOADDIR = app.config.UPLOADDIR
        self.FILEDIRS = app.config.FILEDIRS
        self.IMAGEFMTS = app.config.IMAGEFMTS

        fns = []        
        for fd in self.FILEDIRS:
            for fmt in self.IMAGEFMTS:
                fns.extend(glob.glob(os.path.join(fd, "*" + fmt))) 

        for fn in fns:
            (d, f) = os.path.split(fn)
            f = f[:-4]
            self.identifiers[f] = fn

    def resolve_identifier(self, identifier):
        idv = identifier.baseValue
        if self.identifiers.has_key(idv):
            return self.identifiers[idv]
        else:
            fns = glob.glob(os.path.join(self.UPLOADDIR, idv) + '.*')
            if fns:
                self.identifiers[identifier] = fns[0]
                return fns[0]
            else:
                abort(404, identifier.make_error_message("Image Not Found"))
