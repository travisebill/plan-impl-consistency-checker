"""Plan vs Implementation 一致性檢查工具。

自動比對 plan 文件與程式碼的關鍵字串是否一致，提早抓出
「plan 寫一套，code 做一套」的問題（如 Phase L.1.2 Ryo Block 1 那種）。
"""
from __future__ import annotations

import re
import sys
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------


@dataclass
class KeywordMatch:
    """單一關鍵字比對結果。"""
    key: str
    line_no: int
    source: Literal["plan", "code"]
    context: str = ""
    file_path: str = ""


@dataclass
class IgnoreEntry:
    """豁免條目。"""
    key: str
    reason: str
    expires: str


@dataclass
class ConsistencyWarning:
    """單一一致性警告。"""
    category: str
    plan_key: str = ""
    code_key: str = ""
    message: str = ""


# ----------------------------------------------------------------------
# Phase 1.1: R2KeyExtractor
# ----------------------------------------------------------------------


class R2KeyExtractor:
    """從 plan 或 code 抽出 R2 object key 字串。

    支援格式：
    - Plan:     gamelogs/{season}/{date}.jsonl.gz（無反引號）
    - Code:     f"gamelogs/cpbl_full_{date_str}.json"
    - Code:     "gamelogs/{date}.jsonl.gz"
    """

    # R2 key 白名單前綴：只有這些目錄/檔案才算 R2 key
    R2_PREFIXES = (
        "gamelogs/", "pbp/", "models/", "odds/",
        "advanced/", "splits/", "weather/",
    )
    R2_KNOWN_FILES = (
        "park_factors.json", "latest.json",
    )

    # Plan: R2 key 通常沒有反引號，直接匹配目錄/副檔名格式
    PLAN_PATTERN = re.compile(r'([a-zA-Z0-9_/{}.-]+/[a-zA-Z0-9_{}. -]+(?:/[a-zA-Z0-9_{}. -]+)*(?:\.[a-z]+(?:\\.gz)?)?)')
    PLAN_BACKTICK_PATTERN = re.compile(r'`([a-zA-Z0-9_/{}.-]+)`')

    # Code: f-string, plain string with R2 key patterns
    CODE_PATTERNS = [
        re.compile(r'f"([a-zA-Z0-9_/{}.-]+)"'),
        re.compile(r"f'([a-zA-Z0-9_/{}.-]+)'"),
        re.compile(r'"([a-zA-Z0-9_/{}.-]+)"'),
        re.compile(r"'([a-zA-Z0-9_/{}.-]+)'"),
    ]

    def _is_r2_key(self, candidate: str) -> bool:
        if "/" not in candidate:
            return False
        if " " in candidate or candidate.startswith("#"):
            return False
        # 排除常見非 R2 key 的 pattern
        if candidate.startswith("//"):
            return False
        if "://" in candidate:
            return False
        # 白名單前綴檢查：必須以 gamelogs/, pbp/, models/ 等開頭
        prefix_ok = any(candidate.startswith(p) for p in self.R2_PREFIXES)
        # 或是已知的 R2 檔案（如 park_factors.json）
        filename_ok = candidate in self.R2_KNOWN_FILES
        return prefix_ok or filename_ok

    def extract(self, text: str, source: Literal["plan", "code"] = "plan") -> list[KeywordMatch]:
        results: list[KeywordMatch] = []
        seen: set[str] = set()

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if source == "plan":
                for pat in [self.PLAN_PATTERN, self.PLAN_BACKTICK_PATTERN]:
                    for m in pat.finditer(line):
                        key = m.group(1)
                        if self._is_r2_key(key) and key not in seen:
                            seen.add(key)
                            results.append(KeywordMatch(
                                key=key, line_no=line_no, source=source, context=stripped,
                            ))
            else:
                for pat in self.CODE_PATTERNS:
                    for m in pat.finditer(line):
                        key = m.group(1)
                        if self._is_r2_key(key) and key not in seen:
                            seen.add(key)
                            results.append(KeywordMatch(
                                key=key, line_no=line_no, source=source, context=stripped,
                            ))
        return results


# ----------------------------------------------------------------------
# Phase 1.2: EnvVarExtractor
# ----------------------------------------------------------------------


class EnvVarExtractor:
    """從 plan 或 code 抽出環境變數名稱。"""

    PLAN_PATTERN = re.compile(r'`?([A-Z][A-Z0-9_]*)`?')
    CODE_PATTERNS = [
        re.compile(r'os\.environ\["([A-Z_][A-Z0-9_]*)"\]'),
        re.compile(r"os\.environ\['([A-Z_][A-Z0-9_]*)'\]"),
        re.compile(r'os\.getenv\["([A-Z_][A-Z0-9_]*)"\]'),
        re.compile(r"os\.getenv\['([A-Z_][A-Z0-9_]*)'\]"),
        re.compile(r'os\.getenv\("([A-Z_][A-Z0-9_]*)"\)'),
        re.compile(r"os\.getenv\('([A-Z_][A-Z0-9_]*)'\)"),
        re.compile(r'\.getenv\("([A-Z_][A-Z0-9_]*)"\)'),
        re.compile(r"\.getenv\('([A-Z_][A-Z0-9_]*)'\)"),
    ]

    NON_ENV = {
        "TRUE", "FALSE", "NONE", "DEBUG", "TEST", "CI",
        "CREATE", "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "TABLE", "INDEX", "FROM", "WHERE", "WHEN", "THEN", "ELSE", "BEGIN",
        "END", "NOT", "SET", "GRANT", "REVOKE", "ROLE", "USER", "PASSWORD",
        "SCHEMA", "FUNCTION", "LANGUAGE", "RETURN", "RETURNS", "BIGINT",
        "TEXT", "JSON", "DATE", "INTERVAL", "UTC", "WITH", "QUERY",
        "HTTP", "HTTPS", "URL", "API", "DNS", "CNAME", "LOGIN", "PASS",
        "FAIL", "PASS", "RED", "GREEN", "EOF", "IOE", "SSR", "E2E",
        "API_BASE", "JSONL", "JSONR", "PBP", "DML", "RATE_LIMITED",
        "INCONSISTENT", "SOURCE_UNAVAILABLE", "MODEL_UNAVAILABLE",
        "AUTH_EXPIRED", "INTERNAL_ERROR", "NETWORK_ERROR", "NOT_FOUND",
        "VALID", "DEFAULT", "ADD", "ALL", "EXISTS", "CONFLICT", "EXCEPTION",
        "RAISE", "NOTICE", "WARNING", "COMPLETE", "BEFORE", "UNTIL",
        "CONCURRENTLY", "LOCK_EX", "LOCK_NB", "MAX_RETRIES",
        "INTERNAL_ERROR", "LOCAL_CACHE", "R2_CACHE_DIR",
        # SQL 操作關鍵字（常被誤當 env var）
        "READ", "WRITE", "TRUNCATE", "MERGE", "UPSERT",
        "GET", "POST", "PUT", "PATCH", "OPTIONS", "HEADERS",
        "R2", "S3", "AWS", "GCP", "AZURE", "SUPABASE",
    }

    def _is_env_var(self, candidate: str) -> bool:
        if candidate in self.NON_ENV:
            return False
        if len(candidate) < 3:
            return False
        # 必須包含底線（純 ALL_CAPS 單字如 READ、WRITE 不算 env var）
        if "_" not in candidate and len(candidate) <= 5:
            return False
        return True

    def extract(self, text: str, source: Literal["plan", "code"] = "plan") -> list[KeywordMatch]:
        results: list[KeywordMatch] = []
        seen: set[str] = set()

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for pat in self.CODE_PATTERNS:
                for m in pat.finditer(line):
                    candidate = m.group(1)
                    if self._is_env_var(candidate) and candidate not in seen:
                        seen.add(candidate)
                        results.append(KeywordMatch(
                            key=candidate, line_no=line_no, source=source, context=stripped,
                        ))

            if source == "plan":
                for m in self.PLAN_PATTERN.finditer(line):
                    candidate = m.group(1)
                    if self._is_env_var(candidate) and candidate not in seen:
                        seen.add(candidate)
                        results.append(KeywordMatch(
                            key=candidate, line_no=line_no, source=source, context=stripped,
                        ))
        return results


# ----------------------------------------------------------------------
# Phase 1.3: ApiPathExtractor
# ----------------------------------------------------------------------


class ApiPathExtractor:
    """從 plan 或 code 抽出 API path 字串。"""

    QUOTED_PATTERN = re.compile(r'["\'](/api/v\d+/[a-zA-Z0-9_/{}-]+)["\']')
    BARE_PATTERN = re.compile(r'(GET|POST|PUT|DELETE|PATCH)\s+(/api/v\d+/[a-zA-Z0-9_/{}-]+)')
    BARE_PATH_PATTERN = re.compile(r'^(/api/v\d+/[a-zA-Z0-9_/{}-]+)$')

    def extract(self, text: str, source: Literal["plan", "code"] = "plan") -> list[KeywordMatch]:
        results: list[KeywordMatch] = []
        seen: set[str] = set()

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for m in self.QUOTED_PATTERN.finditer(line):
                key = m.group(1)
                if key not in seen:
                    seen.add(key)
                    results.append(KeywordMatch(
                        key=key, line_no=line_no, source=source, context=stripped,
                    ))

            for m in self.BARE_PATTERN.finditer(line):
                key = m.group(2)
                if key not in seen:
                    seen.add(key)
                    results.append(KeywordMatch(
                        key=key, line_no=line_no, source=source, context=stripped,
                    ))

            for m in self.BARE_PATH_PATTERN.finditer(stripped):
                key = m.group(1)
                if key not in seen:
                    seen.add(key)
                    results.append(KeywordMatch(
                        key=key, line_no=line_no, source=source, context=stripped,
                    ))
        return results


# ----------------------------------------------------------------------
# Phase 1.4: FunctionSigExtractor
# ----------------------------------------------------------------------


class FunctionSigExtractor:
    """從 plan 或 code 抽出函式簽名字串。

    只比對函式名（不含參數），避免因型別差異（如 Path vs str）產生誤報。
    """

    PATTERN = re.compile(r'def\s+(\w+)\s*\(([^)]*)\)')

    def extract(self, text: str, source: Literal["plan", "code"] = "plan") -> list[KeywordMatch]:
        results: list[KeywordMatch] = []
        seen: set[str] = set()

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for m in self.PATTERN.finditer(line):
                func_name = m.group(1)
                # 只存函式名，不含參數
                key = f"def {func_name}"
                if key not in seen:
                    seen.add(key)
                    results.append(KeywordMatch(
                        key=key, line_no=line_no, source=source, context=stripped,
                    ))
        return results


# ----------------------------------------------------------------------
# Phase 1.5: ErrorCodeExtractor
# ----------------------------------------------------------------------


class ErrorCodeExtractor:
    """從 plan 或 code 抽出錯誤碼常量。"""

    PATTERN = re.compile(r'`?([A-Z][A-Z0-9_]*_(?:FAILED|ERROR|TIMEOUT|EXCEPTION))`?')

    def extract(self, text: str, source: Literal["plan", "code"] = "plan") -> list[KeywordMatch]:
        results: list[KeywordMatch] = []
        seen: set[str] = set()

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for m in self.PATTERN.finditer(line):
                key = m.group(1)
                if key not in seen:
                    seen.add(key)
                    results.append(KeywordMatch(
                        key=key, line_no=line_no, source=source, context=stripped,
                    ))
        return results


# ----------------------------------------------------------------------
# Phase 2: ConsistencyChecker
# ----------------------------------------------------------------------


class ConsistencyChecker:
    """比對 plan 與 code 的關鍵字，產出一致性報告。"""

    def __init__(
        self,
        plan_keys: list[KeywordMatch],
        code_keys: list[KeywordMatch],
        ignore_entries: list[IgnoreEntry] | None = None,
    ) -> None:
        self.plan_keys = plan_keys
        self.code_keys = code_keys
        self.ignore_entries = ignore_entries or []
        self.warnings: list[ConsistencyWarning] = []

    def _is_expired(self, entry: IgnoreEntry) -> bool:
        expires = entry.expires.strip().lower()
        if expires in ("never", "永恆"):
            return False
        return False

    def _is_ignored(self, key: str) -> bool:
        for entry in self.ignore_entries:
            if entry.key == key:
                if self._is_expired(entry):
                    self.warnings.append(ConsistencyWarning(
                        category="_ignore_expired",
                        plan_key=key,
                        message=f"豁免已過期但仍在清單中: {key} (reason: {entry.reason})",
                    ))
                return True
        return False

    def check(self) -> list[ConsistencyWarning]:
        self.warnings = []

        plan_set = {m.key for m in self.plan_keys}
        code_set = {m.key for m in self.code_keys}

        for key in sorted(plan_set):
            if key not in code_set and not self._is_ignored(key):
                self.warnings.append(ConsistencyWarning(
                    category="_keyword",
                    plan_key=key,
                    message=f"📄 Plan 提到「{key}」但 Code 中未找到",
                ))

        for key in sorted(code_set):
            if key not in plan_set and not self._is_ignored(key):
                self.warnings.append(ConsistencyWarning(
                    category="_keyword",
                    code_key=key,
                    message=f"💻 Code 使用「{key}」但 Plan 未記載",
                ))

        return self.warnings

    def get_report(self) -> str:
        if not self.warnings:
            return "✅ 全部一致，0 warnings"

        lines = [f"⚠️  共 {len(self.warnings)} 個一致性警告：", ""]
        for w in self.warnings:
            lines.append(f"  • {w.message}")
        return "\n".join(lines)


# ----------------------------------------------------------------------
# Phase 3: CLI helpers
# ----------------------------------------------------------------------


def scan_directory(
    scope: list[str],
    extensions: tuple[str, ...] = (".py", ".sh", ".ts", ".js"),
) -> dict[str, str]:
    """掃描 scope 目錄，回傳 {rel_path: content}。"""
    files: dict[str, str] = {}
    for pattern in scope:
        p = Path(pattern)
        if p.is_file():
            try:
                files[str(p)] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
        elif p.is_dir():
            for ext in extensions:
                for fp in p.rglob(f"*{ext}"):
                    try:
                        files[str(fp)] = fp.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        pass
    return files


def discover_plan_files(project_root: Path) -> list[Path]:
    """自動發現 plan 文件。"""
    plans: list[Path] = []
    changes = project_root / "docs" / "changes"
    if changes.exists():
        plans.extend(changes.glob("**/03-plan.md"))
        plans.extend(changes.glob("**/03-design.md"))
    designs = project_root / "docs" / "designs"
    if designs.exists():
        plans.extend(designs.glob("*.md"))
    return plans


# ----------------------------------------------------------------------
# Phase 4: InstallHelper
# ----------------------------------------------------------------------


def install_hook(project_path: Path, skill_dir: Path) -> None:
    """在 project_path 的 .git/hooks/ 寫入 pre-commit hook。"""
    hook_dir = project_path / ".git" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hook_dir / "pre-commit"

    content = (
        "#!/bin/bash\n"
        "# auto-generated by plan-impl-consistency-checker\n"
        f'SKILL_DIR="{skill_dir}"\n'
        'PROJECT_ROOT="$(git rev-parse --show-toplevel)"\n'
        '\necho "Plan vs Implementation consistency check..."\n'
        'cd "$PROJECT_ROOT" || exit 1\n'
        'python3 "$SKILL_DIR/check_plan_impl_consistency.py" --auto-discover --scope src/,scripts/ --output-format text\n'
        'EXIT_CODE=$?\n'
        'if [ $EXIT_CODE -ne 0 ]; then\n'
        '    echo "Fix issues before committing. Use --ignore-file to add exemptions."\n'
        'fi\n'
        'exit $EXIT_CODE\n'
    )
    hook_path.write_text(content, encoding="utf-8")
    hook_path.chmod(0o755)
    print(f"Pre-commit hook installed: {hook_path}")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _load_ignore_file(path: str) -> list[IgnoreEntry]:
    """載入 YAML 豁免清單。"""
    import yaml
    entries: list[IgnoreEntry] = []
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return entries
        for section_name, items in data.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "key" in item:
                    entries.append(IgnoreEntry(
                        key=str(item["key"]),
                        reason=str(item.get("reason", "")),
                        expires=str(item.get("expires", "never")),
                    ))
    except Exception as exc:
        print(f"Warning: could not load ignore file {path}: {exc}", file=sys.stderr)
    return entries


def _extract_all(text: str, source: Literal["plan", "code"], category: str) -> list[KeywordMatch]:
    """根據 category 呼叫對應的 extractor。"""
    extractors = {
        "r2_key": R2KeyExtractor(),
        "env_var": EnvVarExtractor(),
        "api_path": ApiPathExtractor(),
        "func_sig": FunctionSigExtractor(),
        "error_code": ErrorCodeExtractor(),
    }
    if category == "all":
        results = []
        for ext in extractors.values():
            results.extend(ext.extract(text, source))
        return results
    ext = extractors.get(category)
    if ext:
        return ext.extract(text, source)
    return []


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Plan vs Implementation 一致性檢查工具（繁中）",
    )
    parser.add_argument(
        "--plan",
        type=str,
        help="Plan 文件路徑",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default="src/scraper/,src/backend/,scripts/",
        help="程式碼掃描範圍，逗號分隔（默认: src/,scripts/）",
    )
    parser.add_argument(
        "--ignore-file",
        type=str,
        help="豁免清單 YAML 檔路徑",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="輸出格式（默认: text）",
    )
    parser.add_argument(
        "--auto-discover",
        action="store_true",
        help="自動發現 plan 文件",
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=["all", "r2_key", "env_var", "api_path", "func_sig", "error_code"],
        default="all",
        help="只檢查特定類別",
    )
    args = parser.parse_args()

    # 載入豁免清單
    ignore_entries: list[IgnoreEntry] = []
    if args.ignore_file:
        ignore_entries = _load_ignore_file(args.ignore_file)

    # 決定 plan 文件
    plan_paths: list[Path] = []
    if args.plan:
        p = Path(args.plan)
        if p.exists():
            plan_paths = [p]
        else:
            print(f"Error: plan file not found: {args.plan}", file=sys.stderr)
            sys.exit(1)
    elif args.auto_discover:
        cwd = Path.cwd()
        plan_paths = discover_plan_files(cwd)
        if not plan_paths:
            print(f"Warning: no plan files found in {cwd}/docs/", file=sys.stderr)
    else:
        print("Error: must specify --plan or --auto-discover", file=sys.stderr)
        sys.exit(1)

    if not plan_paths:
        print("No plan files to check.", file=sys.stderr)
        sys.exit(0)

    # 讀取 plan 內容
    plan_texts: dict[str, str] = {}
    for pp in plan_paths:
        try:
            plan_texts[str(pp)] = pp.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"Warning: could not read {pp}: {exc}", file=sys.stderr)

    # 掃描 code scope
    scope_dirs = [s.strip() for s in args.scope.split(",") if s.strip()]
    code_files = scan_directory(scope_dirs)

    # 對每個 category 做檢查
    all_warnings: list[ConsistencyWarning] = []
    categories = (
        ["r2_key", "env_var", "api_path", "func_sig", "error_code"]
        if args.category == "all"
        else [args.category]
    )

    for cat in categories:
        plan_keys: list[KeywordMatch] = []
        for fp, text in plan_texts.items():
            matches = _extract_all(text, source="plan", category=cat)
            for m in matches:
                m.file_path = fp
            plan_keys.extend(matches)

        code_keys: list[KeywordMatch] = []
        for fp, text in code_files.items():
            matches = _extract_all(text, source="code", category=cat)
            for m in matches:
                m.file_path = fp
            code_keys.extend(matches)

        checker = ConsistencyChecker(plan_keys, code_keys, ignore_entries=ignore_entries)
        warnings = checker.check()
        for w in warnings:
            w.category = cat
        all_warnings.extend(warnings)

    # 輸出報告
    if args.output_format == "json":
        output = {
            "total_warnings": len(all_warnings),
            "warnings": [
                {
                    "category": w.category,
                    "plan_key": w.plan_key,
                    "code_key": w.code_key,
                    "message": w.message,
                }
                for w in all_warnings
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not all_warnings:
            print("✅ 全部一致，0 warnings")
        else:
            print(f"⚠️  共 {len(all_warnings)} 個一致性警告：")
            print()
            for w in all_warnings:
                print(f"  [{w.category}] {w.message}")

    sys.exit(1 if all_warnings else 0)


if __name__ == "__main__":
    main()
