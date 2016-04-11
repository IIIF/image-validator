
from imageFile import ImageFile
import re
import urllib
from bottle import abort

class ImageRequest(object):
    identifier = None
    region = None
    size = None
    rotation = None
    quality = None
    format = None
    image = None
    path = ""

    def __init__(self, application, path):

        self.path = path
        self.application = application
        self.image = None
        self.canonical = ""

        self.identifier = None
        self.region = None
        self.size = None
        self.rotation = None
        self.quality = None
        self.format = None

        self.param_hash = {'identifier': IdentifierParam,
            'region': RegionParam,
            'size': SizeParam,
            'rotation': RotationParam,
            'quality': QualityParam,
            'format': FormatParam}
        self.unknown = UnknownParam

    def make_param(self, which, value):
        cls = self.param_hash.get(which, self.unknown)
        inst = cls(value, self)
        setattr(self, which, inst)
        return inst

    def configure_params(self):

        for p in self.param_hash.keys():
            getattr(self, p).configure()

    def isCanonical(self):
        if not self.canonical:
            self.canonicalize()
        return self.path == self.canonical

    def canonicalize(self):
        if not self.canonical:
            params = [self.identifier, self.region, self.size, self.rotation, self.quality, self.format]
            canons = [x.canonicalize() for x in params]
            canon = "{0}/{1}/{2}/{3}/{4}.{5}".format(*canons)
            self.canonical = canon
        return self.canonical

    def make_image(self, filename):
        self.image = ImageFile(filename, self.identifier, self.application)
        return self.image

class ImageParam(object):
    value = ""
    name = ""
    valueRe = None
    app = None
    match = None

    def __init__(self, value, req):
        self.requested = value
        m = self.valueRe.match(value)
        if not m:
            abort(400, self.make_error_message())
        else:
            self.match = m
        self.value = value
        self.imageRequest = req

    def make_error_message(self, msg="Unable to parse"):
        return "Error processing {0} parameter value '{1}': {2} ".format(self.name, self.requested, msg)

    def canonicalize(self):
        return self.value

    def configure(self):
        pass

class IdentifierParam(ImageParam):
    valueRe = re.compile("^([^/#?@\[\]]+)$")
    name = "identifier"
    degraded = False
    value = ""
    baseValue = ""

    def __init__(self, value, req):

        value = urllib.unquote(value)
        ImageParam.__init__(self, value, req)
        cf = self.imageRequest.application.config
        if value.endswith(cf.DEGRADED_IDENTIFIER):
            self.baseValue = value.replace(cf.DEGRADED_IDENTIFIER, '')
            self.degraded = True
        else:
            self.baseValue = value
        self.infoValue = urllib.quote(value, '')


class RegionParam(ImageParam):
    valueRe = re.compile("^(full|square|(pct:)?([\d.]+,){3}([\d.]+))$")
    name = "region"
    x = -1
    y = -1
    width = 0
    height = 0

    def canonicalize(self):
        image = self.imageRequest.image
        if self.x == 0 and self.y == 0 and self.width == image.width and self.height == image.height:
            return "full"
        else:
            return "{0},{1},{2},{3}".format(self.x,self.y,self.width,self.height)        

    def configure(self):
        image = self.imageRequest.image
        # Check region
        if self.value == 'full':
            # full size of image
            x=0;y=0;w=image.width;h=image.height
        elif self.value == 'square':
            if image.width > image.height:
                # landscape: square centered in W
                h = image.height
                w = image.height
                y = 0
                x = (image.width / 2) - (image.height / 2)
            else:
                # portrait: square centered in H
                h = image.width
                w = image.width
                x = 0
                y = (image.height / 2) - (image.height / 2)           
        else:
            try:
                (x,y,w,h)=self.value.split(',')
            except:
                abort(400, self.make_error_message())
            if x.startswith('pct:'):
                x = x[4:]
                # convert pct into px
                try:
                    x = float(x) ; y = float(y) ; w = float(w) ; h = float(h)
                    x = int(x / 100.0 * image.width)
                    y = int(y / 100.0 * image.height)
                    w = int(w / 100.0 * image.width)
                    h = int(h / 100.0 * image.height)
                except:
                    abort(400, self.make_error_message())                    
            else:
                try:
                    x = int(x) ; y = int(y) ; w = int(w) ; h = int(h)
                except:
                    abort(400, self.make_error_message()) 
                            
            if (x > image.width):
                abort(400, "X coordinate is outside image")
            elif (y > image.height):
                abort(400, "Y coordinate is outside image")
            elif w < 1:
                abort(400, "Region width is zero")
            elif h < 1:
                abort(400, "Region height is zero") 
            
            if x+w > image.width:
                w = image.width-x            
            if y+h > image.height:
                h = image.height-y            
        self.x = x
        self.y = y
        self.width = w
        self.height = h

class SizeParam(ImageParam):
    valueRe = re.compile("^(full|[\d.]+,|,[\d.]+|pct:[\d.]+|[\d.]+,[\d.]+|![\d.]+,[\d.]+|\^[\d.]+,([\d.]+)?)$")
    name = "size"
    height = 0
    width = 0
    ratio = 0

    def canonicalize(self):
        image = self.imageRequest.image
        region = self.imageRequest.region
        if not region:
            raise NotImplementedError("Must process region before canonicalizing size")

        if (self.width == image.width and self.height == image.height):
            return "full"
        elif (self.width == region.width and self.height == region.height):
            return "full"
        elif self.ratio:
            return "{0},".format(self.width)
        else:
            return "{0},{1}".format(self.width, self.height)

    def configure(self):
        image = self.imageRequest.image
        region = self.imageRequest.region
        if not region:
            raise NotImplementedError("Must process region before configuring size")

        w = region.width
        h = region.height
        size = self.value
        # Output Size
        if size == 'full':
            sizeW = w ; sizeH = h ; ratio = 1
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
                abort(400, self.make_error_message())
        cf = self.imageRequest.application.config
        if cf.MAX_HEIGHT and sizeH > cf.MAX_HEIGHT:
            abort(400, "Requested image height is greater than maximum allowed")
        elif cf.MAX_WIDTH and sizeW > cf.MAX_WIDTH:
            abort(400, "Requested image width is greater than maximum allowed")
        elif cf.MAX_AREA and (sizeW * sizeH) > cf.MAX_AREA:
            abort(400, "Requested image size is greater than maximum number of pixels allowed")

        self.height = sizeH
        self.width = sizeW
        self.ratio = ratio              


class RotationParam(ImageParam):
    valueRe = re.compile("^(!)?([0-9.]+)$")
    name = "rotation"
    mirror = False

    def canonicalize(self):
        return "{0}{1}".format("!" if self.mirror else "", self.rotation)

    def __init__(self, value, app):
        value = value.replace("%21", '!')
        ImageParam.__init__(self, value, app)
        (mirror, rotation) = self.match.groups()        
        self.mirror = mirror == "!"
        try:
            if '.' in rotation:
                rot = float(rotation)
                if rot == int(rot):
                    rot = int(rot)
            else:
                rot = int(rotation)
        except:
            abort(400, self.make_error_message())
        if rot < 0 or rot > 360:
            abort(400, self.make_error_message())            
        rot = rot % 360
        self.rotation = rot
        

class QualityParam(ImageParam):
    valueRe = re.compile("^(default|color|gray|bitonal)$")
    name = "quality"

    def configure(self):
        quals = self.imageRequest.image.qualities
        quals.extend(["default","bitonal"])
        if not self.value in quals:
            abort(400, self.make_error_message("Quality not supported"))
        if self.value == quals[0]:
            self.value = "default"        

class FormatParam(ImageParam):
    valueRe = re.compile("^(jpg|tif|png|gif|jp2|pdf|eps|bmp|webp)$")
    name = "format"

class UnknownParam(ImageParam):
    valueRe = re.compile("^$")
    name = "unknown"
