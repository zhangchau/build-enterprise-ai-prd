#!/usr/bin/env python3
"""List or extract H1 chapters from a large AI PRD without loading the full file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def h1_sections(text: str) -> list[tuple[str, int, int, str]]:
    """Return (key, start_line, end_line, heading) for H1 sections outside fences."""
    lines = text.splitlines(keepends=True)
    positions: list[tuple[str, int, str]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if re.match(r"^```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^# (.+?)\s*$", line)
        if not match:
            continue
        heading = match.group(1)
        number = re.match(r"^(\d+)\.", heading)
        if number:
            key = number.group(1)
        elif heading.strip() == "附录":
            key = "appendix"
        else:
            key = "title"
        positions.append((key, index, heading))

    result: list[tuple[str, int, int, str]] = []
    for pos, (key, start, heading) in enumerate(positions):
        end = positions[pos + 1][1] if pos + 1 < len(positions) else len(lines)
        result.append((key, start, end, heading))
    return result


def parse_requested(values: list[str]) -> list[str]:
    keys: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip().lower()
            if not item:
                continue
            range_match = re.fullmatch(r"(\d+)-(\d+)", item)
            if range_match:
                start, end = map(int, range_match.groups())
                if start > end:
                    start, end = end, start
                keys.extend(str(number) for number in range(start, end + 1))
            else:
                keys.append(item)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(keys))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="列出或提取完整 PRD 的 H1 章节，支持 --section 9-12 或多次指定。"
    )
    parser.add_argument("file", help="Markdown 文档")
    parser.add_argument("--list", action="store_true", help="只列出章节")
    parser.add_argument(
        "--section",
        action="append",
        default=[],
        help="章节号、范围、title 或 appendix；例如 9-12，可重复",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"错误：文件不存在：{path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    sections = h1_sections(text)

    if args.list or not args.section:
        for key, start, end, heading in sections:
            print(f"{key:>8}  L{start + 1}-L{end}  {heading}")
        return 0

    requested = parse_requested(args.section)
    available = {key for key, *_ in sections}
    missing = [key for key in requested if key not in available]
    if missing:
        print(f"错误：找不到章节：{', '.join(missing)}", file=sys.stderr)
        return 3

    chunks: list[str] = []
    for key in requested:
        for section_key, start, end, _ in sections:
            if section_key == key:
                chunks.append("".join(lines[start:end]).rstrip() + "\n")
                break
    sys.stdout.write("\n---\n\n".join(chunks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
