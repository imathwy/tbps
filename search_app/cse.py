from typing import Dict
from collections import defaultdict
from search_app.myexpr import (
    YourExpr,
    BVar,
    FVar,
    MVar,
    Sort,
    Const,
    App,
    Lam,
    ForallE,
    LetE,
    Lit,
    MData,
    Proj,
)


def generate_new_var(existing_vars: set) -> str:
    i = 0
    while True:
        var_name = f"v{i}"
        if var_name not in existing_vars:
            existing_vars.add(var_name)
            return var_name
        i += 1


def deBruijn_to_bindername(expr: YourExpr, binder_stack=None) -> YourExpr:
    if binder_stack is None:
        binder_stack = []
    if isinstance(expr, BVar):
        return BVar(binder_stack[expr.deBruijnIndex])
    elif isinstance(expr, App):
        return App(
            deBruijn_to_bindername(expr.fn, binder_stack),
            deBruijn_to_bindername(expr.arg, binder_stack),
        )
    elif isinstance(expr, Lam):
        new_binder_name = expr.binderName
        old_binder_stack = binder_stack.copy()
        binder_stack.insert(0, expr.binderName)
        result = Lam(
            new_binder_name,
            deBruijn_to_bindername(expr.binderType, old_binder_stack),
            deBruijn_to_bindername(expr.body, binder_stack),
            expr.binderInfo,
        )
        binder_stack.pop(0)
        return result
    elif isinstance(expr, ForallE):
        new_binder_name = expr.binderName
        old_binder_stack = binder_stack.copy()
        binder_stack.insert(0, expr.binderName)
        result = ForallE(
            new_binder_name,
            deBruijn_to_bindername(expr.binderType, old_binder_stack),
            deBruijn_to_bindername(expr.body, binder_stack),
            expr.binderInfo,
        )
        binder_stack.pop(0)
        return result
    elif isinstance(expr, LetE):
        old_binder_stack = binder_stack.copy()
        binder_stack.insert(0, expr.declName)
        result = LetE(
            expr.declName,
            deBruijn_to_bindername(expr.type, old_binder_stack),
            deBruijn_to_bindername(expr.value, binder_stack),
            deBruijn_to_bindername(expr.body, binder_stack),
            expr.nonDep,
        )
        binder_stack.pop(0)
        return result
    elif isinstance(expr, MData):
        return MData(expr.data, deBruijn_to_bindername(expr.expr, binder_stack))
    elif isinstance(expr, Proj):
        return Proj(
            expr.typeName, expr.idx, deBruijn_to_bindername(expr.struct, binder_stack)
        )
    else:
        return expr


def hash_expr(expr: YourExpr) -> str:
    if isinstance(expr, BVar):
        return f"BVar-{expr.deBruijnIndex}"
    elif isinstance(expr, FVar):
        return f"FVar-{expr.fvarId}"
    elif isinstance(expr, MVar):
        return f"MVar-{expr.mvarId}"
    elif isinstance(expr, Sort):
        return f"Sort-{expr.u}"
    elif isinstance(expr, Const):
        return f"Const-{expr.declName}-" + ",".join(expr.us)
    elif isinstance(expr, App):
        return f"App-{hash_expr(expr.fn)}-{hash_expr(expr.arg)}"
    elif isinstance(expr, Lam):
        return (
            f"Lam-{expr.binderName}-{hash_expr(expr.binderType)}-{hash_expr(expr.body)}"
        )
    elif isinstance(expr, ForallE):
        return f"ForallE-{expr.binderName}-{hash_expr(expr.binderType)}-{hash_expr(expr.body)}"
    elif isinstance(expr, LetE):
        return f"LetE-{expr.declName}-{hash_expr(expr.type)}-{hash_expr(expr.value)}-{hash_expr(expr.body)}"
    elif isinstance(expr, Lit):
        return f"Lit-{expr.literal}"
    elif isinstance(expr, MData):
        return f"MData-{expr.data}-{hash_expr(expr.expr)}"
    elif isinstance(expr, Proj):
        return f"Proj-{expr.typeName}-{expr.idx}-{hash_expr(expr.struct)}"
    else:
        raise ValueError(f"Unknown expression type: {type(expr)}")


def collect_subexprs(expr: YourExpr, count_dict: Dict[str, int]) -> str:
    expr_hash = hash_expr(expr)
    count_dict[expr_hash] += 1
    if isinstance(expr, App):
        collect_subexprs(expr.fn, count_dict)
        collect_subexprs(expr.arg, count_dict)
    elif isinstance(expr, Lam):
        collect_subexprs(expr.binderType, count_dict)
        collect_subexprs(expr.body, count_dict)
    elif isinstance(expr, ForallE):
        collect_subexprs(expr.binderType, count_dict)
        collect_subexprs(expr.body, count_dict)
    elif isinstance(expr, LetE):
        collect_subexprs(expr.type, count_dict)
        collect_subexprs(expr.value, count_dict)
        collect_subexprs(expr.body, count_dict)
    elif isinstance(expr, MData):
        collect_subexprs(expr.expr, count_dict)
    elif isinstance(expr, Proj):
        collect_subexprs(expr.struct, count_dict)

    return expr_hash


def replace_with_vars(
    expr: YourExpr,
    count_dict: Dict[str, int],
    var_map: Dict[str, str],
    existing_vars: set,
) -> YourExpr:
    expr_hash = hash_expr(expr)
    if count_dict[expr_hash] > 1:  # 如果该表达式出现超过一次
        if isinstance(expr, Const):
            return expr
        if expr_hash not in var_map:
            new_var = generate_new_var(existing_vars)
            var_map[expr_hash] = new_var
        return FVar(var_map[expr_hash])
    elif isinstance(expr, App):
        return App(
            replace_with_vars(expr.fn, count_dict, var_map, existing_vars),
            replace_with_vars(expr.arg, count_dict, var_map, existing_vars),
        )
    elif isinstance(expr, Lam):
        return Lam(
            expr.binderName,
            replace_with_vars(expr.binderType, count_dict, var_map, existing_vars),
            replace_with_vars(expr.body, count_dict, var_map, existing_vars),
            expr.binderInfo,
        )
    elif isinstance(expr, ForallE):
        return ForallE(
            expr.binderName,
            replace_with_vars(expr.binderType, count_dict, var_map, existing_vars),
            replace_with_vars(expr.body, count_dict, var_map, existing_vars),
            expr.binderInfo,
        )
    elif isinstance(expr, LetE):
        return LetE(
            expr.declName,
            replace_with_vars(expr.type, count_dict, var_map, existing_vars),
            replace_with_vars(expr.value, count_dict, var_map, existing_vars),
            replace_with_vars(expr.body, count_dict, var_map, existing_vars),
            expr.nonDep,
        )
    elif isinstance(expr, MData):
        return MData(
            expr.data, replace_with_vars(expr.expr, count_dict, var_map, existing_vars)
        )
    elif isinstance(expr, Proj):
        return Proj(
            expr.typeName,
            expr.idx,
            replace_with_vars(expr.struct, count_dict, var_map, existing_vars),
        )
    else:
        return expr


def cse(expr: YourExpr) -> YourExpr:
    count_dict = defaultdict(int)
    var_map = {}
    existing_vars = set()

    expr = deBruijn_to_bindername(expr)

    collect_subexprs(expr, count_dict)

    optimized_expr = replace_with_vars(expr, count_dict, var_map, existing_vars)

    return optimized_expr


def cse_without_deBruijn(expr: YourExpr) -> YourExpr:
    count_dict = defaultdict(int)
    var_map = {}
    existing_vars = set()

    collect_subexprs(expr, count_dict)

    optimized_expr = replace_with_vars(expr, count_dict, var_map, existing_vars)

    return optimized_expr
