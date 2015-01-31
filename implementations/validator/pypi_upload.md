===============================
Updating iiif-validator on pypi
===============================

Notes to remind zimeon...

iiif-validator is at https://pypi.python.org/pypi/iiif-validator

Putting up a new version
------------------------

0. Bump version number working branch in iiif_validator/_version.py and check CHANGES.md is up to date
1. Check all tests good (python setup.py test; py.test) --- no tests yet, skip
2. Check code is up-to-date with github version
3. Check out master and merge in working branch
4. Check all tests good (python setup.py test; py.test)  --- no tests yet, skip
5. Make sure master README has correct travis-ci icon link  --- no tests yet, skip
6. Check branches are as expected (git branch -a)
7. Check local build and version reported OK (python setup.py build; sudo python setup.py install)
8. Check iiif-validator.py correctly starts server and runs tests
9. If all checks out OK, tag and push the new version to github with something like:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "IIIF Image API Validator v0.9.0, first packaged version" v0.9.0
    git push --tags

    python setup.py sdist upload
    ```

10. Then check on PyPI at https://pypi.python.org/pypi/iiif-validator
11. Finally, back on working branch start new version number by editing iiif_validator/_version.py and CHANGES.md

