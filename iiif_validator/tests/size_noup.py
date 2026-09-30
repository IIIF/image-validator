from .test import BaseTest, ValidatorError
import random

class Test_No_Size_Up(BaseTest):
    label = 'Size greater than 100% should only work with the ^ notation'
    level = 1
    category = 3
    versions = [u'3.0'] 
    validationInfo = None

    def run(self, result):
        s = random.randint(1100,2000)

        # testing version 2.x and 1.x to make sure they aren't upscaled
        self.checkSize(result, '%s,%s' % (s,s))
        self.checkSize(result, ',%s' % (s))
        self.checkSize(result, '%s,' % (s))
        self.checkSize(result, 'pct:200')
        # In 3.0 !w,h must return the largest image that fits without exceeding
        # the region, so !2000,3000 on a 1000x1000 image returns 1000x1000.
        self.checkBestFit(result, '!2000,3000')

        return result

    def checkSize(self, result, sizeStr):    
        params = {'size': sizeStr}
        try:
            img = result.get_image(params)
        except:
            self.validationInfo.check('size-upscalling', result.last_status, 400, result, "In version 3.0 image should only be upscaled using the ^ notation.")
        if result.last_status == 200:
            raise ValidatorError('size-upscalling', result.last_status, '!200', result, 'Retrieving upscailed image succeeded but should have failed as 3.0 requires the ^ for upscalling. Size: {}'.format(sizeStr))

    def checkBestFit(self, result, sizeStr):
        params = {'size': sizeStr}
        try:
            img = result.get_image(params)
        except:
            self.validationInfo.check('status', result.last_status, 200, result, 'Failed to retrieve image using {}; the full size image should be returned without upscaling.'.format(sizeStr))
            raise
        self.validationInfo.check('size', img.size, (1000, 1000), result, 'Size {} should return the full size image without upscaling.'.format(sizeStr))
