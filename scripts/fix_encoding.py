"""Normalize Python files to UTF-8 encoding with Unix line endings."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence, Tuple


DEFAULT_TARGETS = [Path("memex_next")]


def detect_text(raw: bytes, encodings: Sequence[str]) -> Tuple[str, str]:
    """Return the first successful decoding of the raw bytes."""

    for encoding in encodings:
        try:
            return encoding, raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", raw, 0, 1, "none of the candidate encodings succeeded")


def process_file(path: Path, candidates: Sequence[str], dry_run: bool) -> str | None:
    raw = path.read_bytes()
    detected, text = detect_text(raw, candidates)
    if detected == "utf-8" and "\r" not in text:
        return None
    if dry_run:
        return detected
    path.write_text(text, encoding="utf-8", newline="\n")
    return detected


def gather_files(dirs: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for directory in dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.py")):
            if path in seen:
                continue
            seen.add(path)
            yield path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix Python file encodings to UTF-8.")
    parser.add_argument(
        "targets",
        nargs="*",
        type=Path,
        default=DEFAULT_TARGETS,
        help="Paths or directories to scan (defaults to memex_next/).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show which files need rewriting.")
    parser.add_argument("--encoding", default="cp1252", help="Fall-back encoding to try after UTF-8.")
    args = parser.parse_args(argv)

    candidates = ["utf-8", args.encoding]
    rewritten = 0
    skipped = 0
    for path in gather_files(args.targets):
        try:
            detected = process_file(path, candidates, dry_run=args.dry_run)
        except UnicodeDecodeError as exc:
            print(f"[error] {path}: could not decode ({exc})", file=sys.stderr)
            continue
        if detected is None:
            skipped += 1
            continue
        rewritten += 1
        action = "(dry-run)" if args.dry_run else "rewritten"
        print(f"{path}: detected {detected} -> utf-8 {action}")

    if args.dry_run:
        print(f"Dry run: {rewritten} file(s) would be rewritten, {skipped} already UTF-8.")
    else:
        print(f"Rewritten {rewritten} file(s); {skipped} already UTF-8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
