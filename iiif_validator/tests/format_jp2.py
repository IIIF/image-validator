from .test import BaseTest, ValidatorError
import magic, urllib

class Test_Format_Jp2(BaseTest):
    label = 'JPEG2000 format'
    level = {u'3.0': 3, u'2.0': 3, u'1.0': 2, u'1.1': 3}
    category = 6
    versions = [u'1.0', u'1.1', u'2.0', u'3.0']
    validationInfo = None

    def run(self, result):

        params = {'format': 'jp2'}
        url = result.make_url(params)
        # Need as plain string for magic
        wh = urllib.urlopen(url)
        img = wh.read()
        wh.close()
        # check response code before checking the file
        if wh.getcode() != 200:
            raise ValidatorError('format', 'http response code: {}'.format(wh.getcode()), url, result, 'Failed to retrieve jp2, got response code {}'.format(wh.getcode()))

        with magic.Magic() as m:
            print ('test')
            info = m.id_buffer(img)
            if not info.startswith('JPEG 2000'):
                # Not JP2
                raise ValidatorError('format', info, 'JPEG 2000', result)
            else:
                result.tests.append('format')
                return result
