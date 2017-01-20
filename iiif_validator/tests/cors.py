from .test import BaseTest

class Test_Cors(BaseTest):
    label = 'Cross Origin Headers'
    level = 1
    category = 7
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        info = result.get_info();
        cors = ''
        for k,v in result.last_headers.items():
            if k.lower() == 'access-control-allow-origin':
                cors = v
                break
        self.validationInfo.check('CORS', cors, '*', result)
        return result
