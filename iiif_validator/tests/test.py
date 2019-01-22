"""BaseTest class for tests and ValidationError exception."""

class BaseTest(object):
    label = "test name"
    level = 0
    category = 0
    versions = []
    validationInfo = None

    def __init__(self, info):
        self.validationInfo = info

    @classmethod
    def make_info(cls, version):
        # print cls.label, version, cls.versions
        if version and not version in cls.versions:
            return {}            
        data = {'label': cls.label, 'level':cls.level, 'versions': cls.versions, 'category': cls.category}
        if type(cls.level) == dict:
            # If not version, need to make a choice... make it max()
            if version:
                data['level'] = cls.level[version]
            else:
                data['level'] = max(cls.level.values())
        return data


# this looks like it needs refactoring, along with validationInfo.check()
class ValidatorError(Exception):
    def __init__(self, type, got, expected, result=None, message="", isWarning=False):
        self.type = type
        self.got = got
        self.expected = expected
        self.message = message
        self.warning = isWarning
        if result != None:
            self.url = result.last_url
            self.headers = result.last_headers
            self.status = result.last_status
        else:
            self.url = None
            self.headers = None
            self.status = None
                
    def __str__(self):
        if self.message:
            return "Expected %s for %s; Got: %r".format(self.message, self.type, self.got)
        else:
            return "Expected %r for %s; Got: %r".format(self.expected, self.type, self.got)



        
