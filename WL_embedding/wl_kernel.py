# wl_kernel.py
import hashlib
from collections import defaultdict
from typing import Dict
from compute.zss_compute import TreeNode, calculate_tree_depth


def initialize_labels_old(tree_node: TreeNode) -> dict[int, str]:
    labels = {}

    def traverse(node, node_id=0, depth=0):
        label_str = f"{str(node.label)}_d{depth}"
        labels[node_id] = label_str

        next_id = node_id + 1
        for child in node.get_children():
            next_id = traverse(child, next_id, depth + 1)
        return next_id

    traverse(tree_node)
    return labels


def initialize_labels(tree_node: TreeNode) -> dict[int, str]:
    labels: Dict[int, str] = {}  # Explicit type hint for dictionary

    simplify_label_prefixes = ("BVar", "FVar", "MVar", "Sort", "Const")

    def traverse(node: TreeNode, node_id: int = 0, depth: int = 0) -> int:

        base_label = node.label
        for prefix in simplify_label_prefixes:
            if node.label.startswith(prefix):
                base_label = prefix
                break  # Found a matching prefix, no need to check others

        label_str = f"{base_label}_d{depth}"
        labels[node_id] = label_str

        next_id = node_id + 1
        for child in node.get_children():
            next_id = traverse(child, next_id, depth + 1)
        return next_id

    traverse(tree_node)
    return labels


def wl_iteration(tree_node: TreeNode, labels: dict[int, str]) -> dict[int, str]:
    new_labels = {}

    def traverse(node, node_id=0):
        children_labels = []
        next_id = node_id + 1
        for child in node.get_children():
            child_id = next_id
            next_id = traverse(child, next_id)
            children_labels.append(labels[child_id])

        new_label = labels[node_id]
        if children_labels:
            new_label += "(" + ",".join(sorted(children_labels)) + ")"
        hashed_label = hashlib.md5(new_label.encode()).hexdigest()
        new_labels[node_id] = hashed_label

        return next_id

    traverse(tree_node)
    return new_labels


def get_label_histogram(labels: dict) -> dict:
    histogram = defaultdict(int)
    for label in labels.values():
        histogram[label] += 1
    return dict(histogram)


def compute_wl_encoding(tree: TreeNode, max_h=5):
    tree_depth = calculate_tree_depth(tree)
    h = min(tree_depth, max_h)

    labels = initialize_labels(tree)

    histograms = []
    for i in range(h):
        labels = wl_iteration(tree, labels)
        hist = get_label_histogram(labels)
        histograms.append(hist)
    combined_hist = {}
    for i, hist in enumerate(histograms):
        for label, count in hist.items():
            combined_hist[f"{i}_{label}"] = count
    return combined_hist, tree_depth


def compute_wl_kernel(wl1: dict, wl2: dict) -> float:

    if not wl1 or not wl2:
        return 0.0

    common = set(wl1.keys()) & set(wl2.keys())
    if not common:
        return 0.0

    score = sum(wl1[k] * wl2[k] for k in common)

    norm1 = sum(v * v for v in wl1.values()) ** 0.5
    norm2 = sum(v * v for v in wl2.values()) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    score = score / (norm1 * norm2)

    return max(0.0, min(1.0, score))
