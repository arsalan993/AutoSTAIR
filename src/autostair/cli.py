from __future__ import annotations

import argparse
import json

from .build import build_indexes
from .config import load_settings
from .evaluation import run_evaluation
from .generation import AnswerGenerator
from .judging import create_blinded_file
from .retrieval import Retriever, format_evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoSTAIR RAG benchmark")
    parser.add_argument("--config", default="configs/default.yaml")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("build", help="Extract the PDF and build FAISS indexes")
    query = commands.add_parser("query", help="Compare both retrievers for one question")
    query.add_argument("question")
    query.add_argument("--generate", action="store_true")

    evaluate = commands.add_parser("evaluate", help="Run the fixed question set")
    evaluate.add_argument("--generate", action="store_true")
    evaluate.add_argument(
        "--resume",
        action="store_true",
        help="Reuse completed question-method rows and continue missing work",
    )

    blind = commands.add_parser("blind", help="Create a randomized answer-judging file")
    blind.add_argument("--input", default="artifacts/results/evaluation.jsonl")
    blind.add_argument("--output", default="artifacts/results/blinded.jsonl")
    blind.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = _parser().parse_args()
    settings = load_settings(args.config)
    if args.command == "build":
        print(json.dumps(build_indexes(settings), indent=2))
        return
    if args.command == "query":
        retriever = Retriever(settings)
        generator = AnswerGenerator(settings) if args.generate else None
        for method, hits in (
            ("flat", retriever.flat(args.question)),
            ("structured", retriever.structured(args.question)),
        ):
            evidence = format_evidence(hits, int(settings.retrieval["evidence_token_budget"]))
            print(f"\n## {method}\n\n{evidence}")
            if generator:
                answer, usage = generator.answer(args.question, evidence)
                print(f"\nAnswer: {answer}\nUsage: {usage}")
        return
    if args.command == "evaluate":
        print(
            run_evaluation(
                settings,
                generate_answers=args.generate,
                resume=args.resume,
            )
        )
        return
    if args.command == "blind":
        create_blinded_file(args.input, args.output, args.seed)
        print(args.output)


if __name__ == "__main__":
    main()
