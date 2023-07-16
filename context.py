from unit import Unit, Step

class Context:
    def __init__(self, umap: dict[str,Unit], vmap:dict[str,any]):
        self.umap = umap
        self.vmap = vmap
        self.l_retog = None
        self.level = 0
        self.callback_fn = no_op_callback
        self.curr_unit = None
        self.curr_step = None

    def add_umap(self, umap: dict):
        self.umap.update(umap)

def no_op_callback(ctx: Context, phase: str, step=None, u=None, f=None):
    pass


def empty_context():
    return Context({}, {})

def clone_context(ctx, vmap):
    child_ctx = Context(ctx.umap, vmap)
    child_ctx.log = ctx.log
    child_ctx.level = ctx.level+1
    child_ctx.callback_fn = ctx.callback_fn
    return child_ctx
