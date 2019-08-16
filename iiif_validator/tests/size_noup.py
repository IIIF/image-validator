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

        # testing vesrion 2.x and 1.x to make sure they aren't upscaled
        self.checkSize(result, '%s,%s' % (s,s))
        self.checkSize(result, ',%s' % (s))
        self.checkSize(result, '%s,' % (s))
        self.checkSize(result, 'pct:200') 
        self.checkSize(result, '!2000,3000') 

        return result

    def checkSize(self, result, sizeStr):    
        params = {'size': sizeStr}
        try:
            img = result.get_image(params)
        except:
            self.validationInfo.check('size', result.last_status, 400, result, "In version 3.0 image should only be upscaled using the ^ notation.")
        if result.last_status == 200:
            raise ValidatorError()
