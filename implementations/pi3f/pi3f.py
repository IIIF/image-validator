#egg_cache = "/path/to/egg_cache"
import os
#os.environ['PYTHON_EGG_CACHE'] = egg_cache

import json
import bottle
from bottle import Bottle, route, run, request, response, abort, error, redirect

import urllib
import glob
import hashlib

from cacher import FileSystemCacher
from resolver import FileSystemResolver
from authHandler import OAuthHandler, NullAuthHandler, BasicAuthHandler
from imageRequest import ImageRequest

class Config(object):

    def __init__(self, info):
        for (k,v) in info.items():
            setattr(self, k, v)
        nf = []
        for f in self.FILEDIRS:
            nf.append(os.path.join(self.HOMEDIR, f))
        self.FILEDIRS = nf
        self.CACHEDIR = os.path.join(self.HOMEDIR, self.CACHEDIR)
        self.UPLOADDIR = os.path.join(self.HOMEDIR, self.UPLOADDIR)
        self.UPLOADLINKDIR = os.path.join(self.UPLOADDIR, self.UPLOADLINKDIR)
        self.BASEPREF = self.BASEURL + self.PREFIX
        self.GOOGLE_REDIRECT_URI = self.BASEPREF + self.AUTH_URL_HOME

        self.formats = {'BMP' : 'image/bmp',  
                   'GIF' : 'image/gif', 
                   'JPEG': 'image/jpeg', 
                   'PCX' : 'image/pcx', 
                   'PDF' :  'application/pdf', 
                   'PNG' : 'image/png', 
                   'TIFF': 'image/tiff',
                   'WEBP': 'image/webp'}

        self.extensions = {'bmp' : 'image/bmp',  
                   'gif' : 'image/gif', 
                   'jpg': 'image/jpeg', 
                   'pcx' : 'image/pcx', 
                   'pdf' :  'application/pdf', 
                   'png' : 'image/png', 
                   'tif' : 'image/tiff',
                   'webp': 'image/webp'}

        self.content_types = {}
        for (k,v) in self.extensions.items():
            self.content_types[v] = k

        self.jpegQuality = 90            

        # ... Can't pass unicode to cookies :(
        self.COOKIE_NAME = str(self.COOKIE_NAME)
        self.COOKIE_NAME_ACCOUNT = str(self.COOKIE_NAME_ACCOUNT)
        self.COOKIE_SECRET = str(self.COOKIE_SECRET)

        # Other possibilities:
        # cf.DEGRADED_QUALITY = "gray"
        # cf.DEGRADED_QUALITY = "bitonal"
        # cf.AUTH_TYPE = "basic"
        # cf.AUTH_TYPE = "oauth"
        # cf.CLIENT_SECRETS = {'name1':'secret1'}

class ImageApp(object):

    def __init__(self, config="config.json"):
        # Only called once, so can do config in init 
        self.config = self.make_config(config)
     
        # Make our Resolver and Cacher
        self.resolverClass = FileSystemResolver
        self.resolver = self.resolverClass(self)
        self.cacherClass = FileSystemCacher
        self.cacher = self.cacherClass(self)
        if self.config.AUTH_TYPE == "oauth":
            self.auth = OAuthHandler(self)
        elif self.config.AUTH_TYPE == "basic":
            self.auth = BasicAuthHandler(self) 
        else:
            self.auth = NullAuthHandler(self)

    def make_config(self, path):
        fh = file(path)
        data = fh.read()
        fh.close()
        info = json.loads(data)
        return Config(info)

    def send(self, data, status=200, ct="text/plain"):
        response["content_type"] = ct
        response.status = status
        return data

    def handle(self, path):
        # We are responsible for processing the URL into params
        # And checking auth at the appropriate times
        # ImageRequest looks after the params and image

        cf = self.config
        # First check auth
        isAuthed = self.auth.check_auth()
        response['Access-Control-Allow-Origin'] =  '*'
        response['Link'] = '<{0}>;rel="profile"'.format(cf.compliance)

        # Assumption is that there really is no / (even encoded) in an identifier
        # Parse the path
        bits = path.split('/')

        imgReq = ImageRequest(self, path)
        identifier  = imgReq.make_param('identifier', bits.pop(0))
        filename = self.resolver.resolve_identifier(identifier)
 
        if not bits or not bits[0]:
            # Redirect identifier or identifier/ to info.json
            redirect("{0}{1}/info.json".format(cf.BASEPREF, identifier.requested), 303)

        isInfoRequest = bits[-1] == "info.json"
        if not isAuthed and not identifier.degraded:
            if isInfoRequest:
                if cf.DEGRADED_NOACCESS:
                    # No access is special degraded
                    redirect('{0}{1}/info.json'.format(cf.BASEPREF, cf.AUTH_URL_NOACCESS_ID))
                else:
                    # Or redirect to degraded  
                    redirect('{0}{1}{2}/info.json'.format(cf.BASEPREF, identifier.value, cf.DEGRADED_IDENTIFIER))
            else:
                # Block access to images
                abort(401, identifier.make_error_message("Not Authenticated"))

        # Early Cache Check
        if self.cacher.exists(path):
            # Will only ever be canonical, otherwise would have redirected
            response['Link'] += ', <{0}{1}>;rel="canonical"'.format(cf.BASEPREF, path)
            return self.cacher.send_file(path)                    

        image = imgReq.make_image(filename)

        rg = bits.pop(0)
        if rg == "info.json":
            # does not exist, otherwise cache check would have caught it
            image.make_info()
            image.close()
            return self.cacher.send_file(identifier.value + "/info.json")

        # From here on, we're only pixel requests
        imgReq.make_param('region', rg)
        if bits:
            imgReq.make_param('size', bits.pop(0))
        else:
            imgReq.make_param('size', '')

        if bits:
            imgReq.make_param('rotation', bits.pop(0))
        else:
            imgReq.make_param('rotation', '')

        if bits:
            quality = bits.pop(0)
            dotidx = quality.rfind('.')
            if dotidx > -1:
                format = quality[dotidx+1:]
                quality = quality[:dotidx]
            else:
                imgReq.make_param('format', '')
            imgReq.make_param('quality', quality)
            imgReq.make_param('format', format)
        else:
            imgReq.make_param('quality', '')              

        if bits:
            # Extra cruft after the format :(
            imgReq.make_param('unknown', '/'.join(bits))

        image.cache_info()           
        imgReq.configure_params()

        if not imgReq.isCanonical():
            new_url = cf.BASEPREF + imgReq.canonicalize()
            response['Link'] += ', <{0}>;rel="canonical"'.format(new_url)
            redirect(new_url, 301)

        # Process and send the image!
        image.process(imgReq)
        return self.cacher.send_file(path)



    def handle_submit(self):
        imgurl = request.query.get('url', '')
        if not imgurl:
            # Need a url
            abort(400, "Missing required parameter: url")

        # cache check
        md = hashlib.md5(imgurl)
        imgid = md.hexdigest()
        done = glob.glob("{0}*".format(os.path.join(cf.UPLOADDIR, imgid)))
        if not done:
            # fetch URL
            fh = urllib.urlopen(imgurl)
            ct = fh.headers['content-type']
            if ct.find('image/') == -1:
                # Not an image!
                abort(400, "That resource is not an image")
            data = fh.read()
            fh.close()

            # store the url / hash somewhere
            fn = os.path.join(cf.UPLOADLINKDIR, "{0}.url.txt".format(imgid))
            fh = file(fn, 'w')
            fh.write(imgurl)
            fh.close()

            ext = cf.content_types.get(ct, 'jpg')
            filename = "{0}.{1}".format(imgid, ext)
            fn = os.path.join(cf.UPLOADDIR, filename)
            fh = file(fn, 'w')
            fh.write(data)
            fh.close()

            files = os.listdir(cf.UPLOADDIR)
            if len(files) > cf.MAXUPLOADFILES:
                # trash oldest one
                mtime = lambda f: os.stat(os.path.join(cf.UPLOADDIR, f)).st_mtime
                ofiles = list(sorted(files, key=mtime))
                os.remove(os.path.join(cf.UPLOADDIR, ofiles[0]))

        link = cf.BASEPREF + imgid
        redirect(link+'/info.json')

    def opts(self, *args, **kw):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = "GET,OPTIONS"
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Authorization'
        return self.send("", ct="text/plain")

    def debug_list(self):
        return self.send(repr(self.resolver.identifiers), status=200, ct="application/json");

    def dispatch_views(self):
        # Auth and Submission
        cf = self.config
        if cf.AUTH_TYPE:
            # must support login and token
            self.app.route('/{0}'.format(cf.AUTH_URL_LOGIN), ["GET"], getattr(self.auth, "login", self.not_implemented))               
            self.app.route('/{0}'.format(cf.AUTH_URL_TOKEN), ["GET"], getattr(self.auth, "get_iiif_token", self.not_implemented))
            if cf.AUTH_URL_LOGOUT:
                self.app.route('/{0}'.format(cf.AUTH_URL_LOGOUT), ["GET"], getattr(self.auth, "logout", self.not_implemented)) 
            if cf.AUTH_URL_HOME:
                self.app.route('/{0}'.format(cf.AUTH_URL_HOME), ["GET"], getattr(self.auth, "home", self.not_implemented))
            if cf.AUTH_URL_CLIENTCODE:
                self.app.route('/{0}'.format(cf.AUTH_URL_CLIENTCODE), ["POST"], getattr(self.auth, "get_client_code", self.not_implemented))
            if cf.AUTH_URL_NOACCESS_ID:
                self.app.route('/{0}/info.json'.format(cf.AUTH_URL_NOACCESS_ID), ["GET"], getattr(self.auth, "noaccess", self.not_implemented))

        if cf.SUBMIT_URL:
            self.app.route('/submit', ["GET", "POST"], getattr(self, "handle_submit", self.not_implemented))

        if cf.ENABLE_DEBUG_LIST:
            self.app.route('/list', ["GET"], getattr(self, "debug_list", self.not_implemented))

        # Send everything to the one function for pixels and info.json
        self.app.route('/<path:re:.*>', ["GET"], getattr(self, "handle", self.not_implemented))

        # Add OPTIONS support for cross domain preflight
        # Send everything to the one function for OPTIONS
        self.app.route('/<path:re:.*>', ["OPTIONS"], getattr(self, "opts", self.not_implemented))


    def not_implemented(self, *args, **kwargs):
        """Returns not implemented status."""
        abort(501)

    def empty_response(self, *args, **kwargs):
        """Empty response"""
        pass

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        return self.app


def apache():
    app = ImageApp(config="config_21.json");
    return app.get_bottle_app()

def main():
    host = "localhost"
    port = 8000
    imgapp = ImageApp(config="config_21.json")
    app=imgapp.get_bottle_app()

    bottle.debug(True)
    run(host=host, port=port, app=app)

if __name__ == "__main__":
    main()
else:
    application = apache()
