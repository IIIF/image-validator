from .test import BaseTest, ValidatorError
try:
    # python3
    from urllib.request import Request, urlopen, HTTPError
    print ('Importing 3')
except ImportError:
    # fall back to python2
    from urllib2 import Request, urlopen, HTTPError
    print ('Importing 2')


class Test_Baseurl_Redirect(BaseTest):
    label = 'Base URL Redirects'
    level = 1
    category = 7
    versions = [u'2.0', u'3.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()
        url = url.replace('/info.json', '')
        newurl = ''
        try:
            r = Request(url)
            wh = urlopen(r)
            img = wh.read()   
            wh.close()
            newurl = wh.geturl()
        except HTTPError as e:
            wh = e        
            if wh.getcode() >= 300 and wh.getcode() < 400:
                newurl = wh.headers['Location']
            else:
                newurl = wh.geturl()

        if newurl == url:
            print (wh)
            print (wh.geturl())
            print (type(wh))
            # we didn't redirect
            raise ValidatorError('redirect', u, '{}/info.json'.format(url), result, 'Failed to redirect from {} to {}/info.json. Response code {}'.format(u, url, wh.getcode()))
        else:
            # we must have redirected if our url is not what was requested
            result.tests.append('redirect')
            return result
