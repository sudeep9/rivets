
from context import Context
import engine 
import errors

def print_vars(ctx: Context, varlist):
    print("---- print vars ---- (Start)")
    for v in varlist:
        val = ctx.vmap.get(v, '<not found>')
        print(v, "=", val)
    print("---- print vars ---- (End)")

def define_vars(ctx: Context, vmap: dict[str,any]):
    for name, val in vmap.items():
        ctx.vmap[name] = engine.resolve_from_ctx(ctx, val)

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

def to_list(ctx: Context, vname: str, args: list[any]):
    ret = []
    for a in args:
        ret.append(engine.resolve_from_ctx(ctx, a))
    ctx.vmap[vname] = ret


def basic_cli_arguments(ctx: Context, args: list, spec: list[dict], usage: None):
    import argparse
    parser = argparse.ArgumentParser(prog=ctx.curr_unit, usage=usage)

    for argspec in spec:
        parser.add_argument(**argspec)

    ns = parser.parse_args(args)
    ctx.vmap.update(vars(ns))

def map_dict_to_ctx(ctx: Context, d: dict, includes: None):
    if isinstance(d, dict):
        if includes:
            for key in includes:
                ctx.vmap(d[key])
        else:
            ctx.vmap.update(d)

def to_dict(ctx: Context, vname: str, vals: dict):
    d = {}
    for key, v in vals.items():
        d[key] = engine.resolve_from_ctx(ctx, v)
    
    ctx.vmap[vname]= d

def getenv(ctx: Context, vars, error=True):
    import os
    missing = []
    values = {}

    for v in vars:
        try:
            val = os.environ[v]
            values[v] = val
        except KeyError:
            missing.append(v)

    if len(missing) > 0 and error:
        raise Exception(f"Environment variables {missing} not found")
    
    ctx.vmap.update(values)
