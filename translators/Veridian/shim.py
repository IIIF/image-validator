
#egg_cache = "/path/to/scripts/egg_cache"
import os
#os.environ['PYTHON_EGG_CACHE'] = egg_cache

import json
import bottle
from bottle import Bottle, route, run, request, response, abort, error, redirect

import urllib, urlparse, urllib2

import StringIO
import glob
import re
import math
import sys

from lxml import etree

BASEURL = 'http://showcase.iiif.io/'
PREFIX = 'shims/veridian/image'
BASEPREF = BASEURL + PREFIX + '/'
CACHEDIR = '/path/to/tmp/image/cache'

VSERVER = "http://cdnc.ucr.edu/cgi-bin/imageserver/imageserver.pl"

TILE_SIZE=512
SCALE_FACTORS=[1,2,4,8]
INFO_CACHE = {}


class ImageApp(object):

    def __init__(self):
        self.cache = {}

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

        self.compliance = "http://iiif.io/api/image/2/level0.json"
        self.context = "http://iiif.io/api/image/2/context.json"
        self.protocol = "http://iiif.io/api/image"
        
        idr = "([^/#?@]+)"
        region = "(full|(pct:)?([\d.]+,){3}([\d.]+))"
        size = "(full|[\d.]+,|,[\d.]+|pct:[\d.]+|[\d.]+,[\d.]+|![\d.]+,[\d.]+|\^[\d.]+,([\d.]+)?)"
        rot = "(!)?([0-9.]+)$"
        quality = "(default|color|gray|bitonal)"
        format = "(jpg|tif|png|gif|jp2|pdf|eps|bmp)"        

        self.idRe = re.compile(idr)
        self.regionRe = re.compile(region)
        self.sizeRe = re.compile(size)
        self.rotationRe = re.compile(rot)
        self.qualityRe = re.compile(quality)
        self.formatRe = re.compile(format)        
        self.infoRe = re.compile("/" + idr + '/info.json')
        self.badcharRe= re.compile('[\[\]?@#/]')

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
        
    def handle_GET(self, path):

        # http://{server}{/prefix}   /{identifier}/{region}/{size}/{rotation}/{quality}{.format}
        bits = path.split('/')

        if bits:
            identifier = bits.pop(0)

            if self.idRe.match(identifier) == None:
                return self.error_msg("identifier", "Identifier invalid: %r" % identifier, status=400)
            else:
                # Check []?#@ (will never find / )
                if self.badcharRe.match(identifier):
                    return self.error_msg('identifier', 'Unescaped Characters', status=400)                
                identifier = urllib.unquote(identifier)
                infoId = urllib.quote(identifier, '')          
        else:
            return self.error_msg("identifier", "Identifier unspecified", status=400)

        response['Link'] = '<%s>;rel="profile"' % self.compliance
        # See: http://mortoray.com/2014/04/09/allowing-unlimited-access-with-cors/
        response['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response['Access-Control-Allow-Credentials'] = 'true'

        # Early cache check here
        fp = path
        if fp == identifier or fp == "%s/" % identifier:
            response.status = 303
            response['location'] = "%s%s/info.json" % (BASEPREF, infoId)
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

                    info = self.get_info(infoId)
                    return self.send(info, status=200, ct=mt)
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
               
        info = self.get_info(infoId)
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

        try:
            quals = info['profile'][1]['qualities']
        except:
            quals = []
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
        new_url = BASEPREF + fn
        response['Link'] += ', <%s>;rel="canonical"' % new_url

        if fn.replace("%7E", '~') != path:
            response['Location'] = new_url
            return self.send("", status=301)

        # generate new URL here
        url = self.make_url(infoId,x,y,w,h,imageW,imageH,sizeW,sizeH,rot,mirror,quality,format)
        response['Location'] = url
        # Use 301 to make clients cache the redirected location
        return self.send("", status=301)


    def get_info(self, infoId):

        # Each cache check
        info = self.cache.get(infoId, {})
        if info:
            return info

        # Need at least image H and W

        info = {                
                "@id": "%s%s" % (BASEPREF, infoId),
                "@context" : self.context,
                "protocol" : self.protocol}

        info2 = self.build_info(infoId)
        info.update(info2)

        imageW = int(info['width'])
        imageH = int(info['height'])

        if not info.has_key('sizes'):
            sizes = []
            for scale in SCALE_FACTORS:
                sizes.append({'width': imageW / scale, 'height': imageH / scale })
            sizes.reverse()
            info['sizes'] = sizes
        if not info.has_key('tiles'):
            info['tiles'] = [{'width':TILE_SIZE, 'scaleFactors': SCALE_FACTORS}]
        if not info.has_key('profile'):
            info['profile'] = [self.compliance]

        return info

    def build_info(self, infoId):
        # Do translation here

        # Check cache first
        cached = os.path.join(CACHEDIR, "%s.xml" % infoId)
        if os.path.exists(cached):
            fh = file(cached)
            data = fh.read()
            fh.close()
        else:
            tgt = "http://cdnc.ucr.edu/cgi-bin/cdnc?a=d&f=XML&d=%s" % (infoId)

            try:
                fh = urllib.urlopen(tgt)
                data = fh.read()
                fh.close()
                fh2 = file(cached, 'w')
                fh2.write(data)
                fh2.close()
            except:
                raise

        dom = etree.XML(data)
        imageW = int(dom.xpath('/VeridianXMLResponse/PageResponse/Page/PageMetadata/PageImageWidth/text()')[0])
        imageH = int(dom.xpath('/VeridianXMLResponse/PageResponse/Page/PageMetadata/PageImageHeight/text()')[0])

        info = {
                "width":imageW,
                "height":imageH       
                }
        return info

    def make_url(self,identifier,x,y,w,h,imageW,imageH,sizeW,sizeH,rot,mirror,quality,format):
        # Do mapping from parsed data to external image URL here

        url = VSERVER + "?color=all&key=&ext=%s&width=%s&crop=%s,%s,%s,%s&oid=%s" % (
            format, sizeW, x,y,w,h,identifier)
        return url


    def dispatch_views(self):
        # Send everything to the one function
        self.app.route('/<path:re:.*>', ["get"], getattr(self, "handle_GET", self.not_implemented))

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
        """Shortcut method"""
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
