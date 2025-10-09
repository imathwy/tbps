import time
import psycopg2
from tqdm import tqdm
import concurrent.futures
from typing import Tuple, List, Optional
from concurrent.futures import ProcessPoolExecutor
import os
import csv
import math
from search_app.myexpr import YourExpr, deserialize_expr, simplify_forall_expr_iter
from search_app.compute.zss_compute import (
    TreeNode,
    zss_edit_distance_TreeNode,
    your_expr_to_treenode,
    count_nodes,
    const_decl_name_similarity,
    can_t1_collapse_match_t2_soft,
)
from search_app.WL.db_utils import load_filtered_theorems, connect_to_db, DB_CONFIG


def process_candidate(
    candidate: Tuple[str, str, float, TreeNode],
) -> Tuple[str, Optional[TreeNode], int, float, float]:
    name, expr_json, wl_score, target_tree = candidate
    try:
        theorem_expr = deserialize_expr(expr_json)

        theorem_expr = simplify_forall_expr_iter(theorem_expr)

        theorem_tree = your_expr_to_treenode(theorem_expr)

        syntactic_similarity = can_t1_collapse_match_t2_soft(target_tree, theorem_tree)

        theorem_size = count_nodes(theorem_tree)

        return (name, theorem_tree, theorem_size, wl_score, syntactic_similarity)
    except Exception as e:
        print(f"Error processing {name}: {str(e)[:100]}")
        return (name, None, 0, wl_score)


def precompute_candidates(
    filtered_results: List[Tuple[str, float]],
    target_tree: TreeNode,
    max_workers: int = 4,
) -> List[Tuple[str, Optional[TreeNode], int, float, float]]:
    names = [cand[0] for cand in filtered_results]
    name_to_score = dict(filtered_results)

    candidates_data = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name, expr_cse_json
            FROM mathlib_filtered
            WHERE name IN %s
        """,
            (tuple(names),),
        )

        results = cur.fetchall()
        if len(results) != len(names):
            print(
                f"Warning: Expected to load {len(names)} data entries, actually loaded {len(results)}"
            )

        for name, expr_json in results:
            wl_score = name_to_score.get(name, 0.0)
            candidates_data.append((name, expr_json, wl_score, target_tree))

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    precomputed_candidates = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:

        results = tqdm(
            executor.map(process_candidate, candidates_data),
            total=len(candidates_data),
            desc="process_candidate",
        )

        for result in results:
            if result[1] is not None:
                precomputed_candidates.append(result)

    return precomputed_candidates


def process_theorem(
    data: tuple[str, TreeNode, int, float, float], target_tree, target_size: int
):
    """Compute edit similarity using precomputed theorem_expr and theorem_size."""
    theorem_name, theorem_tree, theorem_size, wl_score, syntactic_similarity = data

    try:
        if target_size > 50 :
            alpha, gamma, delta = 0.15, 0.30, 0.15
            similarity = alpha * wl_score + gamma * syntactic_similarity + delta * const_decl_name_similarity(target_tree, theorem_tree)
            return (theorem_name, similarity, wl_score)
        distance = zss_edit_distance_TreeNode(target_tree, theorem_tree)
        if distance == float('inf'):
            return None

        max_size = max(target_size, theorem_size)
        similarity = 1 - (distance / max_size) if max_size > 0 else 0.0
        alpha, beta, gamma, delta = 0.15, 0.40, 0.30, 0.15

        similarity = alpha * wl_score + beta * similarity + gamma * syntactic_similarity + delta * const_decl_name_similarity(target_tree, theorem_tree)

        return (theorem_name, similarity, wl_score)
    except Exception as e:
        print(f"Error)) processing {theorem_name}: {e}")
        return None


def calculate_overall_metrics(all_ranks):
    """Calculate overall evaluation metrics based on collected ranks."""
    k_values = [1, 5, 10]
    total_queries = len(all_ranks)

    # Initialize sums for each metric
    recall_sums = {k: 0 for k in k_values}
    precision_sums = {k: 0 for k in k_values}
    f1_sums = {k: 0 for k in k_values}
    ndcg_sums = {k: 0 for k in k_values}
    mrr_sum = 0

    for target_name, rank in all_ranks:
        if rank is None:
            continue  # Skip if target not found

        # Calculate MRR
        # print(rank)
        mrr_sum += 1 / rank

        for k in k_values:
            if rank <= k:
                recall_sums[k] += 1
                precision_sums[k] += 1 / k
                f1 = 2 * (1 / k) / (1 + 1 / k)  # Simplified F1 for single relevant item
                f1_sums[k] += f1
                dcg = 1 / math.log2(rank + 1)
                idcg = 1 / math.log2(2)
                ndcg_sums[k] += dcg / idcg

    # Calculate averages
    for k in k_values:
        recall_k = recall_sums[k] / total_queries
        precision_k = precision_sums[k] / total_queries
        f1_k = f1_sums[k] / total_queries
        ndcg_k = ndcg_sums[k] / total_queries
        print(f"Recall@{k}: {recall_k:.4f}")
        print(f"Precision@{k}: {precision_k:.4f}")
        print(f"F1-score@{k}: {f1_k:.4f}")
        print(f"nDCG@{k}: {ndcg_k:.4f}")

    mrr = mrr_sum / total_queries
    print(f"MRR: {mrr:.4f}")


def process_single_prop(target_name: str, target_expr: YourExpr, output_file: str):
    """Process a single proposition and append results to a CSV file."""
    start_time = time.time()

    # Precompute target-related values
    target_tree = your_expr_to_treenode(target_expr)
    target_node_count = count_nodes(target_tree)
    top_k = 1500  # 8500

    print("-" * 50)
    print(target_node_count)
    node_ratio = 1.2  # 1.2
    if target_node_count >= 600:
        node_ratio = 1.8

    # Load filtered theorems with WL scores
    filtered_results, wl_stats = load_filtered_theorems(
        target_name=target_name,
        database_name="mathlib_filtered",
        target_expr=target_expr,
        node_ratio=node_ratio,  # 1.05
        batch_size=90000,
        top_k=top_k,
        use_clustering=False,
        wl_iterations=3,  # 1,3,10,20,40,80
        debug=False,
    )
    if wl_stats == False:
        return False

    simptree = simplify_forall_expr_iter(target_expr)
    precomputed_candidates = precompute_candidates(
        filtered_results, your_expr_to_treenode(simptree)
    )

    # Parallel computation of edit similarities
    results = []

    target_tree = your_expr_to_treenode(simptree)
    # print(calculate_tree_depth(target_tree))
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        future_to_name = {
            executor.submit(
                process_theorem, data, target_tree, target_node_count
            ): data[0]
            for data in precomputed_candidates
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_to_name),
            total=len(future_to_name),
            desc=f"Processing {target_name}",
            unit="thm",
        ):
            result = future.result()
            if result is not None:
                results.append(result)

    results.sort(key=lambda x: x[1], reverse=True)

    # Calculate ranks with ties
    ranked_results = []
    current_rank = 1
    prev_similarity = None
    for i, (name, similarity, wl_score) in enumerate(results):
        if similarity != prev_similarity:
            current_rank = i + 1  # New rank for different similarity
        ranked_results.append((name, similarity, wl_score, current_rank))
        prev_similarity = similarity

    # Extract top 10 results with ranks
    top_10 = ranked_results[:10]
    top_10_names = [name for name, _, _, _ in top_10]
    top_10_similarities = [similarity for _, similarity, _, _ in top_10]
    top_10_wl_scores = [wl_score for _, _, wl_score, _ in top_10]
    top_10_ranks = [rank for _, _, _, rank in top_10]

    # Format top 10 into strings
    top_10_names_str = "; ".join(top_10_names)
    top_10_similarities_str = "; ".join(f"{s:.4f}" for s in top_10_similarities)
    top_10_wl_scores_str = "; ".join(f"{s:.4f}" for s in top_10_wl_scores)
    top_10_ranks_str = "; ".join(str(r) for r in top_10_ranks)

    # Determine target rank and whether it's in top 10
    target_entry = next(
        (entry for entry in ranked_results if entry[0] == target_name), None
    )
    if target_entry:
        target_rank = target_entry[3]  # Get the computed rank
        is_in_top_10 = "Yes" if target_rank <= 10 else "No"
        target_rank_str = str(target_rank)
    else:
        is_in_top_10 = "No"
        target_rank_str = "Not found"

    # Prepare the row
    row = [
        target_name,
        top_10_names_str,
        top_10_similarities_str,
        top_10_wl_scores_str,
        top_10_ranks_str,
        target_rank_str,
        is_in_top_10,
    ]

    # Define the header
    header = [
        "Target Name",
        "Top 10 Names",
        "Top 10 Edit Similarities",
        "Top 10 WL Scores",
        "Top 10 Ranks",
        "Target Rank",
        "Is Target in Top 10",
    ]

    # Check if file exists before opening
    file_exists = os.path.exists(output_file)

    # Save results to CSV in append mode
    with open(output_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)

    # Calculate processing time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print summary statistics
    print(f"\nResults for '{target_name}':")
    print(f"Processed {len(results)} valid theorems in {elapsed_time:.2f} seconds.")
    if results:
        print(f"Top Edit Similarity: {results[0][1]:.4f}")
        print(f"Top WL Score: {results[0][2]:.4f}")
        print(f"Top 5 Theorems with Ranks:")
        for i, (name, similarity, wl_score, rank) in enumerate(ranked_results[:5], 1):
            print(
                f"{rank}. {name} => Edit Similarity: {similarity:.4f}, WL Score: {wl_score:.4f}"
            )

    # Check target theorem’s rank
    if target_entry:
        target_similarity, target_wl_score, target_rank = (
            target_entry[1],
            target_entry[2],
            target_entry[3],
        )
        print(
            f"Target '{target_name}' rank: {target_rank}, Edit Similarity: {target_similarity:.4f}, WL Score: {target_wl_score:.4f}"
        )
    else:
        print(f"Target '{target_name}' not found in results.")
        with open("not_found_in_results", "a", encoding="utf-8", newline="") as f:
            f.writelines(f"Target '{target_name}' not found in results.\n")
        return top_k

    return target_rank

def fetch_theorem_details(conn, name: str) -> Tuple[Optional[str], Optional[int]]:
    """Fetch statement_str and node_count for a given theorem name from the database."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT statement_str, node_count FROM mathlib_filtered WHERE name = %s",
                (name,)
            )
            result = cur.fetchone()
            return result if result else (None, None)
    except psycopg2.Error as e:
        print(f"Database error for theorem {name}: {e}")
        return None, None
def process_single_prop_new(target_expr: YourExpr, k: int) -> list[tuple[str, float, str, int]]:
    """Process a single proposition and return top k theorems with similarities."""

    # Precompute target-related values
    target_tree = your_expr_to_treenode(target_expr)
    target_node_count = count_nodes(target_tree)
    top_k = 1500  # Use provided k value

    # Adjust node ratio based on node count
    node_ratio = 1.2
    if target_node_count >= 600:
        node_ratio = 1.8

    # Load filtered theorems with WL scores
    filtered_results, wl_stats = load_filtered_theorems(
        target_name="",  # No target name needed for ranking
        database_name="mathlib_filtered",
        target_expr=target_expr,
        node_ratio=node_ratio,
        batch_size=90000,
        top_k=top_k,
        use_clustering=False,
        wl_iterations=3,
        debug=False,
    )
    if wl_stats == False:
        return []

    # Simplify expression and precompute candidates
    simptree = simplify_forall_expr_iter(target_expr)
    precomputed_candidates = precompute_candidates(
        filtered_results, your_expr_to_treenode(simptree)
    )

    # Parallel computation of edit similarities
    results = []
    target_tree = your_expr_to_treenode(simptree)
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        future_to_name = {
            executor.submit(
                process_theorem, data, target_tree, target_node_count
            ): data[0]
            for data in precomputed_candidates
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_to_name),
            total=len(future_to_name),
            desc="Processing theorems",
            unit="thm",
        ):
            result = future.result()
            if result is not None:
                results.append(result)

    # Sort results by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)

    # Extract top k results (name, similarity)
    top_k_results = []
    conn = connect_to_db()
    try:
        for name, similarity, _ in results[:k]:
            statement_str, node_count = fetch_theorem_details(conn, name)
            # Only include results with valid database entries
            if statement_str is not None and node_count is not None:
                top_k_results.append((name, similarity, statement_str, node_count))
            else:
                print(f"Warning: Could not fetch details for theorem {name}")
    finally:
        conn.close()

    return top_k_results
