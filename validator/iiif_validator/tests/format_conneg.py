from .test import BaseTest
try:
    # python3
    from urllib.request import Request, urlopen, HTTPError
except ImportError:
    # fall back to python2
    from urllib2 import Request, urlopen, HTTPError

class Test_Format_Conneg(BaseTest):
    label = 'Negotiated format'
    level = 1
    category = 7
    versions = [u'1.0', u'1.1']
    validationInfo = None

    def run(self, result):
        url = result.make_url(params={})
        hdrs = {'Accept': 'image/png;q=1.0'}
        try:
            r = Request(url, headers=hdrs)
            wh = urlopen(r)
            img = wh.read()   
            wh.close()
        except HTTPError as e:
            wh = e
        ct = wh.headers['content-type']
        result.last_url = url
        try:  # py2
            result.last_headers = wh.headers.dict
        except:
            result.last_headers = wh.info()
        result.last_status = wh.code
        result.urls.append(url)
        self.validationInfo.check('format', ct, 'image/png', result)
        return result