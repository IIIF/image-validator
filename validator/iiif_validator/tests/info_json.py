
from .test import BaseTest, ValidatorError

class Test_Info_Json(BaseTest):
    label = "Check Image Information"
    level = 0
    category = 1
    versions = ["1.0","1.1","2.0"]
    validationInfo = None

    def __init__(self, info):
        self.validationInfo = info
        
    def run(self, result):
        # Does server have info.json
        try:
            info = result.get_info()
            if info == None:
                raise ValidatorError('info.json is JSON', True, False, result)

            self.validationInfo.check('required-field: width', 'width' in info, True, result)
            self.validationInfo.check('required-field: height', 'height' in info, True, result)
            self.validationInfo.check('type-is-int: height', type(info['height']) == int, True, result)
            self.validationInfo.check('type-is-int: width', type(info['width']) == int, True, result)

            # Now switch on version
            if result.version == "1.0":
                self.validationInfo.check('required-field: identifier', 'identifier' in info, True, result)                
            else:

                self.validationInfo.check('required-field: @id', '@id' in info, True, result)
                self.validationInfo.check('type-is-uri: @id', info['@id'].startswith('http'), True, result)
                # Check id is same as request URI
                self.validationInfo.check('@id is correct URI', info['@id'] == result.last_url.replace('/info.json', ''), True, result)

                self.validationInfo.check('required-field: @context', '@context' in info, True, result)
                if result.version == "1.1":
                    self.validationInfo.check('correct-context', info['@context'], 
                        ["http://library.stanford.edu/iiif/image-api/1.1/context.json", "http://iiif.io/api/image/1/context.json"], result)
                elif result.version[0] == "2":
                    self.validationInfo.check('correct-context', info['@context'], "http://iiif.io/api/image/2/context.json", result)
                
                if int(result.version[0]) >= 2:
                    self.validationInfo.check('required-field: protocol', 'protocol' in info, True, result)
                    self.validationInfo.check('correct-protocol', info['protocol'], 'http://iiif.io/api/image', result)

                if result.version[0] == "2":
                    self.validationInfo.check('required-field: profile', 'profile' in info, True, result)
                    profs = info['profile']
                    self.validationInfo.check('is-list', type(profs), list, result)
                    self.validationInfo.check('profile-compliance', profs[0].startswith('http://iiif.io/api/image/2/level'), True, result)

                    if 'sizes' in info:
                        sizes = info['sizes']
                        self.validationInfo.check('is-list', type(sizes), list, result)
                        for sz in sizes:
                            self.validationInfo.check('is-object', type(sz), dict, result)
                            self.validationInfo.check('required-field: height', 'height' in sz, True, result)
                            self.validationInfo.check('required-field: width', 'width' in sz, True, result)
                            self.validationInfo.check('type-is-int: height', type(sz['height']), int, result)
                            self.validationInfo.check('type-is-int: width', type(sz['width']), int, result)

                    if 'tiles' in info:
                        tiles = info['tiles']
                        self.validationInfo.check('is-list', type(tiles), list, result)
                        for t in tiles:
                            self.validationInfo.check('is-object', type(t), dict, result)
                            self.validationInfo.check('required-field: scaleFactors', 'scaleFactors' in t, True, result) 
                            self.validationInfo.check('required-field: width', 'width' in t, True, result)                        
                            self.validationInfo.check('type-is-int: width', type(t['width']), int, result)

            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            ct = result.last_headers['content-type']
            scidx = ct.find(';')
            if scidx > -1:
                ct = ct[:scidx]
            self.validationInfo.check('content-type', result.last_headers['content-type'], ['application/json', 'application/ld+json'], result)
            raise