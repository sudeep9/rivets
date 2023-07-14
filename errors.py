
class VarNotFoundInContext(Exception):
    def __init__(self, name: str):
        Exception.__init__(self, "referenced variable [{0}] not found in context".format(name))

class UnitNotFound(Exception):
    def __init__(self, name: str):
        Exception.__init__(self, "unit [{0}] not found in context".format(name))