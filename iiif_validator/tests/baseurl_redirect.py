from .test import BaseTest, ValidatorError
try:
    # python3
    from urllib.request import Request, urlopen, HTTPError
except ImportError:
    # fall back to python2
    from urllib2 import Request, urlopen, HTTPError


class Test_Baseurl_Redirect(BaseTest):
    label = 'Base URL Redirects'
    level = 1
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()
        url = url.replace('/info.json', '')
        try:
            r = Request(url)
            wh = urlopen(r)
            img = wh.read()   
            wh.close()
        except HTTPError as e:
            wh = e        

        u = wh.geturl()
        if u == url:
            # we didn't redirect
            raise ValidatorError('redirect', '', 'URI', result)
        else:
            # we must have redirected if our url is not what was requested
            result.tests.append('redirect')
            return result