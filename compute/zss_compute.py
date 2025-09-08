from typing import List, Set
import re
import zss
from myexpr import (
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


class TreeNode:
    def __init__(self, label: str, children: List["TreeNode"] = None):
        self.label = label  # 节点的标签，例如 "App" 或 "Lam(x)"
        self.children = children if children else []  # 子节点列表

    def get_children(self) -> List["TreeNode"]:
        return self.children

    def __str__(self):
        return f"TreeNode(label={self.label})"

    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False
        return self.label == other.label and self.children == other.children


def calculate_tree_depth(node: TreeNode) -> int:
    if not node.get_children():
        return 0
    return 1 + max(calculate_tree_depth(child) for child in node.get_children())


# 将 YourExpr 转换为 TreeNode
def your_expr_to_treenode(expr: YourExpr) -> TreeNode:
    label = type(expr).__name__
    if isinstance(expr, BVar):
        label += f"({expr.deBruijnIndex})"
        children = []
    elif isinstance(expr, FVar):
        label += f"({expr.fvarId})"
        children = []
    elif isinstance(expr, MVar):
        label += f"({expr.mvarId})"
        children = []
    elif isinstance(expr, Sort):
        label += f"({expr.u})"
        children = []
    elif isinstance(expr, Const):
        label += f"({expr.declName}, {expr.us})"
        children = []
    elif isinstance(expr, App):
        children = [your_expr_to_treenode(expr.fn), your_expr_to_treenode(expr.arg)]
    elif isinstance(expr, Lam):
        children = [
            your_expr_to_treenode(expr.binderType),
            your_expr_to_treenode(expr.body),
        ]
    elif isinstance(expr, ForallE):
        children = [
            your_expr_to_treenode(expr.binderType),
            your_expr_to_treenode(expr.body),
        ]
    elif isinstance(expr, LetE):
        children = [
            your_expr_to_treenode(expr.type),
            your_expr_to_treenode(expr.value),
            your_expr_to_treenode(expr.body),
        ]
    elif isinstance(expr, Lit):
        label += f"({expr.literal})"
        children = []
    elif isinstance(expr, MData):
        children = [your_expr_to_treenode(expr.expr)]
    elif isinstance(expr, Proj):
        children = [your_expr_to_treenode(expr.struct)]
    else:
        children = []

    return TreeNode(label, children)


def print_tree(node, level=0):
    print("  " * level + str(node))
    for child in node.get_children():
        print_tree(child, level + 1)


def count_nodes(tree: TreeNode) -> int:
    count = 1
    for child in tree.get_children():
        count += count_nodes(child)
    return count


def zss_edit_distance(expr1: YourExpr, expr2: YourExpr) -> int:
    tree1 = your_expr_to_treenode(expr1)
    tree2 = your_expr_to_treenode(expr2)

    num_nodes_1 = count_nodes(tree1)
    num_nodes_2 = count_nodes(tree2)
    node_diff_threshold = 1.5
    if (
        max(num_nodes_1, num_nodes_2) / min(num_nodes_1, num_nodes_2)
        > node_diff_threshold
    ):
        return float("inf")

    return zss.distance(
        tree1,
        tree2,
        get_children=lambda node: node.get_children(),
        insert_cost=lambda node: 1,
        # remove_cost=lambda node: 1,
        remove_cost=lambda node: 0 if isinstance(node, ForallE) else 1,
        update_cost=lambda a, b: (
            0 if a == b or (isinstance(a, ForallE) and isinstance(b, ForallE)) else 1
        ),
    )


def zss_edit_distance_TreeNode(tree1: TreeNode, tree2: TreeNode) -> int:
    zero_cost_label_prefixes = ("BVar(", "FVar(", "MVar(", "Sort(", "Const(")

    return zss.distance(
        tree1,
        tree2,
        get_children=lambda node: node.get_children(),
        insert_cost=lambda node: (
            0.2 if node.label.startswith(zero_cost_label_prefixes) else 1
        ),
        remove_cost=lambda node: (
            0.2 if node.label.startswith(zero_cost_label_prefixes) else 1
        ),
        update_cost=lambda a, b: (
            0.0
            if a == b
            or a.label.startswith(zero_cost_label_prefixes)
            or b.label.startswith(zero_cost_label_prefixes)
            else 0.4
        ),
    )


def expr_to_text(expr: YourExpr, indent: int = 0) -> str:
    indentation = "  " * indent
    lines = [f"{indentation}{type(expr).__name__}"]

    if isinstance(expr, App):
        lines.append(expr_to_text(expr.fn, indent + 1))
        lines.append(expr_to_text(expr.arg, indent + 1))
    elif isinstance(expr, Lam):
        lines.append(f"{indentation}  binderName: {expr.binderName}")
        lines.append(f"{indentation}  binderType:")
        lines.append(expr_to_text(expr.binderType, indent + 2))
        lines.append(f"{indentation}  body:")
        lines.append(expr_to_text(expr.body, indent + 2))
        lines.append(f"{indentation}  binderInfo: {expr.binderInfo}")
    elif isinstance(expr, ForallE):
        lines.append(f"{indentation}  binderName: {expr.binderName}")
        lines.append(f"{indentation}  binderType:")
        lines.append(expr_to_text(expr.binderType, indent + 2))
        lines.append(f"{indentation}  body:")
        lines.append(expr_to_text(expr.body, indent + 2))
        lines.append(f"{indentation}  binderInfo: {expr.binderInfo}")
    elif isinstance(expr, LetE):
        lines.append(f"{indentation}  declName: {expr.declName}")
        lines.append(f"{indentation}  type:")
        lines.append(expr_to_text(expr.type, indent + 2))
        lines.append(f"{indentation}  value:")
        lines.append(expr_to_text(expr.value, indent + 2))
        lines.append(f"{indentation}  body:")
        lines.append(expr_to_text(expr.body, indent + 2))
        lines.append(f"{indentation}  nonDep: {expr.nonDep}")
    elif isinstance(expr, MData):
        lines.append(f"{indentation}  data: {expr.data}")
        lines.append(f"{indentation}  expr:")
        lines.append(expr_to_text(expr.expr, indent + 2))
    elif isinstance(expr, Proj):
        lines.append(f"{indentation}  typeName: {expr.typeName}")
        lines.append(f"{indentation}  idx: {expr.idx}")
        lines.append(f"{indentation}  struct:")
        lines.append(expr_to_text(expr.struct, indent + 2))
    elif isinstance(expr, Const):
        lines.append(f"{indentation}  declName: {expr.declName}")
        lines.append(f"{indentation}  us: {expr.us}")
    elif isinstance(expr, Sort):
        lines.append(f"{indentation}  u: {expr.u}")
    elif isinstance(expr, BVar):
        lines.append(f"{indentation}  deBruijnIndex: {expr.deBruijnIndex}")
    elif isinstance(expr, FVar):
        lines.append(f"{indentation}  fvarId: {expr.fvarId}")
    elif isinstance(expr, MVar):
        lines.append(f"{indentation}  mvarId: {expr.mvarId}")
    elif isinstance(expr, Lit):
        lines.append(f"{indentation}  literal: {expr.literal}")
    # Add more elif blocks if you have more YourExpr types

    return "\n".join(lines)


def extract_const_decl_names(node: TreeNode, decl_names: Set[str]):
    if node.label.startswith("Const("):
        match = re.match(
            r"Const\((\w+)", node.label
        )  # Match "Const(" followed by word characters
        if match:
            decl_name = match.group(1)
            if "inst" not in decl_name:
                decl_names.add(decl_name)
        else:
            # Fallback for potentially more complex names or different formats
            try:
                start_index = node.label.find("(") + 1
                end_index = node.label.find(",", start_index)
                if start_index > 0 and end_index != -1:
                    decl_name = node.label[start_index:end_index].strip()
                    # Basic check to avoid adding empty or malformed names
                    if decl_name:
                        decl_names.add(decl_name)
            except Exception as e:
                print(
                    f"Warning: Could not parse declName from label '{node.label}': {e}"
                )

    for child in node.get_children():
        extract_const_decl_names(child, decl_names)


def get_const_decl_names_set(tree: TreeNode) -> Set[str]:
    decl_names = set()
    extract_const_decl_names(tree, decl_names)
    return decl_names


def const_decl_name_similarity(tree1: TreeNode, tree2: TreeNode) -> float:
    set1 = get_const_decl_names_set(tree1)
    set2 = get_const_decl_names_set(tree2)

    if not set1 and not set2:
        return 1.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def can_conform_by_collapse(t1_node: TreeNode, t2_node: TreeNode) -> bool:

    if not t2_node.get_children():
        return True

    else:
        if t1_node.label != t2_node.label:
            return False
        if len(t1_node.get_children()) != len(t2_node.get_children()):
            return False
        for i in range(len(t2_node.get_children())):
            if not can_conform_by_collapse(
                t1_node.get_children()[i], t2_node.get_children()[i]
            ):
                return False
        return True


def can_t1_collapse_match_t2(T1: TreeNode, T2: TreeNode) -> bool:
    return can_conform_by_collapse(T1, T2)


def count_treenodes(node: TreeNode) -> int:
    count = 1
    for child in node.get_children():
        count += count_treenodes(child)
    return count


def score_conform_by_collapse_recursive(t1_node: TreeNode, t2_node: TreeNode) -> float:
    if not t2_node.get_children():
        return 1.0
    else:
        if t1_node.label != t2_node.label:
            return 0.0
        if len(t1_node.get_children()) != len(t2_node.get_children()):
            return 0.0

        current_node_score = 1.0
        child_scores_sum = 0.0
        for i in range(len(t2_node.get_children())):
            child_scores_sum += score_conform_by_collapse_recursive(
                t1_node.get_children()[i], t2_node.get_children()[i]
            )

        return current_node_score + child_scores_sum


def can_t1_collapse_match_t2_soft(T1: TreeNode, T2: TreeNode) -> float:
    total_t2_nodes = count_treenodes(T2)
    if total_t2_nodes == 0:
        if count_treenodes(T1) == 0:
            return 1.0
        else:
            return 0.0

    raw_score = score_conform_by_collapse_recursive(T1, T2)
    return raw_score / total_t2_nodes
