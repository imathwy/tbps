import json
import psycopg2
from process_single import process_single_prop
from myexpr import deserialize_expr
from WL.db_utils import DB_CONFIG
from cse import cse


def load_apply_steps_from_pgsql_minimal(db_config: dict):
    """
    Loads apply steps data directly from a PostgreSQL database,
    including relevant columns and parsing the main_goal_type_json column.
    This version further optimizes memory by not extracting command_syntax_kind.

    Args:
        db_config: A dictionary containing the PostgreSQL connection parameters
                   (host, port, database, user, password).

    Returns:
        A list of tuples, where each tuple contains:
        (app_fn_name: str, main_goal_type_expr: object, main_goal_type_str: str)
        main_goal_type_expr is the parsed Python object from main_goal_type_json.
    """
    data_rows = []
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()

        query = """
            SELECT
                id,
                data ->> 'appFnName',
                REPLACE(data ->> 'exactStxReprint', E'\\n', ' '),
                REPLACE(data ->> 'mainGoalTypeStr', E'\\n', ' '),
                REPLACE(data ->> 'mainGoalTypeJson', E'\\n', ' ')
                -- data ->> 'commandSyntaxKind'
            FROM tactic_step
            WHERE data ->> 'commandSyntaxKind' = 'Lean.Parser.Command.theorem'
            ORDER BY id;
        """
        cur.execute(query)
        results = cur.fetchall()

        for row in results:
            app_fn_name = row[1].strip()
            main_goal_type_str = row[3].strip()
            main_goal_type_json_str = row[4].strip()

            type_expr = None
            type_expr = json.loads(main_goal_type_json_str)
            data_rows.append((app_fn_name, type_expr, main_goal_type_str))

        cur.close()

    except psycopg2.Error as e:
        print(
            f"An error occurred while connecting to or querying the PostgreSQL database: {e}"
        )
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection is closed.")

    return data_rows


if __name__ == "__main__":

    steps = load_apply_steps_from_pgsql_minimal(DB_CONFIG)
    print(f"Retrieved {len(steps)} records from PostgreSQL.")
    props = []
    for name, exprjson, main_goal_type_str in steps:
        original_expr = deserialize_expr(exprjson)
        cse_expr = cse(original_expr)
        props.append((name, cse_expr, main_goal_type_str))

    output_file = f"similarity_results_propB_final.csv"
    for i, (target_name, target_expr, main_goal_type_str) in enumerate(props):
        print(f"Processing proposition {i+1}/{len(props)}: '{target_name}'")
        print(main_goal_type_str)
        target_rank = process_single_prop(target_name, target_expr, output_file)
        print("-" * 50)
