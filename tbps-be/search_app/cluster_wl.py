import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from collections import Counter
import pickle
from tqdm import tqdm
import logging
from WL_embedding.db_utils import connect_to_db


logging.basicConfig(
    filename="cluster_wl_new.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


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


def get_feature_map(
    table_name: str,
    batch_size: int = 10000,
    max_features: int = 5000,
    total_count: int = 330000,
) -> tuple:
    conn = connect_to_db()
    cur = conn.cursor()

    feature_counts = Counter()
    invalid_count = 0
    offset = 0
    while True:
        cur.execute(
            f"""
            SELECT simp_wl_encode_3 
            FROM {table_name}
            WHERE simp_wl_encode_3  IS NOT NULL
            LIMIT %s OFFSET %s
        """,
            (batch_size, offset),
        )
        batch = cur.fetchall()
        if not batch:
            break
        for (wl_json,) in batch:
            try:
                wl_dict = wl_json
                if not wl_dict:
                    invalid_count += 1
                    print("???")
                    continue
                feature_counts.update(wl_dict.keys())
            except:
                invalid_count += 1
                continue
        offset += batch_size
        logging.info(
            f"Feature statistics: Processing {offset} entries, invalid {invalid_count} entries"
        )

    print(f"Invalid encoding record: {invalid_count} records")
    feature_weights = {
        k: np.log(total_count / v) for k, v in feature_counts.items() if v > 5
    }
    print(f"characteristic dimension: {len(feature_counts)}")
    feature_map = {
        feat: i for i, (feat, _) in enumerate(feature_counts.most_common(max_features))
    }

    print(f"characteristic dimension: {len(feature_map)}")
    logging.info(f"characteristic dimension: {len(feature_map)}")

    cur.close()
    conn.close()
    return feature_map, feature_weights


def clean_data(table_name: str):
    conn = connect_to_db()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE {table_name}
        SET simp_wl_encode_3  = '{{}}', cluster_id = NULL
        WHERE simp_wl_encode_3  IS NULL OR simp_wl_encode_3  = ''
    """
    )
    conn.commit()

    cur.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE simp_wl_encode_3  = '{{}}'
    """
    )
    empty_count = cur.fetchone()[0]
    print(f"Empty code records: {empty_count} records")
    logging.info(f"Empty code records: {empty_count} records")

    cur.close()
    conn.close()


def cluster_wl_encodings(
    table_name="wl_encodings_new",
    n_clusters=2000,
    batch_size=10000,
    max_features=5000,
    use_pca=True,
    pca_components=200,
):

    feature_map, feature_weights = get_feature_map(table_name, batch_size, max_features)

    with open("feature_map_new.pkl", "wb") as f:
        pickle.dump(feature_map, f)
    with open("feature_weights_new.pkl", "wb") as f:
        pickle.dump(feature_weights, f)

    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters, batch_size=batch_size, max_iter=300, random_state=42
    )
    pca = PCA(n_components=pca_components) if use_pca else None

    conn = connect_to_db()
    cur = conn.cursor()
    offset = 0
    total_processed = 0
    while True:
        cur.execute(
            f"""
            SELECT theorem_name, simp_wl_encode_3 
            FROM {table_name}
            LIMIT %s OFFSET %s
        """,
            (batch_size, offset),
        )
        batch = cur.fetchall()
        if not batch:
            break

        X = np.zeros((len(batch), min(max_features, len(feature_map))))
        valid_count = 0
        for i, (_, wl_json) in enumerate(tqdm(batch, desc=f"训练批次 {offset}")):
            try:
                wl_dict = wl_json
                if wl_dict:
                    X[valid_count] = wl_to_vector(
                        wl_dict, feature_map, feature_weights, max_features
                    )
                    valid_count += 1
            except:
                continue

        if valid_count > 0:
            X = X[:valid_count]
            if use_pca:
                X = pca.fit_transform(X) if offset == 0 else pca.transform(X)
            kmeans.partial_fit(X)
            total_processed += valid_count

        offset += batch_size

    with open("kmeans_model.pkl", "wb") as f:
        pickle.dump(kmeans, f)
    with open("pca_model.pkl", "wb") as f:
        pickle.dump(pca, f) if pca else None

    cur.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS cluster_id INTEGER")
    offset = 0
    while True:
        cur.execute(
            f"""
            SELECT theorem_name, simp_wl_encode_3 
            FROM {table_name}
            LIMIT %s OFFSET %s
        """,
            (batch_size, offset),
        )
        batch = cur.fetchall()
        if not batch:
            break

        X = np.zeros((len(batch), min(max_features, len(feature_map))))
        names = []
        valid_count = 0
        for i, (name, wl_json) in enumerate(
            tqdm(batch, desc=f"Predict Batch {offset}")
        ):
            try:
                wl_dict = wl_json
                if wl_dict:
                    X[valid_count] = wl_to_vector(
                        wl_dict, feature_map, feature_weights, max_features
                    )
                    names.append(name)
                    valid_count += 1
            except:
                continue

        if valid_count > 0:
            X = X[:valid_count]
            if use_pca:
                X = pca.transform(X)
            cluster_labels = kmeans.predict(X)
            for name, cluster_id in zip(names, cluster_labels):
                cur.execute(
                    f"""
                    UPDATE {table_name}
                    SET cluster_id = %s
                    WHERE theorem_name = %s
                """,
                    (int(cluster_id), name),
                )
            conn.commit()

        offset += batch_size

    cur.execute(
        f"""
        SELECT cluster_id, COUNT(*)
        FROM {table_name}
        GROUP BY cluster_id
        ORDER BY cluster_id
    """
    )
    for cluster_id, count in cur.fetchall():
        print(f"cluster {cluster_id}：{count}")
        logging.info(f"cluster {cluster_id}：{count}")

    cur.close()
    conn.close()
    print("Clustering completed")
    logging.info("Clustering completed")


if __name__ == "__main__":
    cluster_wl_encodings(
        n_clusters=10000,
        batch_size=10000,
        max_features=8000,
        use_pca=True,
        pca_components=1200,
    )
