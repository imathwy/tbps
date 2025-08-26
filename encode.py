from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import json

from myexpr import deserialize_expr, simplify_forall_expr_iter
from compute.zss_compute import your_expr_to_treenode
from WL_embedding.db_utils import connect_to_db, fetch_theorems_batch
from WL_embedding.wl_kernel import compute_wl_encoding


def process_theorem(args):
    theorem, k = args
    theorem_name, expr_json = theorem
    try:
        theorem_expr = deserialize_expr(expr_json)
        theorem_expr = simplify_forall_expr_iter(theorem_expr)
        theorem_tree = your_expr_to_treenode(theorem_expr)
        wl_encoding, _ = compute_wl_encoding(theorem_tree, max_h=k)
        serialized_encoding = json.dumps(wl_encoding)
        return (theorem_name, serialized_encoding, k, None)
    except Exception as e:
        return (theorem_name, None, k, str(e))


def process_theorems_batch(theorems, k, num_processes=None):
    if num_processes is None:
        num_processes = cpu_count()
    with Pool(processes=num_processes) as pool:
        args = [(theorem, k) for theorem in theorems]
        results = list(
            tqdm(
                pool.imap(process_theorem, args),
                total=len(theorems),
                desc=f"thm (k={k})",
            )
        )
    theorem_trees = []
    for name, wl_encoding, depth, error in results:
        if error:
            print(f"thm {name} (k={depth}) fail: {error}")
        else:
            theorem_trees.append((name, wl_encoding, depth))
    return theorem_trees


def ensure_column_exists(conn, table_name, column_name, column_type="jsonb"):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """,
        (table_name, column_name),
    )
    if not cursor.fetchone():
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )
        conn.commit()


def preprocess_theorems(table_name, k, batch_size=10000, num_processes=None):
    conn = connect_to_db()
    if conn is None:
        return

    wl_encode_column = f"simp_wl_encode_{k}"
    ensure_column_exists(conn, "wl_encodings_new", wl_encode_column)

    total_theorems = 217555
    offset = 0

    with tqdm(total=total_theorems, desc=f"Overall progress (k={k})") as pbar:
        while offset < total_theorems:
            theorems = fetch_theorems_batch(conn, table_name, offset, batch_size)
            if not theorems:
                print(f"No data at offset {offset}, ending processing")
                break

            theorem_results = process_theorems_batch(theorems, k, num_processes)
            cursor = conn.cursor()
            for theorem_name, serialized_encoding, depth in theorem_results:
                try:
                    cursor.execute(
                        f"""
                        UPDATE wl_encodings_new
                        SET {wl_encode_column} = %s
                        WHERE theorem_name = %s
                    """,
                        (serialized_encoding, theorem_name),
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Failed to store theorem {theorem_name} (k={depth}): {e}")

            offset += batch_size
            print(f"Batch processing completed, current offset: {offset}")
            pbar.update(batch_size)

    conn.close()
    print(f"Preprocessing completed (k={k})")


if __name__ == "__main__":
    # 1，3，5,10,20, 40, 80
    k = 80
    preprocess_theorems("mathlib_filtered", k, batch_size=5000, num_processes=2)
