
try:
    from PIL import Image
except:
    import Image

import StringIO
import json

from bottle import abort

class ImageFile(object):

    def __init__(self, filename, identifier, application):        
        self.filename = filename
        self.identifier = identifier
        self.cacher = application.cacher
        self.config = application.config
        self.image = None

        self.height = 0
        self.width = 0
        self.qualities = []
        self.formats = []

        self.degradedWidth = -1
        self.degradedHeight = -1

    def open(self):
        if self.image != None:
            return self.image
        try:
            img = Image.open(self.filename)
        except:
            abort(501, self.identifier.make_error_message("Cannot open file"))
        (imageW, imageH) = img.size
        self.height = imageH
        self.width = imageW
        self.image = img
        return img

    def close(self):
        self.image.close()
        self.image = None

    def process(self, ir):

        image = self.open()
        cf = self.config

        if self.identifier.degraded:
            if cf.DEGRADED_SIZE > 0:
                # resize max size
                if self.width > self.height:
                    ratio = float(cf.DEGRADED_SIZE) / self.width
                    imageH = int(self.height * ratio)
                    imageW = cf.DEGRADED_SIZE
                else:
                    ratio = float(cf.DEGRADED_SIZE) / self.height
                    imageW = int(self.width * ratio)
                    imageH = cf.DEGRADED_SIZE
                image = image.resize((imageW, imageH))
            if cf.DEGRADED_QUALITY:
                nquality = {'gray':'L','bitonal':'1'}[cf.DEGRADED_QUALITY]
                image = image.convert(nquality)                

        # region                
        if (ir.region.width != self.width or ir.region.height != self.height):
            box = (ir.region.x,ir.region.y,ir.region.x+ir.region.width,ir.region.y+ir.region.height)
            image = image.crop(box)
        # size
        if ir.size.width != ir.region.width or ir.size.height != ir.region.height:
            image = image.resize((ir.size.width, ir.size.height))        
        # rotation
        if ir.rotation.mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        if ir.rotation.rotation != 0:
            # NB Rotation in PIL can introduce extra pixels on edges, even for square
            # PIL is counter-clockwise, so need to reverse
            rot = 360 - ir.rotation.rotation
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

        # quality
        if ir.quality.value != 'default':
            nquality = {'color':'RGB','gray':'L','bitonal':'1'}[ir.quality.value]
            image = image.convert(nquality)

        nformat = ir.format.value.upper()
        if nformat == 'JPG':
            nformat = 'JPEG'
        elif nformat == "TIF":
            nformat = "TIFF"
        # Can't save alpha mode in jpeg
        if nformat == 'JPEG' and image.mode == 'P':
            image = image.convert('RGB')

        output = StringIO.StringIO()
        try:
            image.save(output,format=nformat, quality=cf.jpegQuality)
        except SystemError:
            abort(400, imageRequest.size.make_error_message('Unsupported size... tile cannot extend outside image'))
        except IOError:
            abort(501, imageRequest.format.make_error_message('Unsupported output format for base image'))
        contents = output.getvalue()
        output.close()

        self.cacher.cache(ir.canonical, contents)
                    
    def cache_info(self):
        # NB need to cache from the *full* image
        if not self.height:
            cacher = self.cacher
            path = self.identifier.value + "/info.json"
            if cacher.exists(path):
                data = cacher.fetch(path)
                info = json.loads(data)
                self.height = info['height']
                self.width = info['width']
                self.qualities = info['profile'][1]['qualities']
            else:
                self.make_info()

    def make_info(self):

        if not self.height:
            image = self.open()
        (imageW, imageH) = (self.width, self.height)

        cf = self.config
        if cf.DEGRADE_IMAGES and self.identifier.degraded and cf.DEGRADED_SIZE:
            # Make SIZE on long edge
            if imageW > imageH:
                ratio = float(cf.DEGRADED_SIZE) / imageW
                imageH = int(imageH * ratio)
                imageW = cf.DEGRADED_SIZE
            else:
                ratio = float(cf.DEGRADED_SIZE) / imageH
                imageW = int(imageW * ratio)
                imageH = cf.DEGRADED_SIZE

        all_scales = []
        sfn = 0
        sf = 1
        while float(imageH)/sf > cf.MIN_SIZE and float(imageW)/sf > cf.MIN_SIZE: 
            all_scales.append(sf)
            sfn += 1
            sf = 2**sfn

        if image.mode == '' or (cf.DEGRADE_IMAGES and cf.DEGRADED_QUALITY == 'bitonal'):
            qualities = [] 
        elif image.mode == 'L' or (cf.DEGRADE_IMAGES and cf.DEGRADED_QUALITY == 'gray'):
            qualities = ['gray']     
        else:
            qualities = ['color','gray']            
        self.qualities = qualities

        sizes = []
        for scale in all_scales:
            sizes.append({'width': imageW / scale, 'height': imageH / scale })
        sizes.reverse()
        info = {
                "@id": "{0}{1}".format(cf.BASEPREF, self.identifier.value),
                "@context" : cf.context,
                "protocol" : cf.protocol,
                "width": imageW,
                "height": imageH,
                "tiles" : [{'width':cf.TILE_SIZE, 'scaleFactors': all_scales}],
                "sizes" : sizes,
                "profile": [cf.compliance,
                    {
                        "formats":["gif","tif","pdf"],
                        "supports":["regionSquare", "canonicalLinkHeader", "profileLinkHeader", "mirroring", "rotationArbitrary", "sizeAboveFull"],
                        "qualities":qualities
                    }
                ]
        }

        if cf.ATTRIBUTION:
            info['attribution'] = cf.ATTRIBUTION
        if cf.LOGO:
            info['logo'] = cf.LOGO
        if cf.LICENSE:
            info['license'] = cf.LICENSE

        if cf.MAX_WIDTH:
            info['profile'][1]['maxWidth'] = cf.MAX_WIDTH
        if cf.MAX_HEIGHT and cf.MAX_HEIGHT != cf.MAX_WIDTH:
            info['profile'][1]['maxHeight'] = cf.MAX_HEIGHT
        if cf.MAX_AREA:
            info['profile'][1]['maxArea'] = cf.MAX_AREA

        if cf.AUTH_TYPE:
            info['service'] = {'@context': 'http://iiif.io/api/auth/0/context.json', 
                '@id': cf.BASEPREF + cf.AUTH_URL_LOGIN, 
                'profile': 'http://iiif.io/api/auth/0/login', 
                'label': 'Login ({0})'.format(cf.AUTH_TYPE),
                'service': []
                }
            if cf.AUTH_URL_LOGOUT:
                info['service']['service'].append({
                '@id': cf.BASEPREF + cf.AUTH_URL_LOGOUT, 
                'profile': 'http://iiif.io/api/auth/0/logout', 
                'label': 'Logout ({0})'.format(cf.AUTH_TYPE)})
            if cf.AUTH_URL_TOKEN:
                info['service']['service'].append({
                '@id': cf.BASEPREF + cf.AUTH_URL_TOKEN, 
                'profile': 'http://iiif.io/api/auth/0/token'})

        data = json.dumps(info, sort_keys=True)
        self.cacher.cache(self.identifier.value + "/info.json", data)       
        return info
