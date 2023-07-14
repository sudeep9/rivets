from typing import Iterable
from unit import Unit, FunctionUnit, FlowUnit, Step
from errors import VarNotFoundInContext, UnitNotFound
from context import Context, empty_context, clone_context

def get_unit(ctx: Context, name: str):
    try:
        return ctx.umap[name]
    except KeyError:
        raise UnitNotFound(name)

def context_get(ctx: Context, name: str):
    try:
        return ctx.vmap[name]
    except KeyError:
        raise VarNotFoundInContext(name)

def resolve_from_ctx(ctx: Context, val: any):
    if isinstance(val, str):
        if val == '$?':
            return ctx.last_ret

        if val.startswith('\$'):
            return context_get(ctx, val[2:])

        if val.startswith('$'):
            return context_get(ctx, val[1:])

    return val

def resolve_value(ctx: Context, name: str, inp: dict[str,any]):
    try:
        return resolve_from_ctx(ctx, inp[name])
    except KeyError:
        return context_get(ctx, name)
        

def map_pargs(ctx: Context, inp: dict[str,any], pargs: list[str]):
    ret = []
    for name in pargs:
        val = resolve_value(ctx, name, inp)
        ret.append(val)

    return ret

def map_kargs(ctx: Context, inp: dict[str,any], kargs: dict[str,any]):
    ret = {}
    for name, defval in kargs.items():
        try:
            val = resolve_value(ctx, name, inp)
        except VarNotFoundInContext:
            val = defval
        ret[name] = val

    return ret

def map_flow_kargs(ctx: Context, inp: dict[str,any], must_args: Iterable, kargs: dict[str,any]):
    ret = map_kargs(ctx, inp, kargs)
    for name in must_args:
        val = resolve_value(ctx, name, inp)
        ret[name] = val
    return ret

def run_fn_unit(ctx: Context, u: FunctionUnit, inp: dict[str,any]):
    ctx.log.info("running function unit name=%s fn=%s", u.name, u.fn.__name__)

    args = map_pargs(ctx, inp, u.args)
    kargs = map_kargs(ctx, inp, u.defaults)
    if u.is_meta:
        ret = u.fn(ctx, *args, **kargs)
    else:
        ret = u.fn(*args, **kargs)

    ctx.log.info("function ret: %s", ret)
    return ret

def run_flow_unit(ctx: Context, u: FlowUnit):
    ctx.callback_fn(ctx, 'before', f=u)

    ctx.log.info("running flow level=%s name=%s", ctx.level, u.name)

    for step in u.steps:
        run_step(ctx, step)

    ctx.log.info("mapping output for flow level=%s name=%s", ctx.level, u.name)
    ret = {}
    for out_name, val in u.out.items():
        ret[out_name] = resolve_from_ctx(ctx, val)

    ctx.log.info("ctx after flow level=%s name=%s vmap=%s ret=%s", ctx.level, u.name, ctx.vmap, ret)
    ctx.callback_fn(ctx, 'after', f=u)
    return ret

def run_step(ctx: Context, step: Step):
    ctx.log.info("running step level=%s desc=[%s] name=%s", ctx.level, step.desc, step.name)
    u = get_unit(ctx, step.name)

    if isinstance(u, FunctionUnit):
        ctx.callback_fn(ctx, 'before', step=step)

        ret = run_fn_unit(ctx, u, step.inp)
        if u.map_output and isinstance(ret, dict):
            ctx.vmap.update(ret)
        else:
            ctx.last_ret = ret
    elif isinstance(u, FlowUnit):
        kargs = map_flow_kargs(ctx, step.inp, u.args, u.defaults)
        child_ctx = clone_context(ctx, kargs)

        ret = run_flow_unit(child_ctx, u)
        ctx.log.info('ret after run_flow_unit. level=%s step=%s ret=%s', ctx.level, step.name, ret)
        ctx.vmap.update(ret)
    else:
        raise Exception("unknown type of unit")

    ctx.log.info('vmap after level=%s step=%s vmap=%s last_ret=%s', ctx.level, step.name, ctx.vmap, ctx.last_ret)

def run_flow(ctx: Context, name: str, inp: dict[str,any]):
    u = get_unit(ctx, name)
    ctx.vmap.update(inp)
    ret = run_flow_unit(ctx, u)
    return ret
