from .test import BaseTest, ValidatorError

class Test_Id_Escaped(BaseTest):
    label = 'Escaped characters processed'
    level = 1
    category = 1
    versions = [u'1.0', u'1.1', u'2.0', u'3.0']
    validationInfo = None

    def run(self, result):
        try:
            idf = result.identifier.replace('-', '%2D')
            url = result.make_url({'identifier':idf})
            data = result.fetch(url)
            self.validationInfo.check('status', result.last_status, 200, result)
            img = result.make_image(data)
            return result
        except Exception as error:
            raise ValidatorError('url-check', str(error), 404, result, 'Failed to get random identifier from url: {}.'.format(url))
