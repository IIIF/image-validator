
egg_cache = "/path/to/egg_cache"
import os
os.environ['PYTHON_EGG_CACHE'] = egg_cache

import json
import bottle
from bottle import Bottle, route, run, request, response, abort, error, redirect, parse_auth, auth_basic

import urllib, urlparse, urllib2

import StringIO
import glob
import re
import math
import sys
import hashlib

try:
    from PIL import Image
except:
    import Image

class Settings(object):
    GOOGLE_API_CLIENT_ID = ''
    GOOGLE_API_CLIENT_SECRET = ''
    REDIRECT_URI = 'http://server/prefix/home'
    GOOGLE_API_SCOPE = 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
    GOOGLE_OAUTH2_URL = 'https://accounts.google.com/o/oauth2/'
    GOOGLE_API_URL = 'https://www.googleapis.com/oauth2/v1/'
settings = Settings()

def check_auth(user, password):
    return user == password

def fail_auth(user, password):
    return False

class ImageApp(object):

    def __init__(self):

        HOMEDIR = "/home/user"
        BASEDIR = HOMEDIR + "path/to/base"
        FILEDIRS = [
            HOMEDIR+"/data/images/"
        ]
        IMAGEFMTS = ['png', 'jpg', 'tif']
        self.CACHEDIR = HOMEDIR+"/data/webcache/"
        self.UPLOADDIR = HOMEDIR+"/data/submitted/"
        self.BASEURL = "http://server/"
        self.PREFIX = "prefix"
        self.BASEPREF = self.BASEURL + self.PREFIX + '/'
        self.TILE_SIZE = 512
        self.DEGRADE_IMAGES = False
        self.DEGRADED_NOACCESS = False
        self.DEGRADED_SIZE = 400
        self.DEGRADED_QUALITY = ""
        # self.DEGRADED_QUALITY = "gray"
        # self.DEGRADED_QUALITY = "bitonal"
        # self.AUTH_TYPE = "basic"
        self.AUTH_TYPE = "oauth"

        self.identifiers = {}
        fns = []        
        for fd in FILEDIRS:
            for fmt in IMAGEFMTS:
                fns.extend(glob.glob(fd + "*" + fmt)) 

        for fn in fns:
            (d, f) = os.path.split(fn)
            f = f[:-4]
            self.identifiers[f] = fn

        self.formats = {'BMP' : 'image/bmp',  
                   'GIF' : 'image/gif', 
                   'JPEG': 'image/jpeg', 
                   'PCX' : 'image/pcx', 
                   'PDF' :  'application/pdf', 
                   'PNG' : 'image/png', 
                   'TIFF' : 'image/tiff'}

        self.extensions = {'bmp' : 'image/bmp',  
                   'gif' : 'image/gif', 
                   'jpg': 'image/jpeg', 
                   'pcx' : 'image/pcx', 
                   'pdf' :  'application/pdf', 
                   'png' : 'image/png', 
                   'tif' : 'image/tiff'}

        self.content_types = {}
        for (k,v) in self.extensions.items():
            self.content_types[v] = k

        self.compliance = "http://iiif.io/api/image/2/level2.json"
        self.context = "http://iiif.io/api/image/2/context.json"
        self.protocol = "http://iiif.io/api/image"

        # encoding param for PIL        
        self.jpegQuality = 90

        id = "([^/#?@]+)"
        region = "(full|(pct:)?([\d.]+,){3}([\d.]+))"
        size = "(full|[\d.]+,|,[\d.]+|pct:[\d.]+|[\d.]+,[\d.]+|![\d.]+,[\d.]+|\^[\d.]+,([\d.]+)?)"
        rot = "(!)?([0-9.]+)$"
        quality = "(default|color|gray|bitonal)"
        format = "(jpg|tif|png|gif|jp2|pdf|eps|bmp)"        

        self.idRe = re.compile(id)
        self.regionRe = re.compile(region)
        self.sizeRe = re.compile(size)
        self.rotationRe = re.compile(rot)
        self.qualityRe = re.compile(quality)
        self.formatRe = re.compile(format)        
        self.infoRe = re.compile("/" + id + '/info.json')
        self.badcharRe= re.compile('[\[\]?@#/]')

    def send_file(self, filename, mt, status=200):
        if not filename.startswith(self.CACHEDIR):
            filename = self.CACHEDIR + filename
        fh = file(filename)
        data = fh.read()
        fh.close()
        return self.send(data, status=status, ct=mt)

    def send(self, data, status=200, ct="text/plain"):
        response["content_type"] = ct
        response.status = status
        return data

    def error(self, status, message=""):
        self.status = status
        response['content_type'] = 'text/plain'
        if message:
            return message
        else:    
            return self.codes[status]
                        
    def error_msg(self, param, msg, status):
        text = "An error occured when processing the '%s' parameter:  %s" % (param, msg)
        response.status = status
        response['content_type'] = 'text/plain'
        return text

    def get_image_file(self, identifier):
        if self.identifiers.has_key(identifier):
            return self.identifiers[identifier]
        else:
            fns = glob.glob(self.UPLOADDIR + identifier + '.*')
            if fns:
                self.identifiers[identifier] = fns[0]
                return fns[0]
            else:
                return ""

    def make_info(self, infoId, image):
        (imageW, imageH) = image.size
        
        if infoId.endswith('-degraded') and self.DEGRADED_SIZE:
            # Make max 400 and add in auth service
            if imageW > imageH:
                ratio = float(self.DEGRADED_SIZE) / imageW
                imageH = int(imageH * ratio)
                imageW = self.DEGRADED_SIZE
            else:
                ratio = float(self.DEGRADED_SIZE) / imageH
                imageW = int(imageW * ratio)
                imageH = self.DEGRADED_SIZE
            all_scales = [1,2]
        else:
            all_scales = [1,2,4,8,16]            

        if image.mode == '' or self.DEGRADED_QUALITY == 'bitonal':
            qualities = [] 
        elif image.mode == 'L' or self.DEGRADED_QUALITY == 'gray':
            qualities = ['gray']     
        else:
            qualities = ['color','gray']            

        sizes = []
        for scale in all_scales:
            sizes.append({'width': imageW / scale, 'height': imageH / scale })
        sizes.reverse()
        info = {
                "@id": "%s%s" % (self.BASEPREF, infoId),
                "@context" : self.context,
                "protocol" : self.protocol,
                "width":imageW,
                "height":imageH,
                "tiles" : [{'width':self.TILE_SIZE, 'scaleFactors': all_scales}],
                "sizes" : sizes,
                "profile": [self.compliance,
                    {
                        "formats":["gif","tif","pdf"],
                        "supports":["canonicalLinkHeader", "profileLinkHeader", "mirroring", "rotationArbitrary", "sizeAboveFull"],
                        "qualities":qualities
                    }
                ]
        }
        if qualities:
            info["profile"][1]["qualities"] = qualities

        if self.AUTH_TYPE == "oauth":
            services = [            
                {'@context': 'http://iiif.io/api/image/2/auth_context.json', '@id':self.BASEPREF+'login', 'profile': 'http://iiif.io/api/image/2/auth/login', 'label': 'Login (%s)' % self.AUTH_TYPE}
                ]
        elif self.AUTH_TYPE == "basic":
            services = [            
                {'@context': 'http://iiif.io/api/image/2/auth_context.json', '@id':self.BASEPREF+'login_basic', 'profile': 'http://iiif.io/api/image/2/auth/login', 'label': 'Login (%s)' % self.AUTH_TYPE},
                ]

        info['service'] = services
        logoutbase = self.BASEPREF.replace("http://", "http://bad:alsobad@")
        info['service'].extend(
            [
                {'@context': 'http://iiif.io/api/image/2/auth_context.json', '@id':logoutbase+'logout', 'profile': 'http://iiif.io/api/image/2/auth/logout', 'label': 'Logout (%s)' % self.AUTH_TYPE},
                {'@context': 'http://iiif.io/api/image/2/auth_context.json', '@id':self.BASEPREF+'token', 'profile': 'http://iiif.io/api/image/2/auth/token'}
                ]
            )

        data = json.dumps(info, sort_keys=True)

        try:
            os.mkdir(self.CACHEDIR + infoId)
        except OSError:
            # directory already exists
            pass
        fh = file(self.CACHEDIR + infoId+'/info.json', 'w')
        fh.write(data)
        fh.close()       
        return info
        
    def watermark(self, image):
        # Do watermarking here
        return image

    def handle_GET(self, path):

        # First check auth
        if self.DEGRADE_IMAGES:
            isAuthed = request.get_cookie("loggedin", secret="abc-123-!@#")   
            authToken = request.headers.get('Authorization', '')
            hasToken = len(authToken) > 0
        else:
            isAuthed = True
            hasToken = True

        degraded = False

        # http://{server}{/prefix}   /{identifier}/{region}/{size}/{rotation}/{quality}{.format}
        bits = path.split('/')

        response['Access-Control-Allow-Origin'] =  '*'

        # Nasty but useful debugging hack
        if len(bits) == 1 and bits[0] == "list":
            return self.send(repr(self.identifiers), status=200, ct="text/plain");

        if bits:
            identifier = bits.pop(0)
            if identifier.endswith('-degraded'):
                undegraded = identifier.replace('-degraded', '')
                degraded = True
            else:
                undegraded = identifier

            if self.idRe.match(identifier) == None:
                return self.error_msg("identifier", "Identifier invalid: %r" % identifier, status=400)
            else:
                # Check []?#@ (will never find / )
                if self.badcharRe.match(identifier):
                    return self.error_msg('identifier', 'Unescaped Characters', status=400)                
                identifier = urllib.unquote(identifier)
                infoId = urllib.quote(identifier, '')
                filename = self.get_image_file(undegraded)
                if not filename:
                    return self.error_msg('identifier', 'Not found: %s' % identifier, status=404)          
        else:
            return self.error_msg("identifier", "Identifier unspecified", status=400)

        response['Link'] = '<%s>;rel="profile"' % self.compliance

        # Early cache check here
        fp = path
        if fp == identifier or fp == "%s/" % identifier:
            response.status = 303
            response['location'] = "%s%s/info.json" % (self.BASEPREF, infoId)
            return ""            
        elif len(fp) > 9 and fp[-9:] == "info.json":
            # Check request headers for application/ld+json
            inacc = request.headers.get('Accept', '')
            if inacc.find('ld+json'):
                mimetype = "application/ld+json"
            else:
                mimetype = "application/json"
        elif len(fp) > 4 and fp[-4] == '.':
            try:
                mimetype = self.extensions[fp[-3:]]
            except:
                # no such format, early break
                return self.error_msg('format', 'Unsupported format', status=400)

        if identifier.find('-degraded') == -1:
            if mimetype.endswith('json'):
                if not hasToken:
                    if self.DEGRADED_NOACCESS:
                        # No access is special degraded
                        return self.send_file(fp, mimetype, status=401)

                        # self.error_msg('auth', 'auth test', status=401)
                        # redirect('%sno-access/info.json' % BASEPREF)
                    else:
                        # Or restrict size to max edge of 400 as degradation   
                        redirect('%s%s-degraded/info.json' % (self.BASEPREF, identifier))
            elif not isAuthed:
                # Block access to images
                return self.error_msg('auth', 'Not authenticated', status=401)

        if os.path.exists(self.CACHEDIR + fp):
            # Will only ever be canonical, otherwise would redirect
            response['Link'] += ', <%s%s>;rel="canonical"' % (self.BASEPREF, fp)
            return self.send_file(fp, mimetype)                    
                    
        if bits:
            region = bits.pop(0)
            if self.regionRe.match(region) == None:
                # test for info.json
                if region == "info.json":
                    # build and return info
                    if inacc.find('ld+json'):
                        mt = "application/ld+json"
                    else:
                        mt = "application/json"
                    if not os.path.exists(infoId +'/'+region):
                        image = Image.open(filename)
                        self.make_info(infoId, image)
                        try:
                            image.close()
                        except:
                            pass
                    return self.send_file(infoId +'/' + region, mt)
                else:                
                    return self.error_msg("region", "Region invalid: %r" % region, status = 400)
        # else is caught by checking identifier in early cache check

        if bits:
            size = bits.pop(0)
            if self.sizeRe.match(size) == None:
                return self.error_msg("size", "Size invalid: %r" % size, status = 400)
        else:
            return self.error_msg("size", "Size unspecified", status=400)

        if bits:
            rotation = bits.pop(0)
            rotation = rotation.replace("%21", '!')
            m = self.rotationRe.match(rotation) 
            if m == None:
                return self.error_msg("rotation", "Rotation invalid: %r" % rotation, status = 400)
            else:
                mirror, rotation = m.groups()
        else:
            return self.error_msg("rotation", "Rotation unspecified", status=400)

        if bits:
            quality = bits.pop(0)
            dotidx = quality.rfind('.')
            if dotidx > -1:
                format = quality[dotidx+1:]
                quality = quality[:dotidx]
            else:
                return self.error_msg("format", "Format not specified but mandatory", status=400)               
            if self.qualityRe.match(quality) == None:
                return self.error_msg("quality", "Quality invalid: %r" % quality, status = 400)
            elif self.formatRe.match(format) == None:
                return self.error_msg("format", "Format invalid: %r" % format, status = 400)
        else:
            return self.error_msg("quality", "Quality unspecified", status=400)                

        # MUCH quicker to load JSON than the image to find h/w
        # Does json already exist?            
        if os.path.exists(self.CACHEDIR+infoId):
            # load JSON info file or image?
            fh = file(self.CACHEDIR + infoId +'/info.json')
            info = json.load(fh)
            fh.close()
            image = None
        else:
            # Need to load it up for the first time!     
            image = Image.open(filename)
            info = self.make_info(infoId, image)
        imageW = info['width']
        imageH = info['height']
                    
        # Check region
        if region == 'full':
            # full size of image
            x=0;y=0;w=imageW;h=imageH
        else:
            try:
                (x,y,w,h)=region.split(',')
            except:
                return self.error_msg('region', 'unable to parse region: %r' % region, status=400)
            if x.startswith('pct:'):
                x = x[4:]
                # convert pct into px
                try:
                    x = float(x) ; y = float(y) ; w = float(w) ; h = float(h)
                    x = int(x / 100.0 * imageW)
                    y = int(y / 100.0 * imageH)
                    w = int(w / 100.0 * imageW)
                    h = int(h / 100.0 * imageH)
                except:
                    return self.error_msg('region', 'unable to parse region: %r' % region, status=400)                     
            else:
                try:
                    x = int(x) ; y = int(y) ; w = int(w) ; h = int(h)
                except:
                    return self.error_msg('region', 'unable to parse region: %r' % region, status=400) 
                            
            if (x > imageW):
                return self.error_msg("region", "X coordinate is outside image", status=400)
            elif (y > imageH):
                return self.error_msg("region", "Y coordinate is outside image", status=400)
            elif w < 1:
                return self.error_msg("region", "Region width is zero", status=400)
            elif h < 1:
                return self.error_msg("region", "Region height is zero", status=400) 
            
            # PIL will create whitespace outside, so constrain
            # Need this info for next step anyway
            if x+w > imageW:
                w = imageW-x            
            if y+h > imageH:
                h = imageH-y            

        # Output Size
        if size == 'full':
            sizeW = w ; sizeH = h
        else:
            try:
                if size[0] == '!':     # !w,h
                    # Must fit inside w and h
                    (maxSizeW, maxSizeH) = size[1:].split(',')
                    # calculate both ratios and pick smaller
                    if not maxSizeH:
                        maxSizeH = maxSizeW
                    ratioW = float(maxSizeW) / w
                    ratioH = float(maxSizeH) / h
                    ratio = min(ratioW, ratioH)
                    sizeW = int(w * ratio)
                    sizeH = int(h * ratio)        
                elif size[0] == '^':  # ^w,[h]

                    # EXPERIMENTAL 2.1 FEATURE

                    sizeW, sizeH = size[1:].split(',')
                    if not sizeH:
                        sizeH = sizeW
                    sizeW = float(sizeW)
                    sizeH = float(sizeH)
                    rw = w / sizeW
                    rh = h / sizeH
                    multiplier = min(rw, rh)
                    minSizeW = sizeW * multiplier
                    minSizeH = sizeH * multiplier                    

                    x = int(((w-minSizeW)/2)+x)
                    y = int(((h-minSizeH)/2)+y)
                    w = int(minSizeW)
                    h = int(minSizeH)
                    sizeW = int(sizeW)
                    sizeH = int(sizeH)
                    ratio = 1
                elif size[-1] == ',':    # w,
                    # constrain width to w, and calculate appropriate h
                    sizeW = int(size[:-1])
                    ratio = sizeW/float(w)
                    sizeH = int(h * ratio)      
                elif size[0] == ',':     # ,h
                    # constrain height to h, and calculate appropriate w
                    sizeH = int(size[1:])
                    ratio = sizeH/float(h)
                    sizeW = int(w * ratio)

                elif size.startswith('pct:'):     #pct: n
                    # n percent of size
                    ratio = float(size[4:])/100
                    sizeW = int(w * ratio)
                    sizeH = int(h * ratio)                         
                    if sizeW < 1:
                        sizeW = 1
                    if sizeH < 1:
                        sizeH = 1
                else:    # w,h    or invalid
                    (sw,sh) = size.split(',')
                    # exactly w and h, deforming aspect (if necessary)
                    sizeW = int(sw)
                    sizeH = int(sh)  
                    # Nasty hack to get the right canonical URI
                    ratioW = sizeW/float(w)
                    tempSizeH = int(sizeH / ratioW)
                    if tempSizeH in [h, h-1, h+1]:
                        ratio = 1
                    else:
                        ratio = 0
            except:
                return self.error_msg('size', 'Size unparseable: %r' % size, status=400)      

        # Process rotation
        try:
            if '.' in rotation:
                rot = float(rotation)
                if rot == int(rot):
                    rot = int(rot)
            else:
                rot = int(rotation)
        except:
            return self.error_msg('rotation', 'Rotation unparseable: %r' % rotation, status=400)
        if rot < 0 or rot > 360:
            return self.error_msg('rotation', 'Rotation must be 0-359.99: %r' % rotation, status=400)            
        # 360 --> 0
        rot = rot % 360

        quals = info['profile'][1]['qualities']
        quals.extend(["default","bitonal"])
        if not quality in quals:
            return self.error_msg('quality', 'Quality not supported for this image: %r not in %r' % (quality, quals), status=501)
        if quality == quals[0]:
            quality = "default"
        
        nformat = format.upper()
        if nformat == 'JPG':
            nformat = 'JPEG'
        elif nformat == "TIF":
            nformat = "TIFF"
        try:
            mimetype = self.formats[nformat]
        except:
            return self.error_msg('format', 'Unsupported format', status=415)

        # Check if URI is not canonical, if so redirect to canonical URI
        # Check disk cache and maybe redirect
        if x == 0 and y == 0 and w == imageW and h == imageH:
            c_region = "full"
        else:
            c_region = "%s,%s,%s,%s" % (x,y,w,h)

        if (sizeW == imageW and sizeH == imageH) or (w == sizeW and h == sizeH):
            c_size = "full"
        elif ratio:
            c_size = "%s," % (sizeW)
        else:
            c_size = "%s,%s" % (sizeW, sizeH)

        c_rot = "!%s" % rot if mirror else str(rot) 
        c_qual = "%s.%s" % (quality, format.lower())
        paths = [infoId, c_region, c_size, c_rot, c_qual]
        fn = os.path.join(*paths)
        new_url = self.BASEPREF + fn
        response['Link'] += ', <%s>;rel="canonical"' % new_url

        if fn != path:
            response['Location'] = new_url
            return self.send("", status=301)

        # Won't regenerate needlessly as earlier cache check would have found it
        # if we're canonical already

        # And finally, process the image!
        if image == None:
            try:
                image = Image.open(filename)
            except IOError:
                return self.error_msg('identifier', 'Unsupported format for base image', status=501)

        if identifier.endswith('-degraded'):
            if self.DEGRADED_SIZE > 0:
                # resize max size
                image = image.resize((info['width'], info['height']))
            if self.DEGRADED_QUALITY:
                nquality = {'gray':'L','bitonal':'1'}[self.DEGRADED_QUALITY]
                image = image.convert(nquality)                
                
        if (w != info['width'] or h != info['height']):
            box = (x,y,x+w,y+h)
            image = image.crop(box)

        if sizeW != w or sizeH != h:
            image = image.resize((sizeW, sizeH))        
        if mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        if rot != 0:
            # NB Rotation in PIL can introduce extra pixels on edges, even for square
            # PIL is counter-clockwise, so need to reverse
            rot = 360 - rot
            try:
                image = image.rotate(rot, expand=1)
            except:
                # old version of PIL without expand
                segx = image.size[0]
                segy = image.size[1]
                angle = radians(rot)
                rx = abs(segx*cos(angle)) + abs(segy*sin(angle))
                ry = abs(segy*cos(angle)) + abs(segx*sin(angle))
                
                bg = Image.new("RGB", (rx,ry), (0,0,0))
                tx = int((rx-segx)/2)
                ty = int((ry-segy)/2)
                bg.paste(image, (tx,ty,tx+segx,ty+segy))
                image = bg.rotate(rot)

        if quality != 'default':
            nquality = {'color':'RGB','gray':'L','bitonal':'1'}[quality]
            image = image.convert(nquality)

        output = StringIO.StringIO()
        try:
            image.save(output,format=nformat, quality=self.jpegQuality)
        except SystemError:
            return self.error_msg('size', 'Unsupported size... tile cannot extend outside image', status=501)
        except IOError:
            return self.error_msg('format', 'Unsupported format for format', status=501)
        contents = output.getvalue()
        output.close()
        
        # Write to disk cache
        for p in range(1,len(paths)):
            pth = os.path.join(self.CACHEDIR, *paths[:p])
            if not os.path.exists(pth):
                os.mkdir(pth, 0775)         
        fh = file(self.CACHEDIR + fn, 'w')
        fh.write(contents)
        fh.close()

        return self.send(contents, ct=mimetype)


    def _get_token(self):
        # Google OAuth2 helpers
        params = {
            'code': request.query.get('code'),
            'client_id': settings.GOOGLE_API_CLIENT_ID,
            'client_secret': settings.GOOGLE_API_CLIENT_SECRET,
            'redirect_uri': settings.REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        payload = urllib.urlencode(params)
        url = settings.GOOGLE_OAUTH2_URL + 'token'
        req = urllib2.Request(url, payload) 
        return json.loads(urllib2.urlopen(req).read())

    def _get_data(self, response):
        params = {
            'access_token': response['access_token'],
        }
        payload = urllib.urlencode(params)
        url = settings.GOOGLE_API_URL + 'userinfo?' + payload
        req = urllib2.Request(url)  # must be GET
        return json.loads(urllib2.urlopen(req).read())



    def login(self):
        # OAuth starts here. This will redirect User to Google
        params = {
            'response_type': 'code',
            'client_id': settings.GOOGLE_API_CLIENT_ID,
            'redirect_uri': settings.REDIRECT_URI,
            'scope': settings.GOOGLE_API_SCOPE,
            'state': request.query.get('next'),
        }
        url = settings.GOOGLE_OAUTH2_URL + 'auth?' + urllib.urlencode(params)
        response['Access-Control-Allow-Origin'] = '*'
        redirect(url)

    @auth_basic(check_auth)
    def login_basic(self):
        auth = request.headers.get('Authorization')
        email,p = parse_auth(auth)        
        response.set_cookie("account", email, secret="abc-123-!@#")
        return self.send("<html><script>window.close();</script></html>", ct="text/html");

    def home(self):
        # OAuth ends up back here from Google. This sets a cookie and closes window
        # to trigger next step
        resp = self._get_token()
        data = self._get_data(resp)

        first = data.get('given_name', '')
        last = data.get('family_name', '')
        email = data.get('email', '')
        name = data.get('name', '')
        pic = data.get('picture', '')
        response.set_cookie("account", email, secret="abc-123-!@#")
        return self.send("<html><script>window.close();</script></html>", ct="text/html");

    def get_test_cookie(self):
        response.set_cookie("loggedin", "test@example.com", secret="abc-123-!@#")
        return self.send("<html><script>window.close();</script></html>", ct="text/html");        

    def get_iiif_token(self):
        # This is the next step -- client requests a token to send to info.json
        # We're going to just copy it from our cookie.
        # JSONP request to get the token to send to info.json in Auth'z header

        callbackFn = request.query.get('callback', '')
        authcode = request.query.get('code', '')
        account = ''
        try:
            account = request.get_cookie('account', secret="abc-123-!@#")
            response.delete_cookie('account')
        except:
            pass
        if not account:
            data = {"error":"client_unauthorized","error_description": "No login details received"}
        else:
            data = {"access_token":account, "token_type": "Bearer", "expires_in": 3600}
            # Set the cookie for the image content
            response.set_cookie('loggedin', account, secret="abc-123-!@#")
        dataStr = json.dumps(data)

        if callbackFn:
            return self.send("%s(%s);" % (callbackFn, dataStr), ct="application/javascript")
        else:
            return self.send(dataStr, ct="application/json")

    def noaccess(self):
        noacc = {"@context": "http://iiif.io/api/image/2/context.json", "@id": BASEPREF+"no-access", "protocol": "http://iiif.io/api/image", "height": 1, "width": 1, "service": {"@context": "http://iiif.io/api/auth/1/context.json", "@id": BASEPREF+"login", "profile":"iiif:auth-service"}}
        response['Access-Control-Allow-Origin'] = '*'
        return self.send(json.dumps(noacc), ct="application/json")

    def logout(self):
        response.delete_cookie("account")
        response.delete_cookie("loggedin")
        response['Access-Control-Allow-Origin'] = '*'
        return self.send("<html><script>window.close();</script></html>", status=401, ct="text/html");

    def get_client_code(self):
        # Should have registration for clients etc, but this is just a reference implementation
        data = {'authorization_code' : 'not-very-secret'}
        dataStr = json.dumps(dataStr)
        return self.send(dataStr, ct="application/json")


    def handle_submit(self):
        imgurl = request.query.get('url', '')
        if not imgurl:
            # Need a url
            abort(400, "Missing required parameter: url")

        # fetch URL
        fh = urllib.urlopen(imgurl)
        ct = fh.headers['content-type']
        if ct.find('image/') == -1:
            # Not an image!
            abort(400, "That resource is not an image")
        data = fh.read()
        fh.close()

        # generate an id
        md = hashlib.md5(imgurl)
        imgid = md.hexdigest()
        ext = self.content_types.get(ct, 'jpg')
        filename = "{0}.{1}".format(imgid, ext)
        fn = os.path.join(self.UPLOADDIR, filename)
        fh = file(fn, 'w')
        fh.write(data)
        fh.close()

        link = self.BASEPREF + imgid
        result = {"url": link}
        return self.send(json.dumps(result), ct="application/json")

    def opts(self, *args, **kw):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = "GET,OPTIONS"
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Authorization'
        return self.send("", ct="text/plain")

    def dispatch_views(self):
        # Auth experiments
        self.app.route('/no-access/info.json', ["GET"], getattr(self, "noaccess", self.not_implemented))
        self.app.route('/login', ["GET"], getattr(self, "login", self.not_implemented))        
        self.app.route('/login_basic', ["GET"], getattr(self, "login_basic", self.not_implemented))        
        self.app.route('/logout', ["GET"], getattr(self, "logout", self.not_implemented)) 
        self.app.route('/home', ["GET"], getattr(self, "home", self.not_implemented))
        self.app.route('/token', ["GET"], getattr(self, "get_iiif_token", self.not_implemented))
        self.app.route('/test_cookie', ["GET"], getattr(self, "get_test_cookie", self.not_implemented))
        self.app.route('/client_code', ["POST"], getattr(self, "get_client_code", self.not_implemented))

        self.app.route('/submit', ["GET", "POST"], getattr(self, "handle_submit", self.not_implemented))

        # Send everything to the one function
        self.app.route('/<path:re:.*>', ["get"], getattr(self, "handle_GET", self.not_implemented))

        # Add OPTIONS support for cross domain preflight
        # Must be better way to do it...
        self.app.route('/no-access/info.json', ["OPTIONS"], getattr(self, "opts", self.not_implemented))
        self.app.route('/login', ["OPTIONS"], getattr(self, "opts", self.not_implemented))        
        self.app.route('/login_basic', ["OPTIONS"], getattr(self, "opts", self.not_implemented))        
        self.app.route('/logout', ["OPTIONS"], getattr(self, "opts", self.not_implemented)) 
        self.app.route('/home', ["OPTIONS"], getattr(self, "opts", self.not_implemented))
        self.app.route('/token', ["OPTIONS"], getattr(self, "opts", self.not_implemented))
        self.app.route('/client_code', ["OPTIONS"], getattr(self, "opts", self.not_implemented))
        self.app.route('/test_cookie', ["OPTIONS"], getattr(self, "opts", self.not_implemented))

        # Send everything to the one function
        self.app.route('/<path:re:.*>', ["OPTIONS"], getattr(self, "opts", self.not_implemented))



    def not_implemented(self, *args, **kwargs):
        """Returns not implemented status."""
        abort(501)

    def empty_response(self, *args, **kwargs):
        """Empty response"""
        

    def error(self, error, message=None):
        """Returns the error response."""
        return json.dumps({"error": error.status_code,
                        "message": error.body or message}, "")

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        return self.app

    def run(self, *args, **kwargs):
        """Shortcut method for running kule"""
        kwargs.setdefault("app", self.get_bottle_app())
        run(*args, **kwargs)

def apache():
    app = ImageApp();
    return app.get_bottle_app()


def main():
    host = "localhost"
    port = 8000
    imgapp = ImageApp()
    app=imgapp.get_bottle_app()

    bottle.debug(True)
    run(host=host, port=port, app=app)

if __name__ == "__main__":
    main()
else:
    application = apache()
