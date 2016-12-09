"""Test code for validator."""
import unittest
import re

from iiif_validator.validator import ValidationInfo, TestSuite, ImageAPI, Validator


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
        self.assertEqual(ia.version, '2.0')

    def test04_validator(self):
        """Validator class initialization."""
        v = Validator()
        self.assertTrue(hasattr(v, 'handle_test'))
