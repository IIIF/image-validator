from .test import BaseTest, ValidatorError
import random

class Test_No_Size_Up(BaseTest):
    label = 'Size greater than 100% should only work with the ^ notation'
    level = 0
    category = 3
    versions = [u'3.0'] 
    validationInfo = None

    def run(self, result):
        params = {'size': 'full'}
        try:
            img = result.get_image(params)
        except:
            pass

        # should this be a warning as size extension called full could be allowed
        self.validationInfo.check('size', result.last_status != 200, True, result, "Version 3.0 has replaced the size full with max.", warning=True)
        return result

