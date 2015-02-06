#!/usr/bin/env python
"""Minimal wrapper around iiif-validator/validator.py to run server 
   from the command line, or from mod_wsgi in apache
"""

from iiif_validator.validator import main, apache
if __name__ == "__main__":
    main()
else:
    application = apache()
