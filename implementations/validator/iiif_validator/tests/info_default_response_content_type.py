# encoding: utf-8

from test import BaseTest
import urllib2

class Test_Info_Default_Response_Content_Type(BaseTest):
    """Confirm that a generic info request receives an acceptable response type"""
    label = 'Default response Content-Type'
    level = 1
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()

        try:
            r = urllib2.Request(url)
            wh = urllib2.urlopen(r)
            img = wh.read()
            wh.close()
        except urllib2.HTTPError, e:
            wh = e

        ct = wh.headers['content-type']

        # http://iiif.io/api/image/2.1/index.html#information-request
        # The syntax for the response is JSON-LD. The content-type of the response must be either
        # “application/json” (regular JSON), or “application/ld+json” (JSON-LD)
        # If the client explicitly wants the JSON-LD content-type, then it MUST specify this in an Accept
        # header, otherwise the server MUST return the regular JSON content-type.

        self.validationInfo.check('default-response-content-type', ct, 'application/json', result)

        return result
