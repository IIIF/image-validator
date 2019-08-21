===============================
Updating iiif-validator on pypi
===============================

iiif-validator is at <https://pypi.org/project/iiif-validator/>

Putting up a new version
------------------------

  0. Bump version number working branch in iiif_validator/_version.py and check CHANGES.md is up to date
  1. Check all tests good (python setup.py test; py.test)
  2. Check code is up-to-date with github version
  3. Check out master and merge in working branch
  4. Check all tests good (python setup.py test; py.test)
  5. Check branches are as expected (git branch -a)
  6. Check local build and version reported OK (python setup.py build; python setup.py install)
  7. Check iiif-validator.py correctly starts server and runs tests
  8. If all checks out OK, tag and push the new version to github with something like:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "IIIF Image API Validator v1.1.1" v1.1.1
    git push --tags

    python setup.py sdist upload
    ```

FIXME - should change to use `twine` for upload per https://pypi.org/project/twine/


   9. Then check on PyPI at <https://pypi.org/project/iiif-validator/>
  10. Finally, back on working branch start new version number by editing `iiif_validator/_version.py` and `CHANGES.md`

