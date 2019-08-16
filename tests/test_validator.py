#!/usr/bin/env python
"""Test code for validator."""
import mock
from mock import MagicMock
import unittest
import sys
import json
sys.path.insert(1,'.')

from iiif_validator.validator import ValidationInfo, TestSuite, ImageAPI, Validator
from iiif_validator.tests.test import ValidatorError
from iiif_validator.tests.cors import Test_Cors
from iiif_validator.tests.info_json import Test_Info_Json

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
        v = Validator(False)
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

    def test06_info(self):
        """Test info.json checks."""
        vi = ValidationInfo()
        t = Test_Info_Json(vi)
        
        result = createResult('tests/json/info-3.0.json', '3.0')
        try:
            t.run(result)
        except:
            self.fail('Validator failed a valid 3.0 info.json')

    def test07_info3of2(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-2.0.json', '3.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.assertEqual('required-field: id', e.type,'Expected 2.0 image server to fail 3.0 validation with a missing id.')

    def test08_testLogoWarning(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-3.0-logo.json', '3.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.assertEqual('logo-missing', e.type,'Should have picked up logo is invalid with 3.0')
            self.assertTrue(e.warning,'Should be a warning not an error')

    def test09_testExistingAuth(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-3.0-service.json', '3.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.assertEqual('missing-key', e.type,'Expected missing type in service but found: {}'.format(e.type))

    def test10_testLabel(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-3.0-service-label.json', '3.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.fail('Validator failed a valid 3.0 label: \n{}'.format(e))

    def test11_testLabel(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-3.0-service-badlabel.json', '3.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.assertEqual('is-object', e.type,'Expected object test failure but got: {}'.format(e.type))

    def test12_info2(self):
        """Test info.json checks."""
        t = Test_Info_Json(ValidationInfo())
        
        result = createResult('tests/json/info-2.0.json', '2.0')
        try:
            t.run(result)
        except ValidatorError as e:
            self.assertEqual('required-field: id', e.type,'Expected 2.0 image server to fail 3.0 validation with a missing id.')

       

def createResult(filename, version):
    # result.version
    # result.get_info()
    # result.last_url
    # result.last_headers['content-type']

    with open(filename) as f:
        info = json.load(f)

        result = mock.Mock()
        setattr(result, 'version', version)
        result.get_info = MagicMock(return_value=info)
        idField = 'id'
        if idField not in info:
            idField = '@id'
        setattr(result, 'last_url', '{}/info.json'.format(info[idField]))
        setattr(result, 'last_status', 200)
        setattr(result, 'last_headers', {
            'content-type': 'application/ld+json'
        })

        return result


if __name__ == '__main__':
    unittest.main()
