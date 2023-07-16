
class RivException(Exception):
    def __init__(self, msg: str, level=None, unit=None, step=None):
        self.unit = unit
        self.step = step
        self.level = level

        tmp = ""
        if self.unit:
            tmp = "u=\"{0}\"".format(self.unit, tmp)

        if self.step:
            tmp = "s=\"{0}\" {1}".format(self.step, tmp)
        
        if self.level:
            tmp = "l={0} {1}".format(self.level, tmp)

        if len(tmp) > 0:
            msg = "{0} msg=\"{1}\"".format(tmp, msg)

        Exception.__init__(self, msg)


class VarNotFoundInContext(RivException):
    def __init__(self, name, level=None, unit=None, step=None):
        msg = "variable [{0}] not found in the context".format(name)
        RivException.__init__(self, msg, level=level, unit=unit, step=step)

class UnitNotFound(RivException):
    def __init__(self, name: str, level=None, unit=None, step=None):
        msg = "unit [{0}] not found in the context".format(name)
        RivException.__init__(self, msg, level=level, unit=unit, step=step)
