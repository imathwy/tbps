from dataclasses import dataclass
from typing import List, Union


@dataclass
class BVar:
    deBruijnIndex: int


@dataclass
class FVar:
    fvarId: str


@dataclass
class MVar:
    mvarId: str


@dataclass
class Sort:
    u: str


@dataclass
class Const:
    declName: str
    us: List[str]


@dataclass
class App:
    fn: "YourExpr"
    arg: "YourExpr"


@dataclass
class Lam:
    binderName: str
    binderType: "YourExpr"
    body: "YourExpr"
    binderInfo: str


@dataclass
class ForallE:
    binderName: str
    binderType: "YourExpr"
    body: "YourExpr"
    binderInfo: str


@dataclass
class LetE:
    declName: str
    type: "YourExpr"
    value: "YourExpr"
    body: "YourExpr"
    nonDep: bool


@dataclass
class Lit:
    literal: str


@dataclass
class MData:
    data: str
    expr: "YourExpr"


@dataclass
class Proj:
    typeName: str
    idx: int
    struct: "YourExpr"


YourExpr = Union[
    BVar, FVar, MVar, Sort, Const, App, Lam, ForallE, LetE, Lit, MData, Proj
]


def serialize_expr(expr: YourExpr) -> dict:
    if isinstance(expr, BVar):
        return {"bvar": {"deBruijnIndex": expr.deBruijnIndex}}
    elif isinstance(expr, FVar):
        return {"fvar": expr.fvarId}
    elif isinstance(expr, MVar):
        return {"mvar": expr.mvarId}
    elif isinstance(expr, Sort):
        return {"sort": expr.u}
    elif isinstance(expr, Const):
        return {"const": {"declName": expr.declName, "us": expr.us}}
    elif isinstance(expr, App):
        return {"app": {"fn": serialize_expr(expr.fn), "arg": serialize_expr(expr.arg)}}
    elif isinstance(expr, Lam):
        return {
            "lam": {
                "binderName": expr.binderName,
                "binderType": serialize_expr(expr.binderType),
                "body": serialize_expr(expr.body),
                "binderInfo": expr.binderInfo,
            }
        }
    elif isinstance(expr, ForallE):
        return {
            "forallE": {
                "binderName": expr.binderName,
                "binderType": serialize_expr(expr.binderType),
                "body": serialize_expr(expr.body),
                "binderInfo": expr.binderInfo,
            }
        }
    elif isinstance(expr, LetE):
        return {
            "letE": {
                "declName": expr.declName,
                "type": serialize_expr(expr.type),
                "value": serialize_expr(expr.value),
                "body": serialize_expr(expr.body),
                "nonDep": expr.nonDep,
            }
        }
    elif isinstance(expr, Lit):
        return {"lit": {"literal": expr.literal}}
    elif isinstance(expr, MData):
        return {"mdata": {"data": expr.data, "expr": serialize_expr(expr.expr)}}
    elif isinstance(expr, Proj):
        return {
            "proj": {
                "typeName": expr.typeName,
                "idx": expr.idx,
                "struct": serialize_expr(expr.struct),
            }
        }
    else:
        raise ValueError(f"无法序列化未知表达式类型: {expr}")


def deserialize_expr(data: dict) -> YourExpr:
    expr_type = list(data.keys())[0]
    value = data[expr_type]
    if expr_type == "bvar":
        de_bruijn_index = value.get("deBruijnIndex")
        if de_bruijn_index is None:
            raise ValueError("deBruijnIndex is missing for BVar")
        return BVar(deBruijnIndex=de_bruijn_index)
    elif expr_type == "fvar":
        return FVar(fvarId=value)
    elif expr_type == "mvar":
        return MVar(mvarId=value)
    elif expr_type == "sort":
        return Sort(u=value)
    elif expr_type == "const":
        return Const(declName=value["declName"], us=value["us"])
    elif expr_type == "app":
        return App(fn=deserialize_expr(value["fn"]), arg=deserialize_expr(value["arg"]))
    elif expr_type == "lam":
        return Lam(
            binderName=value["binderName"],
            binderType=deserialize_expr(value["binderType"]),
            body=deserialize_expr(value["body"]),
            binderInfo=value["binderInfo"],
        )
    elif expr_type == "forallE":
        return ForallE(
            binderName=value["binderName"],
            binderType=deserialize_expr(value["binderType"]),
            body=deserialize_expr(value["body"]),
            binderInfo=value["binderInfo"],
        )
    elif expr_type == "letE":
        return LetE(
            declName=value["declName"],
            type=deserialize_expr(value["type"]),
            value=deserialize_expr(value["value"]),
            body=deserialize_expr(value["body"]),
            nonDep=value["nonDep"],
        )
    elif expr_type == "lit":
        return Lit(literal=value["literal"])
    elif expr_type == "mdata":
        return MData(data=value["data"], expr=deserialize_expr(value["expr"]))
    elif expr_type == "proj":
        return Proj(
            typeName=value["typeName"],
            idx=value["idx"],
            struct=deserialize_expr(value["struct"]),
        )
    else:
        raise ValueError(f"Unknown expression type: {expr_type}")


def simplify_forall_expr(expr: YourExpr) -> YourExpr:
    if isinstance(expr, ForallE):
        if isinstance(expr.binderType, (BVar, FVar, MVar, Sort, Const)):
            return simplify_forall_expr(expr.body)
        else:
            processed_binder_type = simplify_forall_expr(expr.binderType)
            processed_body = simplify_forall_expr(expr.body)
            return ForallE(
                expr.binderName, processed_binder_type, processed_body, expr.binderInfo
            )

    elif isinstance(expr, App):
        processed_fn = simplify_forall_expr(expr.fn)
        processed_arg = simplify_forall_expr(expr.arg)
        return App(processed_fn, processed_arg)

    elif isinstance(expr, Lam):
        processed_binder_type = simplify_forall_expr(expr.binderType)
        processed_body = simplify_forall_expr(expr.body)
        return Lam(
            expr.binderName, processed_binder_type, processed_body, expr.binderInfo
        )

    elif isinstance(expr, LetE):
        processed_type = simplify_forall_expr(expr.type)
        processed_value = simplify_forall_expr(expr.value)
        processed_body = simplify_forall_expr(expr.body)
        return LetE(
            expr.declName, processed_type, processed_value, processed_body, expr.nonDep
        )

    elif isinstance(expr, MData):
        processed_expr = simplify_forall_expr(expr.expr)
        return MData(expr.data, processed_expr)

    elif isinstance(expr, Proj):
        processed_struct = simplify_forall_expr(expr.struct)
        return Proj(expr.typeName, expr.idx, processed_struct)

    else:
        return expr


def simplify_forall_expr_iter(expr: YourExpr) -> YourExpr:
    expr_new = simplify_forall_expr(expr)
    if expr_new != expr:
        return simplify_forall_expr_iter(expr_new)
    return expr


def simplify_lean_expr(expr: YourExpr) -> YourExpr:
    if isinstance(expr, App):
        simplified_fn = simplify_lean_expr(expr.fn)
        simplified_arg = simplify_lean_expr(expr.arg)

        def is_noise_const(e: YourExpr) -> bool:
            return isinstance(e, Const) and (
                "inst" in e.declName
                or ".to" in e.declName
                or ".of" in e.declName
                or "HAdd." in e.declName
            )

        if isinstance(simplified_fn, Const) and isinstance(simplified_arg, Const):

            if is_noise_const(simplified_fn):
                return simplified_fn
            elif is_noise_const(simplified_arg):
                return simplified_arg

        return App(fn=simplified_fn, arg=simplified_arg)

    elif isinstance(expr, Lam):
        simplified_binder_type = simplify_lean_expr(expr.binderType)
        simplified_body = simplify_lean_expr(expr.body)
        return Lam(
            binderName=expr.binderName,
            binderType=simplified_binder_type,
            body=simplified_body,
            binderInfo=expr.binderInfo,
        )

    elif isinstance(expr, ForallE):
        simplified_binder_type = simplify_lean_expr(expr.binderType)
        simplified_body = simplify_lean_expr(expr.body)
        return ForallE(
            binderName=expr.binderName,
            binderType=simplified_binder_type,
            body=simplified_body,
            binderInfo=expr.binderInfo,
        )

    elif isinstance(expr, LetE):
        simplified_type = simplify_lean_expr(expr.type)
        simplified_value = simplify_lean_expr(expr.value)
        simplified_body = simplify_lean_expr(expr.body)
        return LetE(
            declName=expr.declName,
            type=simplified_type,
            value=simplified_value,
            body=simplified_body,
            nonDep=expr.nonDep,
        )

    elif isinstance(expr, MData):
        simplified_expr = simplify_lean_expr(expr.expr)
        return MData(data=expr.data, expr=simplified_expr)

    elif isinstance(expr, Proj):
        simplified_struct = simplify_lean_expr(expr.struct)
        return Proj(typeName=expr.typeName, idx=expr.idx, struct=simplified_struct)

    else:
        # BVar, FVar, MVar, Sort, Const (非冗余函数/参数时), Lit
        return expr
