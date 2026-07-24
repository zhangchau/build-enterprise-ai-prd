#!/usr/bin/env python3
"""Deterministic structural and coverage checks for a long enterprise AI PRD."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    level: str
    code: str
    message: str
    line: int | None = None


def outside_fence_lines(lines: list[str]) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if re.match(r"^```", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append((number, line))
    return result


def h1_sections(text: str) -> dict[str, tuple[int, int, str]]:
    lines = text.splitlines()
    visible = outside_fence_lines(lines)
    positions: list[tuple[str, int, str]] = []
    for number, line in visible:
        match = re.match(r"^# (.+?)\s*$", line)
        if not match:
            continue
        heading = match.group(1)
        chapter = re.match(r"^(\d+)\.", heading)
        if chapter:
            key = chapter.group(1)
        elif heading.strip() == "附录":
            key = "appendix"
        else:
            key = "title"
        positions.append((key, number - 1, heading))
    sections: dict[str, tuple[int, int, str]] = {}
    for index, (key, start, heading) in enumerate(positions):
        end = positions[index + 1][1] if index + 1 < len(positions) else len(lines)
        if key not in sections:
            sections[key] = (start, end, heading)
    return sections


def meaningful_length(value: str) -> int:
    value = re.sub(r"```[\s\S]*?```", "", value)
    value = re.sub(r"!\?\[\[[^\]]+\]\]|\[\[[^\]]+\]\]", "", value)
    value = re.sub(r"https?://\S+", "", value)
    value = re.sub(r"[#>*_`|:\-\[\](){}0-9\s]", "", value)
    return len(value)


def section_text(lines: list[str], section: tuple[int, int, str]) -> str:
    start, end, _ = section
    return "\n".join(lines[start:end])


def has_na_reason(text: str) -> bool:
    return bool(re.search(r"(?:N/A|不适用)[\s\S]{0,160}(?:原因|因为|替代|当前未使用)", text, re.I))


def add_coverage_checks(
    issues: list[Issue], sections: dict[str, tuple[int, int, str]], lines: list[str]
) -> None:
    checks: dict[str, tuple[str, list[tuple[str, str]]]] = {
        "7": (
            "功能级 PRD",
            [
                ("触发", r"触发"),
                ("输入", r"输入"),
                ("状态", r"状态"),
                ("权限", r"权限"),
                ("异常/降级", r"异常|降级"),
                ("验收", r"验收"),
            ],
        ),
        "9": (
            "数据/RAG",
            [
                ("知识源", r"知识源|数据源"),
                ("清洗/结构", r"清洗|结构化"),
                ("切片", r"切片|Chunk"),
                ("Embedding", r"Embedding|嵌入"),
                ("Metadata", r"metadata|元数据"),
                ("Rerank", r"Rerank|重排"),
                ("评测", r"评测"),
            ],
        ),
        "13": (
            "异常与边界",
            [
                ("输入异常", r"输入异常"),
                ("模型异常", r"模型异常"),
                ("知识异常", r"知识异常"),
                ("工具/接口", r"工具|接口"),
                ("权限", r"权限"),
                ("Corner Case", r"Corner\s*Case|边界案例"),
            ],
        ),
        "14": (
            "降级/人工/恢复",
            [
                ("降级", r"降级"),
                ("人工", r"人工"),
                ("接手包", r"接手包|上下文包"),
                ("对账", r"对账"),
                ("恢复", r"恢复"),
                ("熔断/限流", r"熔断|限流"),
            ],
        ),
        "16": (
            "评测 Gate",
            [
                ("评测集", r"评测集"),
                ("数据来源/分布", r"数据来源|样本来源|分布"),
                ("Gold", r"Gold|标准答案"),
                ("离线", r"离线"),
                ("端到端", r"端到端"),
                ("红队/安全", r"红队|安全"),
                ("成本/容量", r"成本|容量"),
                ("Gate", r"\bGate\b|Go\s*/\s*No-Go"),
            ],
        ),
        "18": (
            "Bad Case",
            [
                ("止损", r"止损"),
                ("根因", r"根因"),
                ("影响范围", r"影响范围"),
                ("回归", r"回归"),
                ("关闭", r"关闭"),
            ],
        ),
        "19": (
            "上线运营",
            [
                ("监控", r"监控"),
                ("知识运营", r"知识运营"),
                ("发布", r"发布"),
                ("回滚", r"回滚"),
                ("Runbook", r"Runbook|运行手册"),
                ("对账/恢复", r"对账|恢复"),
            ],
        ),
    }
    for chapter, (label, required) in checks.items():
        if chapter not in sections:
            continue
        text = section_text(lines, sections[chapter])
        if has_na_reason(text):
            continue
        missing = [name for name, pattern in required if not re.search(pattern, text, re.I)]
        if missing:
            issues.append(
                Issue(
                    "WARN",
                    f"COVERAGE-{chapter}",
                    f"第 {chapter} 章（{label}）可能缺少：{', '.join(missing)}",
                    sections[chapter][0] + 1,
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检查企业级 AI PRD 的结构、占位符、教学提醒和关键章节覆盖。"
    )
    parser.add_argument("file", help="要验证的 Markdown 文档")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="存在 WARN 时也返回非零，用于最终发布 Gate",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR FILE：文件不存在：{path}")
        return 2

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[Issue] = []

    # Frontmatter
    if not lines or lines[0].strip() != "---":
        issues.append(Issue("ERROR", "FRONTMATTER", "缺少 YAML frontmatter"))
    else:
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
            frontmatter = "\n".join(lines[1:end])
            if not re.search(r"^title\s*:", frontmatter, re.M):
                issues.append(Issue("ERROR", "FRONTMATTER-TITLE", "frontmatter 缺少 title"))
        except StopIteration:
            issues.append(Issue("ERROR", "FRONTMATTER-CLOSE", "YAML frontmatter 未闭合"))

    # Fences
    fence_lines = [index for index, line in enumerate(lines, start=1) if re.match(r"^```", line)]
    if len(fence_lines) % 2:
        issues.append(
            Issue("ERROR", "FENCE", f"代码围栏数量为奇数：{len(fence_lines)}", fence_lines[-1])
        )

    # Heading hierarchy outside fences.
    visible = outside_fence_lines(lines)
    previous_level: int | None = None
    for number, line in visible:
        match = re.match(r"^(#{1,6})\s+", line)
        if not match:
            continue
        level = len(match.group(1))
        if previous_level is not None and level > previous_level + 1:
            issues.append(
                Issue(
                    "ERROR",
                    "HEADING-JUMP",
                    f"标题层级从 H{previous_level} 跳到 H{level}",
                    number,
                )
            )
        previous_level = level

    sections = h1_sections(text)
    required = [str(number) for number in range(23)] + ["appendix"]
    missing = [key for key in required if key not in sections]
    if missing:
        issues.append(Issue("ERROR", "CHAPTERS", f"缺少一级章节：{', '.join(missing)}"))

    # Duplicate numbered H1 chapters.
    chapter_hits: dict[str, list[int]] = {}
    for number, line in visible:
        match = re.match(r"^# (\d+)\.", line)
        if match:
            chapter_hits.setdefault(match.group(1), []).append(number)
    for chapter, hits in chapter_hits.items():
        if len(hits) > 1:
            issues.append(
                Issue("ERROR", "DUPLICATE-CHAPTER", f"第 {chapter} 章出现多次：{hits}", hits[1])
            )

    # Chapter substance.
    for chapter in [str(number) for number in range(23)]:
        if chapter not in sections:
            continue
        body = section_text(lines, sections[chapter])
        if meaningful_length(body) < 120 and not has_na_reason(body):
            issues.append(
                Issue(
                    "WARN",
                    "THIN-CHAPTER",
                    f"第 {chapter} 章内容过薄，可能仍是目录或套话",
                    sections[chapter][0] + 1,
                )
            )

    # Unresolved placeholders.
    placeholders = list(
        re.finditer(
            r"【(?:目标用户|核心场景|产品/AI 能力|关键问题|可衡量价值|"
            r"业务系统|草稿生成角色|项目名称|待[^】\n]*|请填写|X{2,})】"
            r"|《项目名称》|\bTODO\b|待填写",
            text,
        )
    )
    if placeholders:
        first_line = text[: placeholders[0].start()].count("\n") + 1
        issues.append(
            Issue(
                "WARN",
                "PLACEHOLDER",
                f"发现 {len(placeholders)} 个明显占位符；最终版需填写、删除或标明待验证",
                first_line,
            )
        )

    # Mandatory teaching/interaction notices.
    notices = [
        ("HAND-DRAW", r"手画|亲手画", "缺少学员本人手画流程/架构的提醒"),
        (
            "NO-AI-DRAW",
            r"(?:不要|禁止)[^\n]{0,30}AI[^\n]{0,30}(?:代画|生成最终|最终图)",
            "缺少“不要让 AI 代画最终流程/架构”的提醒",
        ),
        (
            "NO-PROTOTYPE",
            r"暂不提供[^\n]{0,30}(?:图片|原型)",
            "无原型时缺少“暂不提供图片/原型”的明确说明",
        ),
        (
            "REAL-PROTOTYPE",
            r"企业(?:真实)?落地[^\n]{0,60}(?:可点击)?原型",
            "缺少企业落地必须补原型与交互验收的说明",
        ),
        (
            "FACT-LABEL",
            r"已确认事实[\s\S]{0,200}待验证假设",
            "缺少事实与假设的显式区分",
        ),
    ]
    for code, pattern, message in notices:
        if not re.search(pattern, text, re.I):
            issues.append(Issue("WARN", code, message))

    # Diagrams.
    mermaid_count = len(re.findall(r"```mermaid\s*\n", text))
    if mermaid_count < 4:
        issues.append(
            Issue(
                "WARN",
                "DIAGRAMS",
                f"仅发现 {mermaid_count} 张 Mermaid 图；完整文档通常需展示业务、AI/系统、异常/恢复和治理链路",
            )
        )

    add_coverage_checks(issues, sections, lines)

    # Numbers that deserve evidence review. INFO does not fail strict mode.
    numeric_claims: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        if not re.search(r"\d+(?:\.\d+)?%|(?:提升|降低|节省|缩短)[^\n]{0,15}\d", line):
            continue
        if re.search(r"示例|目标|假设|待测|待验证|来源|基线|公式|阈值依据", line):
            continue
        numeric_claims.append((number, line.strip()))
    if numeric_claims:
        sample = ", ".join(f"L{number}" for number, _ in numeric_claims[:8])
        issues.append(
            Issue(
                "INFO",
                "NUMERIC-EVIDENCE",
                f"发现 {len(numeric_claims)} 条数字结果可能需要核对口径/来源：{sample}",
            )
        )

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    issues.sort(key=lambda issue: (order[issue.level], issue.line or 0, issue.code))
    for issue in issues:
        location = f" L{issue.line}" if issue.line else ""
        print(f"{issue.level} {issue.code}{location}: {issue.message}")

    error_count = sum(issue.level == "ERROR" for issue in issues)
    warning_count = sum(issue.level == "WARN" for issue in issues)
    info_count = sum(issue.level == "INFO" for issue in issues)
    print(
        f"\nSUMMARY file={path} lines={len(lines)} mermaid={mermaid_count} "
        f"errors={error_count} warnings={warning_count} info={info_count}"
    )

    if error_count:
        return 1
    if args.strict and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
