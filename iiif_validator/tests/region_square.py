from .test import BaseTest, ValidatorError
import random

class Test_Region_Square(BaseTest):
    label = 'Request a square region of the full image.'
    level = level = {u'3.0': 1, u'2.1': 3, u'2.1.1': 1}
    category = 3
    versions = [u'3.0', u'2.1', u'2.1.1'] 
    validationInfo = None

    def run(self, result):
        params = {'region': 'square'}
        try:
            img = result.get_image(params)
        except:
            pass

        # should this be a warning as size extension called full could be allowed
        self.validationInfo.check('square-region', result.last_status, 200, result, "A square region is manditory for levels 1 and 2 in IIIF version 3.0.")
        self.validationInfo.check('square-region', img.size[0], img.size[1], result, "Square region returned a rectangle of unequal lenghts.")
        return result
