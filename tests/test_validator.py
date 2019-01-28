"""Test code for validator."""
import mock
import unittest

from iiif_validator.validator import ValidationInfo, TestSuite, ImageAPI, Validator
from iiif_validator.tests.cors import Test_Cors

class TestAll(unittest.TestCase):
    """Tests."""

    def test01_validation_info(self):
        """Check information setup."""
        vi = ValidationInfo()
        self.assertEqual(vi.mimetypes['jpg'], 'image/jpeg')

    def test02_test_suite_init(self):
        """Test suite initalization, include loading modules."""
        ts = TestSuite(info=ValidationInfo())
        # Check an example test
        self.assertTrue(ts.all_tests['info_json'])

    def test03_image_api_init(self):
        """Image API class initialization."""
        ia = ImageAPI(identifier='abc', server='http://example.org/')
        self.assertEqual(ia.version, '2.1')

    def test04_validator(self):
        """Validator class initialization."""
        v = Validator()
        self.assertTrue(hasattr(v, 'handle_test'))

    def test05_cors(self):
        """Test suite CORS."""
        m = mock.Mock()
        t = Test_Cors(m)

        r = mock.Mock()
        setattr(r, 'last_headers', {
            'Access-Control-Allow-Origin': ':-)'
        })
        t.run(r)
        m.check.assert_called_with('CORS', ':-)', '*', r)
