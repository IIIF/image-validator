from .test import BaseTest, ValidatorError
import urllib, ssl

class Test_Format_Webp(BaseTest):
    label = 'WebP format'
    level = 3
    category = 6
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):

        # chrs 8:12 == "WEBP"
        params = {'format': 'webp'}
        url = result.make_url(params)
        # Need as plain string for magic
        context = ssl._create_unverified_context()
        wh = urllib.urlopen(url, context=context)
        img = wh.read()
        wh.close()
        if img[8:12] != "WEBP":
            raise ValidatorError('format', 'unknown', 'WEBP', result)
        else:
            result.tests.append('format')
            return result
