# encoding: utf-8

from test import BaseTest
import urllib2


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
        # If the client explicitly wants the JSON-LD content-type, then it MUST specify this in an Accept
        # header, otherwise the server MUST return the regular JSON content-type.
        #
        # If the regular JSON content-type is returned, then it is RECOMMENDED that the server provide a link
        # header to the context document.

        if ct == 'application/json':
            expected_link_header = '<http://iiif.io/api/image/2/context.json>'
            link_header = wh.headers.get('link')

            if not link_header.startswith(expected_link_header):
                raise ValidatorError('json-ld-with-context-link', link_header, expected_link_header, result)
        else:
            self.validationInfo.check('json-ld', ct, 'application/ld+json', result)

        return result