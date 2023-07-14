
from context import Context

def print_vars(ctx: Context, varlist):
    print("---- print vars ---- (Start)")
    for v in varlist:
        if v == '$?':
            val = ctx.last_ret
        else: 
            val = ctx.vmap.get(v, '<not found>')

        print(v, "=", val)
    print("---- print vars ---- (End)")

def define_vars(ctx: Context, vmap: dict[str,any]):
    ctx.vmap.update(vmap)

def parse_args_to_kv(ctx: Context, args: list[str], types: dict[str,str]):
    if types is None:
        types = {}

    for a in args:
        key, val = a.split('=')

        try:
            ty = types[key]
            if ty == 'int':
                ctx.vmap[key] = int(val)
            elif ty == 'float':
                ctx.vmap[key]
            else:
                ctx.vmap[key] = val
        except KeyError:
            pass