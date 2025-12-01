import argparse
import sys
from pathlib import Path

from .generators import generate_tfvars, generate_env
from .errors import CellSpecError
from .parser import parse_cell_spec


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate .tfvars and .env from a Cell spec markdown file"
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path to cell spec markdown file",
        default="examples/cell-spec.md",
    )

    parser.add_argument(
        "--out-prefix",
        "-o",
        type=str,
        help="Output file prefix, for example 'examples/icc-01'",
        default="examples/icc-01",
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    spec_path = Path(args.input)
    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    try:
        cell = parse_cell_spec(spec_path)
    except CellSpecError as exc:
        print(f"[cell-spec-cli] Spec error in {spec_path}: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        # Catch any unexpected bugs so the user sees a clean message
        print(f"[cell-spec-cli] Unexpected error: {exc}", file=sys.stderr)
        sys.exit(2)

    tfvars_content = generate_tfvars(cell)
    env_content = generate_env(cell)

    tfvars_path = out_prefix.with_suffix(".tfvars")
    env_path = out_prefix.with_suffix(".env")

    try:
        tfvars_path.write_text(tfvars_content, encoding="utf8")
        env_path.write_text(env_content, encoding="utf8")
    except OSError as exc:
        print(f"[cell-spec-cli] Failed to write output files: {exc}", file=sys.stderr)
        sys.exit(3)

    print(f"Generated {tfvars_path}")
    print(f"Generated {env_path}")


if __name__ == "__main__":
    main()
