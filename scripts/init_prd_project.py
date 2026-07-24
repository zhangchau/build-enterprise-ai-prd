#!/usr/bin/env python3
"""Scaffold a file-first enterprise AI PRD project without overwriting data."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "assets" / "ai-prd-master-template.md"


def safe_name(value: str) -> str:
    value = value.strip()
    value = re.sub(r'[<>:"/\\\\|?*\\x00-\\x1f]', "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._")
    if not value:
        raise ValueError("项目名称不能在清理后为空")
    return value[:100]


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"拒绝覆盖已有文件：{path}")
    path.write_text(content, encoding="utf-8")


def render_document(template: str, project_name: str, project_type: str, today: str) -> str:
    text = template
    text = re.sub(
        r"^title:.*$",
        lambda _: "title: "
        + json.dumps(
            f"{project_name} AI产品PRD、方案决策与项目答辩文档",
            ensure_ascii=False,
        ),
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^status:.*$", "status: 初始骨架", text, count=1, flags=re.MULTILINE)
    type_labels = {
        "real": "AI产品PRD",
        "course": "AI产品经理课程项目",
        "simulation": "AI产品经理模拟项目",
        "unspecified": "AI产品PRD",
    }
    text = re.sub(
        r"^type:.*$",
        lambda _: f"type: {type_labels[project_type]}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(r"^created:.*$", f"created: {today}", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^updated:.*$", f"updated: {today}", text, count=1, flags=re.MULTILINE)
    text = text.replace("# 《项目名称》AI 产品 PRD、方案决策与项目答辩文档",
                        f"# 《{project_name}》AI 产品 PRD、方案决策与项目答辩文档",
                        1)
    return text


def build_state(project_name: str, project_type: str, mode: str, output: Path) -> dict:
    batches = [
        ("B0", "0—1", "文档契约与一页纸"),
        ("B1", "2—5", "业务、用户、AI必要性、目标与MVP"),
        ("B2", "6—8", "体验、功能PRD与AI任务"),
        ("B3", "9—12", "数据/RAG、模型、Prompt/Agent与系统"),
        ("B4", "13—16", "异常、降级、安全与评测"),
        ("B5", "17—19", "归因、Bad Case与运营"),
        ("B6", "20—22+附录", "计划、决策与面试答辩"),
    ]
    return {
        "schema_version": 1,
        "skill": "build-enterprise-ai-prd",
        "project_name": project_name,
        "project_type": project_type,
        "mode": mode,
        "output_file": str(output),
        "current_gate": "Gate 0",
        "current_batch": "B0",
        "batches": [
            {"id": bid, "chapters": chapters, "purpose": purpose, "status": "pending"}
            for bid, chapters, purpose in batches
        ],
        "frozen_decisions": [],
        "open_questions": [],
        "global_conflicts": [],
        "last_updated": date.today().isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="创建企业级 AI PRD 骨架和外部记忆工作区；默认不覆盖任何已有文件。"
    )
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--output-dir", default=".", help="输出目录，默认当前目录")
    parser.add_argument("--filename", help="最终 Markdown 文件名；默认由项目名生成")
    parser.add_argument(
        "--mode",
        choices=["guided", "autopilot", "audit", "pack-only"],
        default="guided",
        help="生产模式，默认 guided",
    )
    parser.add_argument(
        "--project-type",
        choices=["real", "course", "simulation", "unspecified"],
        default="unspecified",
        help="项目性质",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="已有资料路径，可重复传入",
    )
    args = parser.parse_args()

    if not TEMPLATE.exists():
        print(f"错误：找不到母版 {TEMPLATE}", file=sys.stderr)
        return 2

    project_name = re.sub(r"\s+", " ", args.project_name).strip()
    try:
        stem = safe_name(project_name)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or f"{stem}_AI产品PRD方案决策与项目答辩文档.md"
    if Path(filename).name != filename:
        print("错误：--filename 只能是文件名，不能包含目录；请用 --output-dir 指定目录。", file=sys.stderr)
        return 2
    if not filename.lower().endswith(".md"):
        filename += ".md"
    final_path = output_dir / filename
    work_dir = output_dir / f".{stem}_ai_prd_work"

    conflicts = [p for p in (final_path, work_dir) if p.exists()]
    if conflicts:
        print("错误：为保护已有内容，拒绝覆盖：", file=sys.stderr)
        for path in conflicts:
            print(f"  - {path}", file=sys.stderr)
        print("请改用 audit 模式处理已有文档，或选择新的输出路径。", file=sys.stderr)
        return 3

    work_dir.mkdir(parents=False)
    try:
        today = date.today().isoformat()
        template_text = TEMPLATE.read_text(encoding="utf-8")
        write_new(
            final_path,
            render_document(template_text, project_name, args.project_type, today),
        )

        write_new(
            work_dir / "project-brief.md",
            f"""# Project Brief

| 字段 | 内容 |
| --- | --- |
| 项目名称 | {project_name} |
| 项目性质 | {args.project_type} |
| 当前阶段 | 待确认 |
| 核心用户 | 待确认 |
| 一期场景/用户任务 | 待确认 |
| 现状流程与损失 | 待确认 |
| AI 增量价值 | 待确认 |
| 一期非目标 | 待确认 |
| 高风险错误 | 待确认 |
| 读者/用途 | 待确认 |
| 生产模式 | {args.mode} |

## 禁止声称

- 未经证实的公司、访谈、上线指标、模型胜出、规则和本人职责。

## Gate 0 待确认

1. 项目事实和证据来源。
2. 一期最小闭环。
3. Rule / RAG / Agent / Tool 的适用性。
4. 输出路径与确认模式。
""",
        )

        write_new(
            work_dir / "evidence-ledger.md",
            """# Evidence Ledger

| ID | 陈述 | 类型 | 来源/路径 | 证据等级 | 可用于哪章 | owner | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E-001 |  | 已确认事实/推断/假设/建议/待决策 |  | E0-E4 |  |  | open |

## 证据缺口

| 缺口 | 影响的决策 | 验证方法 | owner | 截止/状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
""",
        )

        write_new(
            work_dir / "decision-log.md",
            """# Decision Log

| ID | 决策 | 目标/约束 | 证据 | 候选 | 选择 | Why not | 代价/风险 | 重评条件 | owner/date | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-001 |  |  |  |  |  |  |  |  |  | proposed |
""",
        )

        write_new(
            work_dir / "context-snapshot.md",
            """# Context Snapshot

> 只记录决策、接口和未决问题，不复制正文；建议控制在约 1500 中文字内。

## 当前阶段

- Gate 0 / B0。

## 已冻结决策

- 暂无。

## 对象、版本与接口

- 待定义。

## 指标与口径

- 待定义。

## 未决问题

- 项目事实、一期场景与证据待确认。

## 下一批输入

- 完成生产契约和一页纸摘要。
""",
        )

        source_rows = "\n".join(
            f"| S-{idx:03d} | `{source}` | 待读取 | 待判断 |"
            for idx, source in enumerate(args.source, start=1)
        )
        if not source_rows:
            source_rows = "| S-001 |  | 待补充 | 待判断 |"
        write_new(
            work_dir / "source-index.md",
            f"""# Source Index

| ID | 路径/链接 | 状态 | 权威性/用途 |
| --- | --- | --- | --- |
{source_rows}
""",
        )

        state = build_state(project_name, args.project_type, args.mode, final_path)
        write_new(
            work_dir / "build-state.json",
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        )
    except Exception:
        # Avoid leaving a half-created scaffold when a write fails.
        for path in sorted(work_dir.glob("*"), reverse=True):
            if path.is_file():
                path.unlink(missing_ok=True)
        work_dir.rmdir()
        final_path.unlink(missing_ok=True)
        raise

    print(f"已创建最终文档骨架：{final_path}")
    print(f"已创建外部记忆工作区：{work_dir}")
    print("下一步：填写 Project Brief 和 Evidence Ledger，完成 Gate 0 后再分批写正文。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
