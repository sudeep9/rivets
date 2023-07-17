from typing import Iterable
import ast
from unit import Unit, FunctionUnit, FlowUnit, Step
from errors import VarNotFoundInContext, UnitNotFound, RivException
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
    if not isinstance(val, str):
        return val

    if val.startswith('\$'):
        return val[1:]

    if val.startswith('$'):
        sub = val[1:]
        if sub.startswith('look '):
            return dict_query(ctx, sub[5:])
        elif sub.startswith('form '):
            return resolve_format(ctx, sub[5:])
        else:
            return context_get(ctx, sub)

    return val

def resolve_step_input(ctx: Context, inp):
    if isinstance(inp, dict):
        ret = {}
        for key, val in inp.items():
            if key.startswith('$'):
                key = key[1:]
                if isinstance(val, dict) or isinstance(val, list):
                    ret[key] = resolve_step_input(ctx, val)
                else:
                    v = resolve_from_ctx(ctx, val)
                    ret[key] = v
            else:
                ret[key] = val
    elif isinstance(inp, list):
        ret = []
        for i in range(len(inp)):
            ret.append(resolve_step_input(ctx, inp[i]))
    else:
        return resolve_from_ctx(ctx, inp)

    return ret

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
        ret = run_step(ctx, step)
        ctx.vmap['LAST'] = ret

    try:
        ctx.log.info("mapping output for flow level=%s name=%s", ctx.level, u.name)
        ret = {}
        for out_name, val in u.out.items():
            ret[out_name] = resolve_from_ctx(ctx, val)

        ctx.log.info("ctx after flow level=%s name=%s vmap=%s ret=%s", ctx.level, u.name, ctx.vmap, ret)
        ctx.callback_fn(ctx, 'after', f=u)
        del ctx.vmap['LAST']
        return ret
    except Exception as e:
        raise RivException("flow unit mapping failed", level=ctx.level, unit=u.name)

def run_step(ctx: Context, step: Step):
    ctx.log.info("running step level=%s desc=[%s] name=%s", ctx.level, step.desc, step.name)

    u = get_unit(ctx, step.name)

    ctx.curr_step = step.name
    ctx.curr_unit = u.name

    inp = resolve_step_input(ctx, step.inp)

    if isinstance(u, FunctionUnit):
        try:
            ctx.callback_fn(ctx, 'before', step=step)
            ret = run_fn_unit(ctx, u, inp)
        except RivException as e:
            raise
        except Exception as e:
            raise RivException("function unit failed", level=ctx.level, unit=step.name, step=step.desc)
    elif isinstance(u, FlowUnit):
        kargs = map_flow_kargs(ctx, inp, u.args, u.defaults)
        child_ctx = clone_context(ctx, kargs)
        child_ctx.curr_step = ctx.curr_step

        ret = run_flow_unit(child_ctx, u)
        ctx.log.info('ret after run_flow_unit. level=%s step=%s ret=%s', ctx.level, step.name, ret)
    else:
        raise RivException("unknown type of unit", level=ctx.level, unit=step.name, step=step.desc)

    ctx.curr_step = None
    ctx.curr_unit = None
    return ret

def _dq_subscript(ctx: Context, s: any, pval = None):
    if isinstance(s, ast.Subscript):
        if isinstance(s.value, ast.Subscript):
            v = _dq_subscript(ctx, s.value)
            return _dq_subscript(ctx, s.slice, pval = v)
        elif isinstance(s.value, ast.Name):
            v = context_get(ctx, s.value.id)
            return _dq_subscript(ctx, s.slice, pval = v)
    elif isinstance(s, ast.UnaryOp):
        val = _dq_subscript(ctx, s.operand)
        if isinstance(s.op, ast.USub):
            val = -val
        
        if pval:
            return pval[val]
        return val
    elif isinstance(s, ast.Constant):
        if pval:
            return pval[s.value]
        return s.value
    elif isinstance(s, ast.Slice):
        lower = 0; upper = None; step = 1
        if s.lower:
            lower = _dq_subscript(ctx, s.lower)
        if s.upper:
            upper = _dq_subscript(ctx, s.upper)
        if s.step:
            step = _dq_subscript(ctx, s.step)
        return pval[lower:upper:step]
    elif isinstance(s, ast.Name):
        ret = context_get(ctx, s.id)
        return ret

def dict_query(ctx: Context, q: str):
    expr = ast.parse(q, mode='eval')

    if not (isinstance(expr.body, ast.Subscript) or isinstance(expr.body, ast.Name)):
        raise Exception("expression is not right")
    
    try:
        return _dq_subscript(ctx, expr.body)
    except IndexError as e:
        raise RivException("Index error: {0} in: {1}".format(str(e), q), level=ctx.level, unit=ctx.curr_unit, step=ctx.curr_step)
    except KeyError as e:
        raise RivException("Key error: {0} in: {1}".format(str(e), q), level=ctx.level, unit=ctx.curr_unit, step=ctx.curr_step)

def resolve_format(ctx: Context, format_str: str):
    return format_str.format(**ctx.vmap)

if __name__ == '__main__':
    import sys
    from pprint import pprint
    a = {
        'data': [
            {
                'data': {'id': 1}
            }
        ],
        'val': [1,2,3,4,5,6,7,8,9,10],
    }

    ctx = empty_context()
    ctx.vmap['a'] = a
    ctx.vmap['_riv'] = a
    pprint(a, indent=4)

    print(dict_query(ctx, sys.argv[1]))