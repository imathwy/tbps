import json
import numpy as np
import psycopg2
import pickle
import concurrent.futures
from tqdm import tqdm
import os
import logging

from myexpr import deserialize_expr, simplify_forall_expr_iter
from compute.zss_compute import (
    your_expr_to_treenode,
    count_nodes,
    can_t1_collapse_match_t2_soft,
)
from WL_embedding.wl_kernel import compute_wl_encoding, compute_wl_kernel
from WL_embedding.db_utils import connect_to_db, DB_CONFIG


def check_name_in_batch(batch: list, target_name: str) -> bool:
    """
    Check if a specific name exists in the current batch of records.

    Args:
        batch: List of tuples from database query, where each tuplename, wl_encoding)
        target_name: The name to search for in the batch

    Returns:
        bool: True if name exists in batch, False otherwise
    """
    return any(record[0] == target_name for record in batch)


def wl_to_vector(
    wl_encoding: dict,
    feature_map: dict,
    feature_weights: dict = None,
    max_features: int = 5000,
) -> np.ndarray:
    vector = np.zeros(min(len(feature_map), max_features))
    for key, count in wl_encoding.items():
        if key in feature_map:
            idx = feature_map[key]
            if idx < max_features:
                weight = feature_weights.get(key, 1.0) if feature_weights else 1.0
                vector[idx] = count * weight
    return vector


def load_kmeans_model(n_clusters: int = 2000):
    model_path = "kmeans_model.pkl"
    feature_map_path = "feature_map.pkl"
    feature_weights_path = "feature_weights.pkl"
    pca_path = "pca_model.pkl"

    for path in [model_path, feature_map_path, feature_weights_path]:
        assert os.path.exists(path)
    with open(model_path, "rb") as f:
        kmeans = pickle.load(f)
    with open(feature_map_path, "rb") as f:
        feature_map = pickle.load(f)
    with open(feature_weights_path, "rb") as f:
        feature_weights = pickle.load(f)
    pca = pickle.load(open(pca_path, "rb")) if os.path.exists(pca_path) else None

    _key_labels = ["forallE", "Not", "Nat", "app", "fvar"]
    return kmeans, feature_map, feature_weights, pca


def compute_wl_score(item: tuple[str, str], target_encoding: dict) -> tuple[str, float]:
    name, wl_encoding_json = item
    try:
        wl_encoding = wl_encoding_json
        # print(wl_encoding)
        wl_score = compute_wl_kernel(target_encoding, wl_encoding)
        # print(wl_score)
        return (name, wl_score)
    except Exception as e:
        return (name, 0.0)


def compute_wl_score_new(
    item: tuple[str, str, str], simptree, target_encoding: dict
) -> tuple[str, float]:
    name, wl_encoding_json, thmtree = item
    thmtree = your_expr_to_treenode(
        simplify_forall_expr_iter(deserialize_expr(thmtree))
    )
    try:
        wl_encoding = wl_encoding_json
        # print(wl_encoding)
        wl_score = compute_wl_kernel(target_encoding, wl_encoding)
        s = can_t1_collapse_match_t2_soft(simptree, thmtree)
        alpha = 0.5
        wl_score = alpha * wl_score + (1 - alpha) * s
        # print(wl_score)
        return (name, wl_score)
    except Exception as e:
        print(f"计算WL分数失败 ({name}): {e}")
        return (name, 0.0)


def load_filtered_theorems(
    target_name: str,
    database_name: str = "mathlib",
    target_expr=None,
    node_ratio: float = 1.5,
    node_diff: int = 25,  # 15
    batch_size: int = 50000,
    top_k: int = 3000,
    n_closest_clusters: int = 2250,
    use_clustering: bool = True,
    wl_iterations: int = 80,  # New parameter: Number of WL iterations
    debug: bool = False,
):
    """
    Load the top-k theorems filtered by node count and (optionally) clustering, ranked by WL score.

    Args:
        target_name: Name of the target theorem
        database_name: Source database table name
        target_expr: Target expression
        node_ratio: Node count filtering ratio
        node_diff: Absolute node count difference
        batch_size: Number of records to process per batch
        top_k: Number of top results to return
        n_closest_clusters: Number of closest clusters to consider (used if use_clustering=True)
        use_clustering: Whether to use clustering model for filtering
        wl_iterations: Number of WL iterations to determine the WL encoding column
        debug: Whether to print debug information

    Returns:
        tuple: (filtered_results, wl_stats)
    """
    # Compute node count and WL encoding for the target tree
    try:
        simptree = simplify_forall_expr_iter(target_expr)
        target_tree = your_expr_to_treenode(simptree)

        # target_node_count = count_nodes(target_tree)
        target_simp_node_count = count_nodes(target_tree)
        target_node_count = target_simp_node_count
        # target_tree = simptree
        target_encoding, _ = compute_wl_encoding(target_tree, max_h=wl_iterations)
        logging.info(
            f"Target tree node count: {target_node_count}, WL encoding: {list(target_encoding.items())[:10]}"
        )
    except Exception as e:
        print(f"Failed to generate target tree: {e}")
        logging.error(f"Failed to generate target tree: {e}")
        return [], {"wl_min": 0.0, "wl_max": 0.0, "wl_avg": 0.0}

    # Calculate node count range
    min_nodes = min(target_node_count / node_ratio, target_node_count - node_diff)
    min_nodes = max(0, min_nodes)
    max_nodes = max(target_node_count * node_ratio, target_node_count + node_diff)
    print(f"Node count filter range: [{min_nodes}, {max_nodes}]")
    logging.info(f"Node count filter range: [{min_nodes}, {max_nodes}]")

    all_candidates = []

    try:
        conn = connect_to_db()
        cur = conn.cursor()

        # Dynamically generate WL encoding column name based on wl_iterations
        wl_column = f"w.simp_wl_encode_{wl_iterations}"

        if use_clustering:
            # Load clustering model
            try:
                kmeans, feature_map, feature_weights, pca = load_kmeans_model()
            except FileNotFoundError as e:
                print(e)
                logging.error(str(e))
                return [], {"wl_min": 0.0, "wl_max": 0.0, "wl_avg": 0.0}

            # Predict target cluster
            target_vector = wl_to_vector(
                target_encoding, feature_map, feature_weights, max_features=5000
            )
            target_vector = pca.transform([target_vector])[0] if pca else target_vector
            distances = kmeans.transform([target_vector])[0]
            closest_clusters = np.argsort(distances)[:n_closest_clusters]
            logging.info(
                f"Closest {n_closest_clusters} clusters: {closest_clusters.tolist()}"
            )

            # Query total theorems matching node count and clusters
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM {database_name} AS d
                JOIN wl_encodings_new AS w ON d.name = w.theorem_name
                WHERE d.expr_cse_json != 'null'
                AND d.simp_node_count BETWEEN %s AND %s
                AND w.cluster_id = ANY(%s)
            """,
                (min_nodes, max_nodes, closest_clusters.tolist()),
            )
        else:
            # Query total theorems matching node count only
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM {database_name} AS d
                WHERE d.expr_cse_json != 'null'
                AND d.simp_node_count BETWEEN %s AND %s
            """,
                (min_nodes, max_nodes),
            )

        total_filtered = cur.fetchone()[0]
        print(
            f"Filtered by node count{' and clustering' if use_clustering else ''}: {total_filtered} candidate theorems"
        )
        logging.info(
            f"Filtered by node count{' and clustering' if use_clustering else ''}: {total_filtered} candidate theorems"
        )

        # Load in batches
        for offset in range(0, total_filtered, batch_size):
            if use_clustering:
                cur.execute(
                    f"""
                    SELECT d.name, {wl_column}, d.expr_cse_json  
                    FROM {database_name} AS d
                    JOIN wl_encodings_new AS w ON d.name = w.theorem_name
                    WHERE d.expr_cse_json != 'null'
                    AND d.simp_node_count BETWEEN %s AND %s
                    AND w.cluster_id = ANY(%s)
                    LIMIT %s OFFSET %s
                """,
                    (
                        min_nodes,
                        max_nodes,
                        closest_clusters.tolist(),
                        batch_size,
                        offset,
                    ),
                )
            else:
                cur.execute(
                    f"""
                    SELECT d.name, {wl_column}, d.expr_cse_json  
                    FROM {database_name} AS d
                    JOIN wl_encodings_new AS w ON d.name = w.theorem_name
                    WHERE d.expr_cse_json != 'null'
                    AND d.simp_node_count BETWEEN %s AND %s
                    LIMIT %s OFFSET %s
                """,
                    (min_nodes, max_nodes, batch_size, offset),
                )

            batch = cur.fetchall()
            print(f"Batch {offset}: Loaded {len(batch)} records")
            logging.info(f"Batch {offset}: Loaded {len(batch)} records")

            if check_name_in_batch(batch, target_name):
                print(f"Found {target_name} in current batch")
                logging.info(f"Found {target_name} in current batch")
            else:
                print(f"Did not find {target_name} in current batch")
                logging.info(f"Did not find {target_name} in current batch")

            # Compute WL scores in parallel
            with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
                results = list(
                    tqdm(
                        executor.map(
                            compute_wl_score_new,
                            batch,
                            [target_tree] * len(batch),
                            [target_encoding] * len(batch),
                        ),
                        total=len(batch),
                        desc=f"WL score computation Batch {offset}",
                    )
                )
            all_candidates.extend(
                [r for r in results if r[1] >= 0]
            )  # Keep only non-zero scores

        # Global sampling if clustering is used and candidates are insufficient
        if use_clustering and total_filtered < top_k:
            print("Insufficient candidates, initiating global sampling")
            logging.info("Insufficient candidates, initiating global sampling")
            cur.execute(
                f"""
                SELECT d.name, {wl_column}
                FROM {database_name} AS d
                JOIN wl_encodings_new AS w ON d.name = w.theorem_name
                WHERE d.expr_cse_json != 'null'
                AND d.simp_node_count BETWEEN %s AND %s
                AND (w.cluster_id IS NULL OR w.cluster_id != ALL(%s))
                ORDER BY RANDOM()
                LIMIT %s
            """,
                (min_nodes, max_nodes, closest_clusters.tolist(), 5000),
            )
            random_batch = cur.fetchall()
            print(f"Global sampling: Loaded {len(random_batch)} records")
            logging.info(f"Global sampling: Loaded {len(random_batch)} records")

            with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
                results = list(
                    tqdm(
                        executor.map(
                            compute_wl_score,
                            random_batch,
                            [target_encoding] * len(random_batch),
                        ),
                        total=len(random_batch),
                        desc="Global sampling WL score computation",
                    )
                )
            all_candidates.extend([r for r in results if r[1] > 0])

        # Debug samples when clustering is used
        if debug and use_clustering:
            for cluster_id in closest_clusters[:2]:
                cur.execute(
                    f"""
                    SELECT d.name, {wl_column}
                    FROM {database_name} AS d
                    JOIN wl_encodings_new AS w ON d.name = w.theorem_name
                    WHERE w.cluster_id = %s
                    LIMIT 1
                """,
                    (int(cluster_id),),
                )
                sample = cur.fetchone()
                if sample:
                    name, wl_json = sample
                    wl_encoding = json.loads(wl_json)
                    print(
                        f"Cluster {cluster_id} sample theorem: {name}, WL encoding: {list(wl_encoding.items())[:10]}"
                    )
                    logging.info(
                        f"Cluster {cluster_id} sample theorem: {name}, WL encoding: {list(wl_encoding.items())[:10]}"
                    )

        cur.close()
        conn.close()

        # Sort and take top_k
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        index = next(
            (
                i
                for i, (name, score) in enumerate(all_candidates)
                if name == target_name
            ),
            -1,
        )

        if index != -1:
            print(f"'{target_name}' ranked at position {index + 1} (index {index})")
            if index + 1 > top_k:
                return 0, False
        else:
            print(f"'{target_name}' not in candidate list")
        filtered_results = all_candidates[: min(top_k, len(all_candidates))]

        # Compute WL statistics
        wl_scores = [x[1] for x in filtered_results] if filtered_results else [0.0]
        wl_stats = {
            "wl_min": min(wl_scores),
            "wl_max": max(wl_scores),
            "wl_avg": sum(wl_scores) / len(wl_scores) if wl_scores else 0.0,
            "total_candidates": len(all_candidates),
            "filtered_candidates": len(filtered_results),
        }

        if debug:
            print(
                f"WL scores - Min: {wl_stats['wl_min']:.2f}, Max: {wl_stats['wl_max']:.2f}, Avg: {wl_stats['wl_avg']:.2f}"
            )
            print(f"Pre-filter candidates: {len(all_candidates)}")
            print(f"Post-filter candidates: {len(filtered_results)}")
        print(f"Returning top-{top_k}: {len(filtered_results)} candidate theorems")
        logging.info(
            f"Returning top-{top_k}: {len(filtered_results)} candidate theorems"
        )

        return filtered_results, wl_stats

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        logging.error(f"Database error: {e}")
        return [], {"wl_min": 0.0, "wl_max": 0.0, "wl_avg": 0.0}


def check_target_existence(
    database_name: str = "mathlib",
    target_name: str = None,
    target_node_count: int = None,
    node_ratio: float = 1.2,
):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT COUNT(*), 
                   EXISTS(SELECT 1 FROM {database_name} WHERE name = %s AND expr_cse_json != 'null'),
                   (SELECT node_count FROM {database_name} WHERE name = %s AND expr_cse_json != 'null')
            FROM {database_name}
            WHERE expr_cse_json != 'null'
        """,
            (target_name, target_name),
        )
        total_records, target_exists_before, target_db_node_count = cur.fetchone()
        print(f"Total records before filtering: {total_records}")
        print(
            f"Target '{target_name}' in database before filtering: {'Yes' if target_exists_before else 'No'}"
        )
        if target_exists_before:
            print(
                f"Target '{target_name}' node count in database: {target_db_node_count}"
            )
        if target_node_count is not None:
            print(f"Target node count (input): {target_node_count}")

        if target_node_count is None:
            print("No target_node_count provided, skipping post-filtering check.")
            cur.close()
            conn.close()
            return

        min_nodes = target_node_count / node_ratio
        max_nodes = target_node_count * node_ratio

        cur.execute(
            f"""
            SELECT COUNT(*), 
                   EXISTS(
                       SELECT 1 FROM {database_name}
                       WHERE name = %s AND expr_cse_json != 'null'
                       AND node_count BETWEEN %s AND %s
                   )
            FROM {database_name}
            WHERE expr_cse_json != 'null'
            AND node_count BETWEEN %s AND %s
        """,
            (target_name, min_nodes, max_nodes, min_nodes, max_nodes),
        )
        total_filtered_records, target_exists_after = cur.fetchone()
        print(f"\nTotal records after node count filtering: {total_filtered_records}")
        print(
            f"Target '{target_name}' in filtered results: {'Yes' if target_exists_after else 'No'}"
        )
        if not target_exists_after and target_exists_before:
            print(f"Target node count in database: {target_db_node_count}")
            print(f"Filter range: [{min_nodes:.1f}, {max_nodes:.1f}]")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        raise
