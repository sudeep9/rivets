
import argparse
import sys
import json
from pprint import pprint
import logging

import unit
import context
import engine
import loader
import yml_loader


def setup_logging():
    log = logging.getLogger()

    handler = logging.FileHandler('riv.log', mode='w')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    return log

def print_level(level: int, msg: str):
    for _ in range(level):
        print('  ', end='')

    print(msg)

def show_progress(ctx: context.Context, phase: str, step = None, u = None, f=None):
    p = '>'
    if phase == 'after': 
        p = '<'

    level = ctx.level 
    desc = ""
    name = ""
    obj = None

    if step:
        obj = 'step'
        desc = step.desc
        name = step.name
        level += 1

    if f:
        obj = 'flow'
        desc = f.desc
        name = f.name

    if len(desc) > 0:
        desc = "{0} / ".format(desc)

    msg = "{0} {1}: {2}{3}".format(p, obj, desc, name)
    print_level(level, msg)

def do_run_cmd(ns):
    flow_name = ns.name
    cfg_path = ns.cfg

    seed = {}
    argmode = 'none'
    if len(ns.seed) > 0:
        argmode = ns.seed[0]

    if argmode == 'json':
        if len(ns.seed) < 2:
            print("error: missing json string seed parameter")
            return
        seed = json.loads(ns.seed[1])
    elif argmode == 'ymlfile':
        if len(ns.seed) < 2:
            print("error: missing yaml file seed parameter")
            return
        seed = yml_loader.load_yml(ns.seed[1])
    else:
        seed = {
            'cli_args': ns.seed,
        }

    ctx = context.empty_context()
    ctx.log = setup_logging()

    if not ns.silent:
        ctx.callback_fn = show_progress

    loader.load_std_config(ctx, yml_loader.load_yml)
    loader.load_config(ctx, cfg_path, yml_loader.load_yml, processed_cfg={'std.yml': 'done'})
    ret = engine.run_flow(ctx, flow_name, seed)
    pprint(ret, indent=3)


def process_args(ns):
    if ns.cmd == 'run':
        do_run_cmd(ns)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='riv.py', 
        description='CLI to drive rivet flows')

    parser.add_argument('-s', dest='silent', action='store_true', help='No printing on screen')

    sub = parser.add_subparsers(title='subcommands', help='choose one of the commands',required=True, dest='cmd')

    run_cmd = sub.add_parser('run', help='run the flow')
    run_cmd.add_argument('cfg', help='File path of the cfg')
    run_cmd.add_argument('name', help='Name of the flow to run')
    run_cmd.add_argument('seed', nargs='*', help='seed arguments arguments passed')

    list_cmd = sub.add_parser('list', help='List the units')
    list_cmd.add_argument('cfg', help='File path of the cfg')

    ns = parser.parse_args()
    process_args(ns)