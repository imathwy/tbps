# db_utils.py
import psycopg2
import json

# PostgreSQL 配置信息
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "user": "princhern"
}


def connect_to_db(config=DB_CONFIG):
    try:
        conn = psycopg2.connect(**config)
        print("Successfully connected to the database")
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None


def fetch_theorems_batch(conn, table_name, offset, batch_size):
    try:
        cur = conn.cursor()
        query = f"""
            SELECT name, expr_cse_json 
            FROM {table_name} 
            WHERE expr_cse_json != 'null' 
            ORDER BY name 
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (batch_size, offset))
        theorems = cur.fetchall()
        cur.close()
        return theorems
    except Exception as e:
        print(f"Batch extraction theorem failed (offset {offset}): {e}")
        return []


def create_wl_table(conn):
    """创建存储WL编码的表"""
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS wl_encodings (
                theorem_name VARCHAR PRIMARY KEY,
                wl_encoding JSONB,
                tree_depth INTEGER
            )
        """
        )
        conn.commit()
        print("Successfully created the wl_encodings table")
        cur.close()
    except Exception as e:
        print(f"Create table failed: {e}")


def store_wl_encoding(conn, theorem_name, wl_encoding, tree_depth):
    try:
        cur = conn.cursor()
        serialized_encoding = json.dumps(wl_encoding)
        cur.execute(
            """
            INSERT INTO wl_encodings (theorem_name, wl_encoding, tree_depth)
            VALUES (%s, %s, %s)
            ON CONFLICT (theorem_name) DO UPDATE SET wl_encoding = %s, tree_depth = %s
        """,
            (
                theorem_name,
                serialized_encoding,
                tree_depth,
                serialized_encoding,
                tree_depth,
            ),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"WL encoding of storage theorem {theorem_name} failed: {e}")
