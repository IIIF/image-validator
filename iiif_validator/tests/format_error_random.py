from .test import BaseTest, ValidatorError

class Test_Format_Error_Random(BaseTest):
    label = 'Random format gives 400'
    level = 1
    category = 6
    versions = [u'1.0', u'1.1', u'2.0', u'3.0']
    validationInfo = None

    def run(self, result):
        url = result.make_url({'format': self.validationInfo.make_randomstring(3)})
        try:
            error = result.fetch(url)
            self.validationInfo.check('status', result.last_status, [400, 415, 503], result)
            return result
        except Exception as error:
            raise ValidatorError('url-check', str(error), 400, result, 'Failed to get random format from url: {}.'.format(url))
