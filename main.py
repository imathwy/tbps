import subprocess
import json
import os
from process_single import process_single_prop
from myexpr import deserialize_expr
from cse import cse
# forall (a b : Nat), a + b = b + a
# pg_ctl -D /Users/princhern/Documents/structure_search/mathlib4_data start
PROJECT_ROOT = r"/Users/princhern/Documents/structure_search/TreeSelect/Lean_tool"
INPUT_TXT = os.path.join(PROJECT_ROOT, "input_expr.txt")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "expr_output.json")

def run_lean(input_str: str):
    with open(INPUT_TXT, "w", encoding="utf-8") as f:
        f.write(input_str.strip())

    result = subprocess.run(
        ["lake", "exe","Mathlib_Construction"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        print("Lean 执行失败:")
        print(result.stderr)
        return None

    if not os.path.exists(OUTPUT_JSON):
        raise FileNotFoundError(f"{OUTPUT_JSON} 未生成！")

    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        name = data["input_str"].strip()
        statement_str = data["expr_dbg"].strip()
        expr_json = data["your_expr"]
    return [(name, expr_json, statement_str)]


if __name__ == "__main__":
    input_expr = input("Enter a Lean expression to parse: ").strip()
    if not input_expr:
        print("No input provided. Exiting.")
        exit(1)

    steps = run_lean(input_expr)

    props = []
    for name, exprjson, main_goal_type_str in steps: # type: ignore
        original_expr = deserialize_expr(exprjson)
        cse_expr = cse(original_expr)
        props.append((name, cse_expr, main_goal_type_str))

    output_file = "similarity_results_propB_final.csv"
    for i, (target_name, target_expr, main_goal_type_str) in enumerate(props):
        print(f"Processing proposition {i+1}/{len(props)}: '{target_name}'")
        print(main_goal_type_str)
        target_rank = process_single_prop(target_name, target_expr, output_file)
        print("-" * 50)