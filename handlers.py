import subprocess
import json
import os
import random
import asyncio
from base_server import TheoremHandler, TheoremResult
from process_single import process_single_prop_new
from myexpr import deserialize_expr  # pyright: ignore[reportUnknownVariableType]
from cse import cse
from WL.db_utils import connect_to_db  # pyright: ignore[reportPrivateLocalImportUsage, reportUnknownVariableType]

class ProductionHandler:
    """Production handler that uses real Lean parsing and database queries."""

    def __init__(self):
        self.PROJECT_ROOT = r"/Users/princhern/Documents/structure_search/TreeSelect/Lean_tool"
        self.INPUT_TXT = os.path.join(self.PROJECT_ROOT, "input_expr.txt")
        self.OUTPUT_JSON = os.path.join(self.PROJECT_ROOT, "expr_output.json")
        self.version = "1.0.0"

    def _run_lean(self, input_str: str) -> tuple[str, str, str]:
        """Parse Lean expression using the Lean tool."""
        try:
            with open(self.INPUT_TXT, "w", encoding="utf-8") as f:
                f.write(input_str.strip())

            result = subprocess.run(
                ["lake", "exe", "Mathlib_Construction"],
                cwd=self.PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"Lean execution failed: {result.stderr}")

            if not os.path.exists(self.OUTPUT_JSON):
                raise Exception(f"{self.OUTPUT_JSON} not generated")

            with open(self.OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                name: str = data["input_str"].strip()
                statement_str: str = data["expr_dbg"].strip()
                expr_json = data["your_expr"]

            return name, expr_json, statement_str

        except subprocess.TimeoutExpired:
            raise Exception("Lean parsing timed out after 30 seconds")
        except Exception as e:
            raise Exception(f"Lean parsing error: {str(e)}")

    async def find_similar_theorems(
        self,
        expression: str,
        k: int,
        node_ratio: float | None = None
    ) -> tuple[list[TheoremResult], str]:
        """Find similar theorems using real computation."""
        # Parse the Lean expression
        name, expr_json, statement_str = self._run_lean(expression)

        # Deserialize and apply CSE transformation
        original_expr = deserialize_expr(expr_json)
        cse_expr = cse(original_expr)

        # Find similar theorems
        results = process_single_prop_new(cse_expr, k)

        # Format results
        theorem_results = []
        for theorem_name, similarity, statement, node_count in results:
            theorem_results.append(TheoremResult(
                name=theorem_name,
                similarity_score=round(similarity, 4),
                statement=statement,
                node_count=node_count
            ))

        return theorem_results, statement_str

    async def check_health(self) -> tuple[bool, bool, str]:
        """Check database and Lean availability."""
        database_connected = False
        lean_available = False

        # Check database connection
        try:
            conn = connect_to_db()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            conn.close()
            database_connected = True
        except Exception:
            database_connected = False

        # Check if Lean is available
        try:
            result = subprocess.run(
                ["lake", "--version"],
                cwd=self.PROJECT_ROOT if os.path.exists(self.PROJECT_ROOT) else ".",
                capture_output=True,
                text=True,
                timeout=5
            )
            lean_available = result.returncode == 0
        except Exception:
            lean_available = False

        return database_connected, lean_available, self.version


class MockHandler:
    """Mock handler that returns simulated data without external dependencies."""

    def __init__(self):
        self.version = "1.0.0-test"
        self.mock_theorem_names = [
            "Nat.add_comm", "Nat.mul_comm", "Nat.add_assoc", "Nat.mul_assoc",
            "List.length_append", "List.reverse_reverse", "Set.union_comm", "Set.inter_comm",
            "Function.comp_assoc", "Finset.card_union", "Real.add_comm", "Real.mul_comm",
            "Int.add_comm", "Int.mul_comm", "Vector.append_cons", "Matrix.mul_assoc",
            "Group.mul_assoc", "Ring.add_comm", "Field.mul_inv_cancel", "Topology.isOpen_compl_iff",
            "MeasureTheory.measure_union", "Probability.indep_comm", "DifferentialGeometry.contDiff_add",
            "LinearAlgebra.span_union", "CategoryTheory.comp_assoc", "Prop.and_comm",
            "Prop.or_comm", "Classical.not_not", "Set.subset_union_left", "Fintype.card_le_of_injective"
        ]

        self.mock_statements = [
            "∀ (a b : Nat), a + b = b + a",
            "∀ (a b : Nat), a * b = b * a",
            "∀ (a b c : Nat), (a + b) + c = a + (b + c)",
            "∀ (l₁ l₂ : List α), List.length (l₁ ++ l₂) = List.length l₁ + List.length l₂",
            "∀ (A B : Set α), A ∪ B = B ∪ A",
            "∀ (f g h : α → β → γ), (f ∘ g) ∘ h = f ∘ (g ∘ h)",
            "∀ (s t : Finset α), s.card + t.card = (s ∪ t).card + (s ∩ t).card",
            "∀ (x y : ℝ), x + y = y + x",
            "∀ (G : Type) [Group G] (a b c : G), (a * b) * c = a * (b * c)",
            "∀ (R : Type) [Ring R] (a b : R), a + b = b + a",
            "∀ (l : List α), List.reverse (List.reverse l) = l",
            "∀ (A B : Set α), A ∩ B = B ∩ A",
            "∀ (p q : Prop), p ∧ q ↔ q ∧ p",
            "∀ (p q : Prop), p ∨ q ↔ q ∨ p",
            "∀ (p : Prop), ¬¬p ↔ p"
        ]

    def _generate_mock_results(self, expression: str, k: int) -> list[TheoremResult]:
        """Generate mock theorem results with realistic similarity scores."""
        results = []

        # Use expression hash to get consistent results for same input
        seed = hash(expression) % 1000
        random.seed(seed)

        # Generate k results
        num_results = min(k, len(self.mock_theorem_names))
        selected_names = random.sample(self.mock_theorem_names, num_results)
        selected_statements = random.sample(
            self.mock_statements,
            min(len(self.mock_statements), num_results)
        )

        for i, name in enumerate(selected_names):
            # Generate decreasing similarity scores with some randomness
            base_score = 0.95 - (i * 0.08) + random.uniform(-0.05, 0.05)
            base_score = max(0.1, min(0.99, base_score))  # Keep in reasonable range

            statement = selected_statements[i % len(selected_statements)]
            node_count = random.randint(10, 150)

            results.append(TheoremResult(
                name=name,
                similarity_score=round(base_score, 4),
                statement=statement,
                node_count=node_count
            ))

        # Sort by similarity score descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results

    async def find_similar_theorems(
        self,
        expression: str,
        k: int,
        node_ratio: float | None = None
    ) -> tuple[list[TheoremResult], str]:
        """Generate mock similar theorems."""
        # Validate input
        if not expression.strip():
            raise ValueError("Expression cannot be empty")

        if len(expression) > 1000:
            raise ValueError("Expression too long (max 1000 characters)")

        # Simulate processing time (1-3 seconds)
        processing_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(processing_time)

        # Generate mock results
        results = self._generate_mock_results(expression, k)

        # Mock parsed expression
        mock_parsed = f"parsed: {expression[:50]}{'...' if len(expression) > 50 else ''}"

        return results, mock_parsed

    async def check_health(self) -> tuple[bool, bool, str]:
        """Return mock health status with occasional issues for testing."""
        # Simulate occasional service issues for testing
        db_status = random.random() > 0.05  # 95% uptime
        lean_status = random.random() > 0.02  # 98% uptime

        return db_status, lean_status, self.version
