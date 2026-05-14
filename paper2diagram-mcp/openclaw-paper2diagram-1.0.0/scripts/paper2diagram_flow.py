#!/usr/bin/env python3
"""
Stateful helper for the OpenClaw paper-to-diagram workflow.

The script keeps deterministic work out of prompt-only skills:
- path validation
- output directory creation
- prompt extraction from Gemini analysis text
- draw queue generation
- JSONL state logging
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


DEFAULT_PAPERS_DIR = Path("/home/xie/桌面/papers")
DEFAULT_ANALYSIS_DIR = Path("/home/xie/桌面/analysis")
DEFAULT_IMAGES_DIR = Path("/home/xie/桌面/images")
DEFAULT_GEMINI_URL = "https://gemini.google.com/app"


@dataclass
class PromptItem:
    index: int
    title: str
    prompt: str
    output_path: Path


@dataclass
class FlowPaths:
    paper_name: str
    papers_dir: Path
    analysis_dir: Path
    images_dir: Path

    @property
    def paper_path(self) -> Path:
        return self.papers_dir / f"{self.paper_name}.pdf"

    @property
    def analysis_path(self) -> Path:
        return self.analysis_dir / f"{self.paper_name}.txt"

    @property
    def image_dir(self) -> Path:
        return self.images_dir / self.paper_name

    @property
    def queue_path(self) -> Path:
        return self.image_dir / "draw_queue.json"

    @property
    def state_log_path(self) -> Path:
        return self.image_dir / "state.jsonl"


class StateLog:
    def __init__(self, path: Path):
        self.path = path

    def emit(self, state: str, **data: object) -> None:
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "state": state,
            **data,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        print(f"STATE: {state}")
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))


class AgentBrowser:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def run(self, args: Iterable[str], timeout: int = 60) -> subprocess.CompletedProcess:
        cmd = ["agent-browser", *args]
        if self.dry_run:
            print("DRY_RUN:", " ".join(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def require_ok(self, args: Iterable[str], state_log: StateLog, state: str) -> str:
        result = self.run(args)
        if result.returncode != 0:
            state_log.emit("ERROR", failed_state=state, stderr=result.stderr)
            raise RuntimeError(f"agent-browser failed in {state}: {result.stderr}")
        state_log.emit(state)
        return result.stdout


def normalize_paper_name(raw: str) -> str:
    name = raw.strip()
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    if name.lower().endswith(".txt"):
        name = name[:-4]
    if not name:
        raise ValueError("paper_name must not be empty")
    return name


def build_paths(args: argparse.Namespace) -> FlowPaths:
    return FlowPaths(
        paper_name=normalize_paper_name(args.paper_name),
        papers_dir=Path(args.papers_dir).expanduser(),
        analysis_dir=Path(args.analysis_dir).expanduser(),
        images_dir=Path(args.images_dir).expanduser(),
    )


def prepare(paths: FlowPaths, state_log: StateLog) -> None:
    paths.analysis_dir.mkdir(parents=True, exist_ok=True)
    paths.image_dir.mkdir(parents=True, exist_ok=True)
    state_log.emit(
        "PREPARED",
        paper_path=str(paths.paper_path),
        analysis_path=str(paths.analysis_path),
        image_dir=str(paths.image_dir),
    )
    if not paths.paper_path.exists():
        state_log.emit("PAPER_MISSING", paper_path=str(paths.paper_path))


def extract_prompt_blocks(text: str) -> List[tuple[str, str]]:
    text = text.lstrip("\ufeff")
    blocks: List[tuple[str, str]] = []
    headers = list(re.finditer(r"^\s*\[(?P<title>[^\]]+)\]\s*$", text, re.MULTILINE))
    for offset, header in enumerate(headers):
        start = header.end()
        end = headers[offset + 1].start() if offset + 1 < len(headers) else len(text)
        body = text[start:end].strip()
        prompt_match = re.search(r"Prompt\s*[:：]\s*(?P<prompt>.*)", body, re.IGNORECASE | re.DOTALL)
        prompt = prompt_match.group("prompt").strip() if prompt_match else body
        if prompt:
            blocks.append((header.group("title").strip(), prompt))
    if blocks:
        return blocks

    figure_pattern = re.compile(
        r"(?P<title>(?:图|Figure)\s*[\dA-Za-z.-]*[^\n]*)\n(?P<body>.*?)(?=(?:\n(?:图|Figure)\s*[\dA-Za-z.-]*)|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in figure_pattern.finditer(text):
        body = match.group("body").strip()
        prompt_match = re.search(r"Prompt\s*[:：]\s*(?P<prompt>.*)", body, re.IGNORECASE | re.DOTALL)
        prompt = prompt_match.group("prompt").strip() if prompt_match else body
        if prompt:
            blocks.append((match.group("title").strip(), prompt))
    return blocks


def build_queue(paths: FlowPaths, state_log: StateLog) -> List[PromptItem]:
    if not paths.analysis_path.exists():
        state_log.emit("ERROR", reason="analysis file missing", path=str(paths.analysis_path))
        raise FileNotFoundError(paths.analysis_path)

    text = paths.analysis_path.read_text(encoding="utf-8")
    blocks = extract_prompt_blocks(text)
    if not blocks:
        state_log.emit("ERROR", reason="no prompt blocks found", path=str(paths.analysis_path))
        raise ValueError("No prompt blocks found in analysis file")

    items = [
        PromptItem(
            index=index,
            title=title,
            prompt=prompt,
            output_path=paths.image_dir / f"figure_{index}.png",
        )
        for index, (title, prompt) in enumerate(blocks, start=1)
    ]
    payload = [
        {
            "index": item.index,
            "title": item.title,
            "prompt": item.prompt,
            "output_path": str(item.output_path),
        }
        for item in items
    ]
    paths.image_dir.mkdir(parents=True, exist_ok=True)
    paths.queue_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    state_log.emit("QUEUE_CREATED", total_images=len(items), queue_path=str(paths.queue_path))
    return items


def upload_with_existing_script(
    paths: FlowPaths,
    state_log: StateLog,
    url: str,
    upload_script: Path,
    selector: Optional[str],
    wait_ms: int,
) -> None:
    if not paths.paper_path.exists():
        state_log.emit("ERROR", reason="paper file missing", path=str(paths.paper_path))
        raise FileNotFoundError(paths.paper_path)

    cmd = [
        sys.executable,
        str(upload_script),
        url,
        str(paths.paper_path),
    ]
    if selector:
        cmd.append(selector)
    cmd.append(str(wait_ms))

    state_log.emit("UPLOAD_STARTED", command=" ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        state_log.emit("ERROR", reason="upload failed", stderr=result.stderr, stdout=result.stdout)
        raise RuntimeError("upload failed")
    state_log.emit("UPLOAD_COMPLETED", stdout=result.stdout[-1000:])


def verify_images(paths: FlowPaths, state_log: StateLog) -> None:
    if not paths.queue_path.exists():
        state_log.emit("ERROR", reason="queue file missing", path=str(paths.queue_path))
        raise FileNotFoundError(paths.queue_path)
    queue = json.loads(paths.queue_path.read_text(encoding="utf-8"))
    missing = [item["output_path"] for item in queue if not Path(item["output_path"]).exists()]
    if missing:
        state_log.emit("IMAGES_INCOMPLETE", missing=missing, total_missing=len(missing))
        return
    state_log.emit("ALL_COMPLETED", total_images=len(queue))


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paper_name", help="Paper file name with or without .pdf/.txt")
    parser.add_argument("--papers-dir", default=os.environ.get("P2D_PAPERS_DIR", DEFAULT_PAPERS_DIR))
    parser.add_argument("--analysis-dir", default=os.environ.get("P2D_ANALYSIS_DIR", DEFAULT_ANALYSIS_DIR))
    parser.add_argument("--images-dir", default=os.environ.get("P2D_IMAGES_DIR", DEFAULT_IMAGES_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw paper-to-diagram workflow helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Create directories and validate paths")
    add_common_args(prepare_parser)

    queue_parser = subparsers.add_parser("queue", help="Parse analysis text into draw_queue.json")
    add_common_args(queue_parser)

    verify_parser = subparsers.add_parser("verify", help="Verify all queued image files exist")
    add_common_args(verify_parser)

    upload_parser = subparsers.add_parser("upload", help="Upload the paper using the existing upload skill script")
    add_common_args(upload_parser)
    upload_parser.add_argument("--url", default=DEFAULT_GEMINI_URL)
    upload_parser.add_argument("--selector", default=None)
    upload_parser.add_argument("--wait-ms", type=int, default=2000)
    upload_parser.add_argument(
        "--upload-script",
        default=Path(__file__).resolve().parents[2] / "upload-file-1.0.0" / "scripts" / "upload.py",
    )

    args = parser.parse_args()
    paths = build_paths(args)
    state_log = StateLog(paths.state_log_path)

    if args.command == "prepare":
        prepare(paths, state_log)
    elif args.command == "queue":
        prepare(paths, state_log)
        build_queue(paths, state_log)
    elif args.command == "verify":
        verify_images(paths, state_log)
    elif args.command == "upload":
        prepare(paths, state_log)
        upload_with_existing_script(
            paths=paths,
            state_log=state_log,
            url=args.url,
            upload_script=Path(args.upload_script),
            selector=args.selector,
            wait_ms=args.wait_ms,
        )
    else:
        parser.error(f"Unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
