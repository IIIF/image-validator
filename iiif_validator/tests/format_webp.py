from .test import BaseTest, ValidatorError
try:
    # python3
    from urllib.request import Request, urlopen, HTTPError
except ImportError:
    # fall back to python2
    from urllib2 import Request, urlopen, HTTPError

class Test_Format_Webp(BaseTest):
    label = 'WebP format'
    level = 3
    category = 6
    versions = [u'2.0', u'3.0']
    validationInfo = None

    def run(self, result):

        # chrs 8:12 == "WEBP"
        params = {'format': 'webp'}
        url = result.make_url(params)
        # Need as plain string for magic
        try:
            wh = urlopen(url)
        except HTTPError as error:    
            raise ValidatorError('format', 'http response code: {}'.format(error.code), url, result, 'Failed to retrieve webp, got response code {}'.format(error.code))
        img = wh.read()
        wh.close()
        if img[8:12] != "WEBP":
            raise ValidatorError('format', 'unknown', 'WEBP', result)
        else:
            result.tests.append('format')
            return result
