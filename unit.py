class Unit:
    # inp: describes all inputs.
    # out: (opt) describes the output mapping
    # args: list of mandatory args. They act like positional arguments for functions
    # defs: defaults values if not specified
    def __init__(self, name: str, desc: str, inp: dict[str,str], out:dict[str,str], args: list[str], defs: dict[str,any]):
        self.name = name
        self.desc = desc
        self.inp = inp
        self.out = out
        self.args = args
        self.defaults = defs
        self.map_output = True

class FunctionUnit(Unit):
    def __init__(self, fn, is_meta: bool, map_op: bool, *args, **kargs):
        Unit.__init__(self, *args, **kargs)
        self.fn = fn
        self.is_meta = is_meta
        self.map_output = map_op

    def __str__(self):
        return f"{self.name} fn:{self.fn} args:{self.args} defs:{self.defaults}"

class Step:
    def __init__(self, name: str, desc: str, inp: dict[str, any], out, map_output=False):
        self.desc = desc
        self.name = name
        self.inp = inp
        self.out = out
        self.map_output=map_output

class FlowUnit(Unit):
    def __init__(self, steps: list[Step], *args, **kargs):
        Unit.__init__(self, *args, **kargs)
        self.steps = steps
        self.map_output = True

        for key in self.inp:
            if key not in self.defaults:
                self.args.append(key)

    def __str__(self):
        return f"{self.name} in:{self.inp} defs:{self.defaults} out:{self.out}"

class RivetsFile:
    def __init__(self):
        self.imports = None
        self.unit_map = {}