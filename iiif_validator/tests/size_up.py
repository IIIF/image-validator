from .test import BaseTest, ValidatorError
import random

class Test_Size_Up(BaseTest):
    label = 'Size greater than 100%'
    level = 3
    category = 3
    versions = [u'1.0', u'1.1', u'2.0', u'3.0'] 
    validationInfo = None

    def run(self, result):
        s = random.randint(1100,2000)
        params = {'size': ',%s' % s}
        try:
            img = result.get_image(params)

            self.validationInfo.check('size', img.size, (s,s), result)
            return self.checkSquares(img, s, result)
        except ValidatorError:
            raise
        except:
            if result.version.startswith("3"):
                self.validationInfo.check('size', result.last_status, 400, result, "In version 3.0 image should not be upscaled unless the ^ notation is used.")
            else:    
                self.validationInfo.check('status', result.last_status, 200, result, 'Failed to retrieve upscaled image.')
                raise

        # Now testing vesrion 3.0 upscalling notation        
        self.checkSize(result, (s, s), '^%s,%s' % (s,s), 'Failed to get correct size for an image using the ^ notation')
        self.checkSize(result, (s, s), '^,%s' % (s), 'Failed to get correct size when asking for the height only using the ^ notation')
        self.checkSize(result, (s, s), '^%s,' % (s), 'Failed to get correct size when asking for the width only using the ^ notation')
        # needs a bit more thought as maxium may not be the same as full, should check the info.json
        self.checkSize(result, (1000, 1000), '^max', 'Failed to get max size while using the ^ notation') 
        self.checkSize(result, (2000, 2000), '^pct:200', 'Failed to get correct size when asking for the 200% size image and using the ^ notation') 
        self.checkSize(result, (500, 500), '^!2000,500', 'Failed to get correct size when trying to fit in a box !2000,500 using the ^ notation but not upscallingtrying to fit in a box !2000,500 using the ^ notation but not upscalling') 
        self.checkSize(result, (2000, 2000), '^!2000,3000', 'Failed to get correct size when trying to fit in a box !2000,3000 using the ^notation that requires upscalling.') 

        return result

    def checkSize(self, result, size, sizeStr, message):    
        params = {'size': sizeStr}
        try:
            img = result.get_image(params)
        except:
            self.validationInfo.check('status', result.last_status, 200, result, 'Failed to retrieve upscaled image using ^ notation.')
        self.validationInfo.check('size', img.size, size, result, message)
        self.checkSquares(img, size[0], result)

        
    def checkSquares(self, img, sourceSize, result):            
        match = 0
        sqs = int(sourceSize / 1000.0 * 100)
        for i in range(5):
            x = random.randint(0,9)
            y = random.randint(0,9)
            xi = x * sqs + 13;
            yi = y * sqs + 13;
            box = (xi,yi,xi+(sqs-13),yi+(sqs-13))
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, x, y, result)
            if ok:
                match += 1
            else:
                error = (x,y)      
        if match >= 3:           
            return result
        else:
            raise ValidatorError('color', 1,0, result) 
