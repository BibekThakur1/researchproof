from pathlib import Path

from researchproof.ast_baseline import evaluate_ast_baseline
from researchproof.source_benchmark import write_source_benchmark
from researchproof.static_analysis import evaluate_symbolic_analyzer


def main() -> None:
    root = Path("artifacts/source_pilot_v0_1")
    index = write_source_benchmark(root / "cases.jsonl")
    report = evaluate_ast_baseline(index, root / "ast_baseline.json")
    symbolic = evaluate_symbolic_analyzer(index, root / "symbolic_baseline.json")
    print(f"Source cases written to {index}")
    print(f"AST baseline written to {report}")
    print(f"Symbolic baseline written to {symbolic}")


if __name__ == "__main__":
    main()
