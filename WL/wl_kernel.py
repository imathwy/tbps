# wl_kernel.py
from collections import defaultdict
from typing import Dict
import hashlib


def initialize_labels(tree_node) -> dict[int, str]:
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


def initialize_labels_new(tree_node) -> dict[int, str]:
    labels: Dict[int, str] = {}  # Explicit type hint for dictionary

    simplify_label_prefixes = ("BVar", "FVar", "MVar", "Sort", "Const")

    def traverse(node, node_id: int = 0, depth: int = 0) -> int:

        base_label = node.label
        for prefix in simplify_label_prefixes:
            if node.label.startswith(prefix):
                base_label = prefix
                break
        label_str = f"{base_label}_d{depth}"
        labels[node_id] = label_str

        next_id = node_id + 1
        for child in node.get_children():
            next_id = traverse(child, next_id, depth + 1)
        return next_id

    traverse(tree_node)
    return labels


def wl_iteration(tree_node, labels: dict[int, str]) -> dict[int, str]:
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


def get_label_histogram(labels: Dict[int, str]) -> Dict[str, int]:
    histogram = defaultdict(int)
    for label in labels.values():
        histogram[label] += 1
    return dict(histogram)


def compute_wl_kernel(hist1: Dict[str, int], hist2: Dict[str, int]) -> float:
    kernel_value = 0.0
    for label in set(hist1.keys()) & set(hist2.keys()):
        kernel_value += hist1[label] * hist2[label]
    return kernel_value


# wl_kernel.py
def wl_kernel(tree1, tree2, iterations: int = 2, debug: bool = False) -> float:
    labels1 = initialize_labels(tree1)
    labels2 = initialize_labels(tree2)

    histograms1 = [get_label_histogram(labels1)]
    histograms2 = [get_label_histogram(labels2)]

    for i in range(iterations):
        labels1 = wl_iteration(tree1, labels1)
        labels2 = wl_iteration(tree2, labels2)
        histograms1.append(get_label_histogram(labels1))
        histograms2.append(get_label_histogram(labels2))

    total_kernel = 0.0
    for h1, h2 in zip(histograms1, histograms2):
        kernel_value = compute_wl_kernel(h1, h2)
        norm_factor = sum(h1.values()) * sum(h2.values())
        total_kernel += kernel_value / norm_factor if norm_factor > 0 else 0

    if debug:
        print(f"Normalized WL kernel: {total_kernel}")
    return total_kernel
