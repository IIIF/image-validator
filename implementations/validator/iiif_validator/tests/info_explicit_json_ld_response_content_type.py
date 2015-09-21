# encoding: utf-8

import urllib2
from test import BaseTest


class Test_Info_Explicit_Json_Ld_Response_Content_Type(BaseTest):
    """Confirm that explicit requests for JSON-LD have the specific Content-Type"""
    label = 'JSON-LD Media Type'
    level = 1
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        url = result.make_info_url()
        hdrs = {'Accept': 'application/ld+json'}
        try:
            r = urllib2.Request(url, headers=hdrs)
            wh = urllib2.urlopen(r)
            img = wh.read()
            wh.close()
        except urllib2.HTTPError, e:
            wh = e
        ct = wh.headers['content-type']

        # http://iiif.io/api/image/2.1/index.html#information-request
        #
        # See https://github.com/IIIF/image-api/pull/27 for clarification that only
        # application/ld+json is acceptable when the request explicitly accepts it:
        self.validationInfo.check('json-ld', ct, 'application/ld+json', result)

        return result
