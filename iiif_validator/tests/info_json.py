
from .test import BaseTest, ValidatorError

class Test_Info_Json(BaseTest):
    label = "Check Image Information"
    level = 0
    category = 1
    versions = ["1.0","1.1","2.0","3.0"]
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
                idField = '@id'
                if result.version[0] == '3':
                    idField = 'id'
                self.validationInfo.check('required-field: {}'.format(idField), idField in info, True, result)
                self.validationInfo.check('type-is-uri: {}'.format(idField), info[idField].startswith('http'), True, result)
                # Check id is same as request URI
                self.validationInfo.check('@id is correct URI', info[idField] == result.last_url.replace('/info.json', ''), True, result, 'Found: {} Expected: {}'.format(info[idField], result.last_url.replace('/info.json', '')))

                self.validationInfo.check('required-field: @context', '@context' in info, True, result)
                if result.version == "1.1":
                    self.validationInfo.check('correct-context', info['@context'], 
                        ["http://library.stanford.edu/iiif/image-api/1.1/context.json", "http://iiif.io/api/image/1/context.json"], result)
                elif result.version[0] == "2":
                    self.validationInfo.check('correct-context', info['@context'], "http://iiif.io/api/image/2/context.json", result)
                elif result.version[0] == "3":
                    self.validationInfo.check('correct-context', info['@context'], "http://iiif.io/api/image/3/context.json", result)
                    self.validationInfo.check('correct-type', info['type'], "ImageService3", result, "Info.json missing required type of ImageService3.")

                
                if int(result.version[0]) >= 2:
                    self.validationInfo.check('required-field: protocol', 'protocol' in info, True, result)
                    self.validationInfo.check('correct-protocol', info['protocol'], 'http://iiif.io/api/image', result)

                if result.version[0] == "2" or result.version[0] == "3":
                    self.validationInfo.check('required-field: profile', 'profile' in info, True, result)
                    profs = info['profile']
                    if result.version[0] == "2":
                        self.validationInfo.check('is-list', type(profs), list, result, 'Profile should be a list.')
                        self.validationInfo.check('profile-compliance', profs[0].startswith('http://iiif.io/api/image/2/level'), True, result)
                    else:    
                        self.validationInfo.check('profile-compliance', profs in ['level0', 'level1', 'level2'], True, result, 'Profile should be one of level0, level1 or level2. https://iiif.io/api/image/3.0/#6-compliance-level-and-profile-document')

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
        except Exception as exception:
            self.validationInfo.check('status', result.last_status, 200, result, "Failed to reach {} due to http status code: {}.".format(result.make_info_url(), result.last_status))
            ct = result.last_headers['content-type']
            scidx = ct.find(';')
            if scidx > -1:
                ct = ct[:scidx]
            self.validationInfo.check('content-type', 'application/json' in result.last_headers['content-type'] or 'application/ld+json' in result.last_headers['content-type'], True, result, 'Content-type for the info.json needs to be either application/json or application/ld+json.')
            raise
