from .test import BaseTest
try:
    # python3
    from urllib.request import Request, urlopen, HTTPError
except ImportError:
    # fall back to python2
    from urllib2 import Request, urlopen, HTTPError

class Test_Jsonld(BaseTest):
    label = 'JSON-LD Media Type'
    level = 1
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()
        hdrs = {'Accept': 'application/ld+json'}
        try:
            r = Request(url, headers=hdrs)
            wh = urlopen(r)
            img = wh.read()   
            wh.close()
        except HTTPError as e:
            wh = e
        ct = wh.headers['content-type']
        self.validationInfo.check('json-ld', ct.startswith('application/ld+json'), 1, result, "Content-Type to start with application/ld+json")
        return result