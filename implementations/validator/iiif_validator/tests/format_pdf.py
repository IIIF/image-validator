from .test import BaseTest, ValidatorError
import magic, urllib, ssl

class Test_Format_Pdf(BaseTest):
    label = 'PDF format'
    level = 3
    category = 6
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):

        params = {'format': 'pdf'}
        url = result.make_url(params)
        # Need as plain string for magic
        context = ssl._create_unverified_context()
        wh = urllib.urlopen(url, context=context)
        img = wh.read()
        wh.close()

        with magic.Magic() as m:
            info = m.id_buffer(img)
            if not info.startswith('PDF document'):
                # Not JP2
                raise ValidatorError('format', info, 'PDF', result)
            else:
                result.tests.append('format')
                return result
