
from rivparser import Lark_StandAlone, Transformer, Token
from unit import Step, FunctionUnit, FlowUnit

def parse(p, filepath):
    with open(filepath) as f:
        buf = f.read()

    t = p.parse(buf)
    print(t)
    for name, u in t.items():
        print(name,":", str(u))

class RivTransformer(Transformer):
    def fn(self, item):
        return ('fn', item[0])

    def value(self, items):
        return items[0]
    
    def default(self, items):
        return items[0]

    def IDENTIFIER(self, item):
        return item.value

    def STR(self, item):
        return item.value[1:-1]

    def NUMBER(self, items):
        return int(items.value)

    def indent_str(self, items):
        return items[0]

    def kv(self, items):
        return (items[0], items[1])

    def arg_decl(self, items):
        return (items[0], items[1])

    def dict(self, items):
        return {k: v for k, v in items }

    def list(self, items):
        return items

    def arg_decl_def(self, items):
        return items

    def false(self, val):
        return False

    def true(self, val):
        return True
    def nil(self, _val):
        return None

    def step(self, items):
        desc = items[0]
        name = desc
        inp = {}
        for k, v in items[1:]:
            if k == '$unit':
                name = v
                continue
            inp[k] = v
        
        s = Step(name, desc, inp, None)
        return s

    def steps(self, items):
        return ('steps', items)

    def unit_body(self, items):
        return items

    def flow_body(self, items):
        return items[0]

    def unit_desc(self, items):
        return ("desc", items[0])

    def input(self, items):
        default_found = False
        args = []
        defaults = {}
        inp = {}
        for i in items:
            if len(i) == 2:
                if default_found:
                    raise Exception(f"Positional argument [{name}] declared after keyword argument")
                name, desc = i[0], i[1]
                inp[name] = desc
                args.append(name)
            elif len(i) == 3:
                name, default, desc = i[0], i[1], i[2]
                inp[name] = desc
                default_found = True
                defaults[name] = default
            else:
                raise Exception(f"Invalid number of argument attributes [{i}]")

        return ('in', (args, inp, defaults))

    def output(self, items):
        return ('out', {k: v for k, v in items })
    
    def options(self, items):
        return ('opt', {k: v for k, v in items })

    def unit(self, items):
        name = items[0]
        fn = None
        args = []
        inp = defs = {}
        meta = False
        map_op = False
        desc = name
        for x in items[1]:
            ty, val = x
            if ty == 'desc':
                desc = val
            elif ty == 'fn':
                fn = val
            elif ty == 'in':
                args, inp, defs = val
            elif ty == 'out':
                out = val
            elif ty == 'opt':
                meta = val.get('meta', False)
                map_op = val.get('map_op', False)

        if fn is None or not isinstance(fn, str):
            raise Exception(f"Function name [{fn}] is not defined or is not string")

        u = FunctionUnit(fn, meta, map_op, name, desc, inp, out, args, defs)
        return u

    def flow(self, items):
        name = items[0]
        args = []
        inp = defs = {}
        steps = []
        out = {}

        for ty, val in items[1:]:
            if ty == 'in':
                _, inp, defs = val
            elif ty == 'out':
                out = val
            elif ty == 'opt':
                pass
        u = FlowUnit(steps, name, name, inp, out, args, defs)
        return u

    def start(self, items):
        return {u.name: u for u in items}



p = Lark_StandAlone(transformer=RivTransformer())
#p = Lark_StandAlone()
parse(p, "./test.riv")