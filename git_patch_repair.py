#!/usr/bin/env python3
\"\"\"AI-style patch planner / iterative repair engine (v4).

Modes:
- --scan-only       : analyse only, never modify the input patch.
- --apply-repairs   : single-pass conservative repair.
- --iterative       : multi-pass feedback loop (apply ➝ validate ➝ re-apply).

Notes:
- In scan-only mode, no repairs are applied; the planner only observes and logs.
- In apply-repairs / iterative modes, structural fixes (e.g. span header fixes)
  may be applied.
\"\"\"

from __future__ import annotations


import json
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

ACTION_PLAN: List[Dict[str, Any]] = []
CURRENT_ITERATION: int = 0


def log(code: str, phase: str, message: str, **extra: Any) -> None:
    entry: Dict[str, Any] = {
        "code": code,
        "phase": phase,
        "message": message,
        "iteration": CURRENT_ITERATION,
    }
    if extra:
        entry["data"] = extra
    ACTION_PLAN.append(entry)


def preview(text: str, max_len: int = 80) -> str:
    text = text.replace("\n", "\\n")
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def load_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def save_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def basic_clean(text: str) -> List[str]:
    lines = text.splitlines(keepends=True)
    log(
        "BASIC_CLEAN_START",
        "basic_clean",
        "Starting basic_clean",
        line_count=len(lines),
    )

    preamble_index: Optional[int] = None
    for i, line in enumerate(lines):
        if line.startswith("diff --git "):
            preamble_index = i
            break

    if preamble_index is not None and preamble_index != 0:
        log(
            "PREAMBLE_STRIPPED",
            "basic_clean",
            "Stripped preamble before first diff --git",
            removed_lines=preamble_index,
        )
        lines = lines[preamble_index:]
    else:
        log(
            "PREAMBLE_NONE",
            "basic_clean",
            "No preamble detected before first diff --git",
        )

    cleaned: List[str] = []
    trimmed = 0
    for lineno, line in enumerate(lines, start=1):
        if line.rstrip() != line:
            trimmed += 1
            log(
                "WHITESPACE_TRIMMED",
                "basic_clean",
                "Trimmed trailing whitespace on line",
                line_number=lineno,
                original_preview=preview(line),
            )
        cleaned.append(line.rstrip("\n").rstrip() + "\n")

    lines = cleaned
    log(
        "WHITESPACE_TRIM_SUMMARY",
        "basic_clean",
        "Trailing whitespace trimming summary",
        trimmed_lines=trimmed,
    )

    dropped = 0
    while lines and lines[-1].startswith("+") and lines[-1].strip() == "+":
        dropped += 1
        lines.pop()

    log(
        "EOF_PLUS_BLANK_DROPPED",
        "basic_clean",
        "Dropped trailing '+ blank' lines at EOF",
        dropped_lines=dropped,
    )

    log(
        "BASIC_CLEAN_END",
        "basic_clean",
        "Finished basic_clean",
        line_count=len(lines),
    )
    return lines


class Hunk:
    def __init__(self, header_line: str) -> None:
        self.header: str = header_line
        self.body: List[str] = []


class FileDiff:
    def __init__(self, header: str) -> None:
        self.header: str = header
        self.headers: List[str] = []
        self.hunks: List[Hunk] = []


def parse_diff(lines: List[str]) -> List[FileDiff]:
    files: List[FileDiff] = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[Hunk] = None

    for lineno, line in enumerate(lines, start=1):
        if line.startswith("diff --git "):
            current_file = FileDiff(line)
            files.append(current_file)
            log(
                "PARSE_FILE_START",
                "parse",
                "Detected new file diff section",
                line_number=lineno,
                diff_header_preview=preview(line),
            )
            current_hunk = None
            continue

        if current_file is None:
            log(
                "PARSE_ORPHAN_LINE",
                "parse",
                "Line before any diff section (ignored)",
                line_number=lineno,
                text_preview=preview(line),
            )
            continue

        if line.startswith("@@ "):
            current_hunk = Hunk(line)
            current_file.hunks.append(current_hunk)
            log(
                "PARSE_HUNK_HEADER",
                "parse",
                "Detected hunk header",
                line_number=lineno,
                header_preview=preview(line),
            )
            continue

        if current_hunk is not None:
            current_hunk.body.append(line)
            log(
                "PARSE_HUNK_BODY_LINE",
                "parse",
                "Recorded hunk body line",
                line_number=lineno,
                text_preview=preview(line),
            )
        else:
            current_file.headers.append(line)
            log(
                "PARSE_FILE_HEADER_LINE",
                "parse",
                "Recorded file header line",
                line_number=lineno,
                text_preview=preview(line),
            )

    log(
        "PARSE_SUMMARY",
        "parse",
        "Finished parsing patch",
        file_count=len(files),
    )
    return files


def _count_body_lines(hunk: Hunk) -> Tuple[int, int, int, bool]:
    context = 0
    removed = 0
    added = 0
    has_unexpected = False

    for line in hunk.body:
        if line.startswith(" "):
            context += 1
        elif line.startswith("-"):
            removed += 1
        elif line.startswith("+") and line.strip() != "+":
            added += 1
        elif line.startswith("\\ No newline at end of file"):
            continue
        else:
            has_unexpected = True

    return context, removed, added, has_unexpected


def _maybe_fix_span_header(
    hunk: Hunk,
    file_header: str,
    old_span: int,
    new_span: int,
    context: int,
    removed: int,
    added: int,
) -> Tuple[bool, int, int]:
    repaired = False
    expected_old = context + removed
    expected_new = context + added

    if expected_old != old_span or expected_new != new_span:
        new_header = re.sub(
            r"@@ -\d+,\d+ \+\d+,\d+ @@",
            f"@@ -0,{expected_old} +0,{expected_new} @@",
            hunk.header,
        )
        log(
            "HUNK_HEADER_SPAN_REPAIRED",
            "validate",
            "Repaired hunk header span values",
            file_header_preview=preview(file_header),
            old_header_preview=preview(hunk.header),
            new_header_preview=preview(new_header),
            old_span=old_span,
            new_span=new_span,
            expected_old_span=expected_old,
            expected_new_span=expected_new,
        )
        hunk.header = new_header
        old_span = expected_old
        new_span = expected_new
        repaired = True

    return repaired, old_span, new_span


def validate_hunk(
    hunk: Hunk,
    file_header: str,
    allow_repairs: bool,
) -> bool:
    match = re.match(
        r"@@ -\d+,(?P<old>\d+) \+\d+,(?P<new>\d+) @@",
        hunk.header,
    )
    if not match:
        log(
            "HUNK_INVALID_MALFORMED_HEADER",
            "validate",
            "Hunk header is malformed",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            repair_hint="REPAIR_RECONSTRUCT_MALFORMED_HEADER or regenerate diff.",
        )
        return False

    old_span = int(match.group("old"))
    new_span = int(match.group("new"))

    context, removed, added, has_unexpected = _count_body_lines(hunk)

    if has_unexpected:
        log(
            "HUNK_INVALID_UNEXPECTED_LINE",
            "validate",
            "Unexpected line type in hunk body",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            repair_hint="REPAIR_REBUILD_HUNK_FROM_BODY or drop hunk.",
        )
        if not allow_repairs:
            return False

    expected_old = context + removed
    expected_new = context + added

    if expected_old == old_span and expected_new == new_span and not has_unexpected:
        log(
            "HUNK_VALID",
            "validate",
            "Hunk is structurally valid",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            old_span=old_span,
            new_span=new_span,
            context_lines=context,
            removed_lines=removed,
            added_lines=added,
        )
        return True

    if not allow_repairs:
        if expected_old != old_span:
            log(
                "HUNK_INVALID_OLD_SPAN_MISMATCH",
                "validate",
                "Old span mismatch in hunk header",
                file_header_preview=preview(file_header),
                header_preview=preview(hunk.header),
                expected_old_span=expected_old,
                actual_old_span=old_span,
                repair_hint=(
                    "REPAIR_FIX_OLD_SPAN_HEADER or "
                    "REPAIR_APPROXIMATE_HEADER_REWRITE."
                ),
            )
        if expected_new != new_span:
            log(
                "HUNK_INVALID_NEW_SPAN_MISMATCH",
                "validate",
                "New span mismatch in hunk header",
                file_header_preview=preview(file_header),
                header_preview=preview(hunk.header),
                expected_new_span=expected_new,
                actual_new_span=new_span,
                repair_hint=(
                    "REPAIR_FIX_NEW_SPAN_HEADER or "
                    "REPAIR_APPROXIMATE_HEADER_REWRITE."
                ),
            )
        return False

    repaired, old_span2, new_span2 = _maybe_fix_span_header(
        hunk,
        file_header,
        old_span,
        new_span,
        context,
        removed,
        added,
    )

    if repaired:
        log(
            "HUNK_VALID_AFTER_REPAIR",
            "validate",
            "Hunk became valid after header span repair",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            old_span=old_span2,
            new_span=new_span2,
        )
        return True

    if expected_old != old_span:
        log(
            "HUNK_INVALID_OLD_SPAN_MISMATCH",
            "validate",
            "Old span mismatch in hunk header (repair failed)",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            expected_old_span=expected_old,
            actual_old_span=old_span,
            repair_hint="REPAIR_FIX_OLD_SPAN_HEADER or REPAIR_REGENERATE_DIFF_FOR_FILE.",
        )

    if expected_new != new_span:
        log(
            "HUNK_INVALID_NEW_SPAN_MISMATCH",
            "validate",
            "New span mismatch in hunk header (repair failed)",
            file_header_preview=preview(file_header),
            header_preview=preview(hunk.header),
            expected_new_span=expected_new,
            actual_new_span=new_span,
            repair_hint="REPAIR_FIX_NEW_SPAN_HEADER or REPAIR_REGENERATE_DIFF_FOR_FILE.",
        )

    return False


def filter_or_repair_files(
    files: List[FileDiff],
    allow_repairs: bool,
) -> List[FileDiff]:
    result: List[FileDiff] = []

    for file_diff in files:
        valid_hunks: List[Hunk] = []
        for hunk in file_diff.hunks:
            if validate_hunk(hunk, file_diff.header, allow_repairs):
                valid_hunks.append(hunk)

        if valid_hunks:
            file_diff.hunks = valid_hunks
            result.append(file_diff)
        else:
            log(
                "FILE_DROPPED_NO_VALID_HUNKS",
                "validate",
                "Dropping file diff because it has no valid hunks",
                file_header_preview=preview(file_diff.header),
                repair_hint="REPAIR_REGENERATE_DIFF_FOR_FILE or REPAIR_REGENERATE_FULL_PATCH.",
            )

    log(
        "FILTER_FILES_SUMMARY",
        "validate",
        "Finished validating/repairing hunks and filtering files",
        remaining_files=len(result),
    )
    return result


def render_patch(files: List[FileDiff]) -> str:
    out: List[str] = []
    for file_diff in files:
        out.append(file_diff.header)
        out.extend(file_diff.headers)
        for hunk in file_diff.hunks:
            out.append(hunk.header)
            out.extend(hunk.body)

    text = "".join(out)
    lines = len(text.splitlines())
    log(
        "RENDER_SUMMARY",
        "render",
        "Rendered patch text from FileDiffs",
        rendered_lines=lines,
    )
    return text


def git_validate(patch_text: str) -> str:
    proc = subprocess.Popen(
        ["git", "apply", "--check", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(patch_text)
    combined = (stdout or "") + (stderr or "")
    combined = combined.strip()

    if proc.returncode == 0:
        log(
            "GIT_VALIDATE_OK",
            "git_validate",
            "git apply --check reports patch is structurally valid",
        )
        return "ok"

    log(
        "GIT_VALIDATE_ERROR",
        "git_validate",
        "git apply --check reports patch issues",
        stderr=combined,
    )
    return "error"


REPAIR_METHODS: List[Dict[str, Any]] = [
    {
        "repair_code": "REPAIR_FIX_NEW_SPAN_HEADER",
        "applies_to_event_codes": ["HUNK_INVALID_NEW_SPAN_MISMATCH"],
        "description": "Corrects the new_span field in the hunk header so it matches actual added+context lines.",
        "approximation_allowed": False,
        "strategy": "Rewrite +section span in @@ header to actual_new_span derived from body.",
        "safety": "medium",
        "notes": "Most common corruption. Safe to auto-apply in many cases."
    },
    {
        "repair_code": "REPAIR_FIX_OLD_SPAN_HEADER",
        "applies_to_event_codes": ["HUNK_INVALID_OLD_SPAN_MISMATCH"],
        "description": "Corrects the old_span field in the hunk header so it matches actual removed+context lines.",
        "approximation_allowed": False,
        "strategy": "Rewrite -section span in @@ header to actual_old_span derived from body.",
        "safety": "medium",
        "notes": "Pair with REPAIR_FIX_NEW_SPAN_HEADER when both sides mismatch."
    },
    {
        "repair_code": "REPAIR_RECONSTRUCT_MALFORMED_HEADER",
        "applies_to_event_codes": ["HUNK_INVALID_MALFORMED_HEADER"],
        "description": "Reconstructs a missing, truncated or corrupted @@ header.",
        "approximation_allowed": True,
        "strategy": "Infer spans from body or context, synthesise a minimal canonical @@ header.",
        "safety": "low",
        "notes": "Useful when patches are damaged by emails, markdown or PDF extraction."
    },
    {
        "repair_code": "REPAIR_REBUILD_HUNK_FROM_BODY",
        "applies_to_event_codes": ["HUNK_INVALID_UNEXPECTED_LINE"],
        "description": "Repairs a hunk body by rewriting non-prefix lines into valid context or removed lines.",
        "approximation_allowed": True,
        "strategy": "Filter or normalise unexpected body lines; convert to context when unclear.",
        "safety": "low",
        "notes": "Good for salvaging when formatting bled into diff body."
    },
    {
        "repair_code": "REPAIR_REMOVE_WHITESPACE_CORRUPTION",
        "applies_to_event_codes": ["WHITESPACE_TRIMMED"],
        "description": "Normalises whitespace to prevent prefix corruption in diff lines.",
        "approximation_allowed": True,
        "strategy": "Convert tabs to spaces; ensure diff prefixes are intact and aligned.",
        "safety": "medium",
        "notes": "Important for patches copied from terminals or web consoles."
    },
    {
        "repair_code": "REPAIR_STRIP_LEADING_PLUS_BLANKS",
        "applies_to_event_codes": ["EOF_PLUS_BLANK_DROPPED"],
        "description": "Removes or normalises trailing '+ blank' lines at EOF.",
        "approximation_allowed": True,
        "strategy": "Drop trailing '+\\n' lines or treat them as context if needed.",
        "safety": "high",
        "notes": "Rarely harmful; git typically ignores these lines."
    },
    {
        "repair_code": "REPAIR_APPROXIMATE_HEADER_REWRITE",
        "applies_to_event_codes": [
            "HUNK_INVALID_NEW_SPAN_MISMATCH",
            "HUNK_INVALID_OLD_SPAN_MISMATCH",
            "HUNK_INVALID_MALFORMED_HEADER"
        ],
        "description": "Creates an approximate header when exact reconstruction is not possible.",
        "approximation_allowed": True,
        "strategy": "Estimate spans from available body information and fallback heuristics.",
        "safety": "low",
        "notes": "Enables partial recovery of heavily corrupted hunks."
    },
    {
        "repair_code": "REPAIR_DROP_HUNK_IF_UNFIXABLE",
        "applies_to_event_codes": [
            "HUNK_INVALID_NEW_SPAN_MISMATCH",
            "HUNK_INVALID_OLD_SPAN_MISMATCH",
            "HUNK_INVALID_UNEXPECTED_LINE",
            "HUNK_INVALID_MALFORMED_HEADER"
        ],
        "description": "Drops the hunk entirely when repair attempts fail.",
        "approximation_allowed": False,
        "strategy": "Remove the hunk block from the patch.",
        "safety": "destructive",
        "notes": "Last resort when structural recovery is not feasible."
    },
    {
        "repair_code": "REPAIR_REGENERATE_DIFF_FOR_FILE",
        "applies_to_event_codes": ["FILE_DROPPED_NO_VALID_HUNKS"],
        "description": "Regenerates the diff for a single file from the source tree.",
        "approximation_allowed": False,
        "strategy": "Use git diff or semantic diff for the specific file.",
        "safety": "high",
        "notes": "Preferred when repository context is available."
    },
    {
        "repair_code": "REPAIR_REGENERATE_FULL_PATCH",
        "applies_to_event_codes": ["PLAN_SUMMARY"],
        "description": "Recreates the entire patch if all other repairs fail.",
        "approximation_allowed": True,
        "strategy": "Regenerate patch via git diff or semantic diff, possibly in multiple passes.",
        "safety": "high",
        "notes": "Used when valid_files == 0 or patch is fully broken."
    },
    {
        "repair_code": "REPAIR_VERIFY_WITH_GIT_APPLY",
        "applies_to_event_codes": ["GIT_VALIDATE_ERROR"],
        "description": "Performs iterative repair cycles until git accepts the patch.",
        "approximation_allowed": False,
        "strategy": "Apply selected repairs, rerun git apply --check, repeat until clean or give up.",
        "safety": "high",
        "notes": "Acts as a final gatekeeper before accepting a patch."
    }
]


def run_scan_only(input_path: str, validate_with_git: bool) -> Dict[str, Any]:
    original = load_file(input_path)
    cleaned_lines = basic_clean(original)
    files = parse_diff(cleaned_lines)
    _ = filter_or_repair_files(files, allow_repairs=False)

    git_result: Optional[str] = None
    if validate_with_git:
        git_result = git_validate(original)

    log(
        "PLAN_SUMMARY",
        "meta",
        "Scan-only patch analysis completed",
        valid_files=None,
        git_validation=git_result,
    )

    plan: Dict[str, Any] = {
        "plan_version": 4,
        "mode": "scan-only",
        "input_file": input_path,
        "output_file": None,
        "steps": ACTION_PLAN,
        "repair_methods": REPAIR_METHODS,
        "summary": {
            "valid_files": None,
            "git_validation": git_result,
        },
    }
    return plan


def run_apply_once(
    input_path: str,
    output_path: str,
    validate_with_git: bool,
) -> Dict[str, Any]:
    original = load_file(input_path)
    cleaned_lines = basic_clean(original)
    files = parse_diff(cleaned_lines)
    repaired_files = filter_or_repair_files(files, allow_repairs=True)
    repaired_patch = render_patch(repaired_files)
    save_file(output_path, repaired_patch)

    git_result: Optional[str] = None
    if validate_with_git:
        git_result = git_validate(repaired_patch)

    log(
        "PLAN_SUMMARY",
        "meta",
        "Single-pass repair completed",
        valid_files=len(repaired_files),
        git_validation=git_result,
    )

    plan: Dict[str, Any] = {
        "plan_version": 4,
        "mode": "apply-repairs",
        "input_file": input_path,
        "output_file": output_path,
        "steps": ACTION_PLAN,
        "repair_methods": REPAIR_METHODS,
        "summary": {
            "valid_files": len(repaired_files),
            "git_validation": git_result,
        },
    }
    return plan


def run_iterative(
    input_path: str,
    output_path: str,
    validate_with_git: bool,
    max_iterations: int = 5,
) -> Dict[str, Any]:
    global CURRENT_ITERATION

    original = load_file(input_path)
    patch_text = original
    git_result: Optional[str] = None
    last_patch_text: Optional[str] = None

    for iteration in range(max_iterations):
        CURRENT_ITERATION = iteration
        log(
            "ITERATION_START",
            "meta",
            "Starting repair iteration",
            iteration=iteration,
        )

        cleaned_lines = basic_clean(patch_text)
        files = parse_diff(cleaned_lines)
        repaired_files = filter_or_repair_files(files, allow_repairs=True)
        new_patch_text = render_patch(repaired_files)

        if validate_with_git:
            git_result = git_validate(new_patch_text)

        if last_patch_text is not None and new_patch_text == last_patch_text:
            log(
                "ITERATION_NO_PROGRESS",
                "meta",
                "Iteration made no textual changes; stopping loop",
                iteration=iteration,
            )
            patch_text = new_patch_text
            break

        if git_result == "ok":
            log(
                "ITERATION_GIT_OK",
                "meta",
                "git apply --check succeeded; stopping loop",
                iteration=iteration,
            )
            patch_text = new_patch_text
            break

        patch_text = new_patch_text
        last_patch_text = new_patch_text

        log(
            "ITERATION_END",
            "meta",
            "Completed repair iteration",
            iteration=iteration,
            git_validation=git_result,
        )

    save_file(output_path, patch_text)

    log(
        "PLAN_SUMMARY",
        "meta",
        "Iterative repair completed",
        iterations_run=iteration + 1,
        git_validation=git_result,
    )

    plan: Dict[str, Any] = {
        "plan_version": 4,
        "mode": "iterative",
        "input_file": input_path,
        "output_file": output_path,
        "steps": ACTION_PLAN,
        "repair_methods": REPAIR_METHODS,
        "summary": {
            "iterations_run": iteration + 1,
            "git_validation": git_result,
        },
    }
    return plan


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="AI-style patch planner / iterative repair engine."
    )
    parser.add_argument("input", help="Input patch file")
    parser.add_argument(
        "output",
        nargs="?",
        help="Output (repaired) patch file (required for --apply-repairs or --iterative)",
    )
    parser.add_argument(
        "--plan-out",
        help="Path to write pretty-printed JSON action plan",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run `git apply --check` in the chosen mode",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Analyse patch and emit a plan without modifying patch contents",
    )
    parser.add_argument(
        "--apply-repairs",
        action="store_true",
        help="Apply a single-pass conservative repair and write repaired patch",
    )
    parser.add_argument(
        "--iterative",
        action="store_true",
        help="Run an iterative feedback loop with multiple repair passes",
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=5,
        help="Maximum number of iterations in --iterative mode (default 5)",
    )

    args = parser.parse_args()

    mode_flags = [
        args.scan_only,
        args.apply_repairs,
        args.iterative,
    ]
    if sum(1 for flag in mode_flags if flag) > 1:
        raise SystemExit(
            "Choose exactly one of: --scan-only, --apply-repairs, --iterative."
        )

    if not any(mode_flags):
        args.scan_only = True

    ACTION_PLAN.clear()
    global CURRENT_ITERATION
    CURRENT_ITERATION = 0

    if args.scan_only:
        log(
            "PLAN_START",
            "meta",
            "Starting scan-only patch analysis",
            input_file=args.input,
            output_file=None,
        )
        plan = run_scan_only(args.input, args.validate)
    elif args.apply_repairs:
        if not args.output:
            raise SystemExit(
                "Output path is required when using --apply-repairs."
            )
        log(
            "PLAN_START",
            "meta",
            "Starting single-pass repair",
            input_file=args.input,
            output_file=args.output,
        )
        plan = run_apply_once(args.input, args.output, args.validate)
    else:
        if not args.output:
            raise SystemExit(
                "Output path is required when using --iterative."
            )
        log(
            "PLAN_START",
            "meta",
            "Starting iterative repair loop",
            input_file=args.input,
            output_file=args.output,
        )
        plan = run_iterative(
            args.input,
            args.output,
            args.validate,
            max_iterations=args.max_iters,
        )

    if args.plan_out:
        with open(args.plan_out, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
