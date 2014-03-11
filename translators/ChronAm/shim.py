

try:
    import ljson as json
except:
    import json

from functools import partial
from bottle import Bottle, route, run, request, response, abort, error

from lxml import etree
import uuid
import datetime

import cgitb
import urllib, urllib2, urlparse

import StringIO
import os, sys
import re
import random
import math
from uritemplate import expand


TILE_SIZE=512
SCALE_FACTORS=[1,2,4,8]
FORMATS = ['jpg']
QUALITIES = ['native']
SERVER = "http://localhost:8080"
PFX = ""

INFO_CACHE = {}

class ChronAmShim(object):

    def __init__(self):
        id = "([^/#?@]+)"
        region = "(full|(pct:)?([\d.]+,){3}([\d.]+))"
        size = "(full|[\d.]+,|,[\d.]+|pct:[\d.]+|[\d.]+,[\d.]+|![\d.]+,[\d.]+)"
        rot = "([0-9.+])"
        quality = "(native|color|grey|bitonal)"
        format = "(jpg|tif|png|gif|jp2|pdf|eps|bmp)"        
        #ire = '/' + '/'.join([id,region,size,rot,quality]) + "(." + format + ")?"

        self.idRe = re.compile(id)
        self.regionRe = re.compile(region)
        self.sizeRe = re.compile(size)
        self.rotationRe = re.compile(rot)
        self.qualityRe = re.compile(quality)
        self.formatRe = re.compile(format)        
        self.infoRe = re.compile("/" + id + '/info.(xml|json)')
        self.badcharRe= re.compile('[\[\]?@#/]')
        

    def make_info(self, identifier, date, edition, sequence):

        tgt = "http://chroniclingamerica.loc.gov/lccn/%s/%s/%s/%s.rdf" % (identifier, date, edition, sequence)

        try:
            (imageW, imageH) = INFO_CACHE[tgt]
        except:
            try:
                fh = urllib.urlopen(tgt)
                data = fh.read()
                fh.close()
                dom = etree.XML(data)
                imageW = int(dom.xpath('//exif:width/text()', namespaces={'exif':'http://www.w3.org/2003/12/exif/ns#'})[0])
                imageH = int(dom.xpath('//exif:height/text()', namespaces={'exif':'http://www.w3.org/2003/12/exif/ns#'})[0])
                INFO_CACHE[tgt] = (imageW, imageH)
            except:
                raise
                return {}


        info = {"@id": "%s/%slccn/%s/%s/%s/%s" % (SERVER, PFX, identifier, date, edition, sequence), 
                "@context" : "http://library.stanford.edu/iiif/image-api/1.1/context.json",
                "width":imageW,
                "height":imageH,
                "tile_width": TILE_SIZE,
                "tile_height": TILE_SIZE,
                "scale_factors": SCALE_FACTORS,
                "formats": FORMATS,
                "qualities": QUALITIES}
        return info


    def do_shim(self, identifier, date, edition, sequence, region, size, rotation, quality, format="jpg"):
        # /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024_from_0,0_to_6504,8192.jpg
        # /lccn/sn85066387/1907-03-17/ed-1/seq-4/image_813x1024.jpg
        stuff = [identifier, date, edition, sequence, region, size, rotation, quality, format]

        # Will only get called if all bits are present
        # Otherwise will end at a 404

        if self.regionRe.match(region) == None:               
            return self.error_msg("region", "Region invalid: %r" % region, status = 400)
        if self.sizeRe.match(size) == None:
            return self.error_msg("size", "Size invalid: %r" % size, status = 400)
        if self.rotationRe.match(rotation) == None:
            return self.error_msg("rotation", "Rotation invalid: %r" % rotation, status = 400)       
        if self.qualityRe.match(quality) == None:
            return self.error_msg("quality", "Quality invalid: %r" % quality, status = 400)
        elif self.formatRe.match(format) == None:
            return self.error_msg("format", "Format invalid: %r" % format, status = 400)               

        info = self.make_info(identifier, date, edition, sequence)

        try:
            imageW = info['width']
            imageH = info['height']
        except:
            return self.error_msg("identifier", "Identifier does not identify an Image", status=404)

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
            if x+w > imageW:
                w = imageW-x            
            if y+h > imageH:
                h = imageH-y            

        # Size of part of image
        if size == 'full':
            sizeW = w
            sizeH = h
        else:
            try:
                if size[-1] == ',':    # w,
                    # constrain width to w, and calculate appropriate h
                    sizeW = int(size[:-1])
                    scale = int(sizeW/float(w))
                    sizeH = h * scale     
                elif size[0] == ',':     # ,h
                    # constrain height to h, and calculate appropriate w
                    sizeH = int(size[1:])
                    scale = int(sizeH/float(h))
                    sizeW = w * scale;
                elif size[0] == '!':     # !w,h
                    # Must fit inside w and h
                    (maxSizeW, maxSizeH) = size[1:].split(',')
                    # calculate both ratios and pick smaller
                    ratioW = float(maxSizeW) / w
                    ratioH = float(maxSizeH) / h
                    scale = int(min(ratioW, ratioH))
                    sizeW = w * scale
                    sizeH = h * scale       
                elif size.startswith('pct:'):     #pct: n
                    # n percent of size
                    scale = float(size[4:])/100.0
                    sizeW = w * scale
                    sizeH = h * scale                     
                else:    # w,h    or invalid
                    (sw,sh) = size.split(',')
                    # exactly w and h, deforming aspect
                    return self.error_msg('size', 'arbitrary w,h is not supported by ChronAm')              
            except:
                return self.error_msg('size', 'Size unparseable: %r' % size, status=400)      
        
            sizeW = int(sizeW)
            sizeH = int(sizeH)

        # Process rotation
        try:
            rotation = float(rotation)
        except:
            return self.error_msg('rotation', 'Rotation unparseable: %r' % rotation, status=400)
        if rotation < 0 or rotation > 360:
            return self.error_msg('rotation', 'Rotation must be 0-359.99: %r' % rotation, status=400)            
        if rotation != 0.0:
            return self.error_msg('rotation', 'Rotation is not supported', status=501)
        if not quality in info['qualities']:
            return self.error_msg('quality', 'Quality not supported for this image: %r' % quality, status=501)            

        # Now construct image URL and redirect to it

        target = "http://chroniclingamerica.loc.gov/lccn/%s/%s/%s/%s/image_%sx%s_from_%s,%s_to_%s,%s.jpg" % (
            identifier, date, edition, sequence, sizeW, sizeH, x,y, x+w, y+h)

        response.headers['Location'] = target
        response.status = 302
        return ""


    def do_info(self, identifier, date, edition, sequence):
        response["content_type"] = "application/json"        
        js = self.make_info(identifier, date, edition, sequence)
        out = json.dumps(js, sort_keys=True, indent=2)
        return out

    def dispatch_views(self):
        self.app.route("/%slccn/<identifier>/<date>/<edition>/<sequence>/info.json" % PFX, "GET", self.do_info)
        self.app.route("/%slccn/<identifier>/<date>/<edition>/<sequence>/<region>/<size>/<rotation>/<quality>.<format>" % PFX, "GET", self.do_shim)
        self.app.route("/%slccn/<identifier>/<date>/<edition>/<sequence>/<region>/<size>/<rotation>/<quality>" % PFX, "GET", self.do_shim)


    def after_request(self):
        """A bottle hook to add CORS headers"""
        methods = 'GET'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods


    def error_msg(self, param, msg, status):
        abort(status, "Error with %s: %s" % (param, msg))

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        return self.app


    def run(self, *args, **kwargs):
        """Shortcut method for running kule"""
        kwargs.setdefault("app", self.get_bottle_app())
        run(*args, **kwargs)


def apache():
    # Apache takes care of the prefix
    PFX = ""
    v = ChronAmShim();
    return v.get_bottle_app()

def main():
    mr = ChronAmShim()
    run(host='localhost', port=8080, app=mr.get_bottle_app())


if __name__ == "__main__":
    main()
else:
    application = apache()
