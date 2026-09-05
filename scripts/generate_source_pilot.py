from pathlib import Path

from researchproof.ast_baseline import evaluate_ast_baseline
from researchproof.source_benchmark import write_source_benchmark


def main() -> None:
    root = Path("artifacts/source_pilot_v0_1")
    index = write_source_benchmark(root / "cases.jsonl")
    report = evaluate_ast_baseline(index, root / "ast_baseline.json")
    print(f"Source cases written to {index}")
    print(f"AST baseline written to {report}")


if __name__ == "__main__":
    main()

