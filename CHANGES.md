iiif_validator change log
=========================

v1.0.4 2017-09-08
  * Add license information <https://github.com/IIIF/image-validator/pull/56>
  * Use Requirements-Builder and Tox for testing <https://github.com/IIIF/image-validator/pull/53>

v1.0.3 2017-01-19
  * Fix CORS test <https://github.com/IIIF/image-validator/pull/51>
  
v1.0.2 2017-01-19
  * Tie Pillow to < 4.0.0 as 4.0.0 no longer supports python 2.6 <https://github.com/IIIF/image-validator/pull/49>

v1.0.1 2015-05-20
  * Made to work with python 3.x as well as 2.7 <https://github.com/IIIF/image-api/pull/40>
  * Fix for Origin request header <https://github.com/IIIF/image-api/issues/33>
  * Fix for Content-type <https://github.com/IIIF/image-api/issues/31>
  * Timeout added on validation requests <https://github.com/IIIF/image-api/commit/c0d3e6df82e43aaae2e20f49b3546f7ec8e88447>

v1.0.0 2015-02-10
  * Has been running long enough and tested by others to declare 1.0.0
  * Fix issues with images with >256 colors and color palettes
  * Switch README to reStructuredText for pypi
  * Added --test param to iiif-validate.py to run specific tests

v0.9.1 2014-11-11
  * Fix bug in validation of rotation
  * Update README with instructions for use in Travis CI

v0.9.0 2014-11-04
  * Packaged for pypi and easy use with Travis CI
  * Used IIIF in validation service at <http://iiif.io/api/image/validator/>
