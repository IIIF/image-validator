
import os
import glob
from bottle import abort, request

class Cacher(object):
    pass

class FileSystemCacher(Cacher):

    def __init__(self, app):
        self.application = app
        self.directory = app.config.CACHEDIR

    def cache(self, path, data):
        (dirp, filep) = os.path.split(path)
        paths = dirp.split(os.sep)

        for p in range(1,len(paths)+1):
            pth = os.path.join(self.directory, *paths[:p])
            if not os.path.exists(pth):
                os.mkdir(pth, 0775)         

        if not path.startswith(self.directory):
            path = os.path.join(self.directory, path)

        fh = file(path, 'w')
        fh.write(data)
        fh.close()        

    def exists(self, path):
        if not path.startswith(self.directory):
            path = os.path.join(self.directory, path)
        return os.path.exists(path)


    def fetch(self, path):
        if not path.startswith(self.directory):
            path = os.path.join(self.directory, path)
        fh = file(path)
        data = fh.read()
        fh.close()
        return data

    def generate_media_type(self, path):
        if path.endswith("info.json"):
            # Check request headers for application/ld+json
            inacc = request.headers.get('Accept', '')
            if inacc.find('ld+json') > -1:
                mimetype = "application/ld+json"
            else:
                mimetype = "application/json"
        else:
            # Check in config.extensions
            dotidx = path.rfind('.')
            ext = path[dotidx+1:]
            try:
                mimetype = self.application.config.extensions[ext]
            except:
                abort(400, "Unsupported format: {0}".format(ext))
        return mimetype

    def send_file(self, path, mt="", status=200):
        if not path.startswith(self.directory):
            path = os.path.join(self.directory, path)
        if not mt:
            mt = self.generate_media_type(path)
        fh = file(path)
        data = fh.read()
        fh.close()
        return self.application.send(data, status=status, ct=mt)

