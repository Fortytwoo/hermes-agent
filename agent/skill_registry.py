"""Shared skill discovery helpers for tools, slash commands, and menus."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from agent.skill_utils import (
    extract_skill_description,
    extract_skill_visibility_policy,
    get_external_skills_dirs,
    get_disabled_skill_names,
    iter_skill_index_files,
    parse_frontmatter,
    skill_matches_platform,
)


@dataclass(frozen=True)
class SkillRecord:
    name: str
    description: str
    frontmatter: Dict[str, Any]
    skill_md_path: Path
    skill_dir: Path | None
    source: str
    category: str | None = None
    namespace: str | None = None
    bare_name: str | None = None
    root_dir: Path | None = None

    @property
    def identifier(self) -> str:
        if self.namespace:
            return f"{self.namespace}:{self.bare_name or self.name}"
        return self.name

    @property
    def visibility_policy(self) -> Dict[str, Any]:
        return extract_skill_visibility_policy(self.frontmatter)


def _resolve_disabled_skill_names(platform: str | None = None) -> set[str]:
    if platform is None:
        try:
            from tools.skills_tool import _get_disabled_skill_names as _legacy_disabled

            return set(_legacy_disabled())
        except Exception:
            pass
    return set(get_disabled_skill_names(platform=platform))


def get_skill_roots(local_skills_dir: Path) -> List[Path]:
    roots = [local_skills_dir]
    roots.extend(get_external_skills_dirs())
    return roots


def _get_category_from_root(skill_md_path: Path, root_dir: Path) -> str | None:
    try:
        rel_path = skill_md_path.relative_to(root_dir)
    except ValueError:
        return None
    parts = rel_path.parts
    if len(parts) >= 3:
        return parts[0]
    return None


def _description_from_body(body: str) -> str:
    for line in body.strip().split("\n"):
        candidate = line.strip()
        if candidate and not candidate.startswith("#"):
            return candidate
    return ""


def _build_local_record(
    *,
    skill_md_path: Path,
    root_dir: Path,
    source: str,
) -> SkillRecord | None:
    content = skill_md_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    if not skill_matches_platform(frontmatter):
        return None

    skill_dir = skill_md_path.parent if skill_md_path.name == "SKILL.md" else None
    name = str(frontmatter.get("name") or (skill_dir.name if skill_dir else skill_md_path.stem))
    description = extract_skill_description(frontmatter) or _description_from_body(body)
    return SkillRecord(
        name=name,
        description=description,
        frontmatter=frontmatter,
        skill_md_path=skill_md_path,
        skill_dir=skill_dir,
        source=source,
        category=_get_category_from_root(skill_md_path, root_dir),
        bare_name=name,
        root_dir=root_dir,
    )


def iter_local_skill_records(
    local_skills_dir: Path,
    *,
    skip_disabled: bool = False,
    platform: str | None = None,
) -> List[SkillRecord]:
    records: List[SkillRecord] = []
    seen_names: set[str] = set()
    disabled = set() if skip_disabled else _resolve_disabled_skill_names(platform=platform)

    for root_dir in get_skill_roots(local_skills_dir):
        if not root_dir.exists():
            continue
        source = "local" if root_dir == local_skills_dir else "external"
        for skill_md_path in iter_skill_index_files(root_dir, "SKILL.md"):
            try:
                record = _build_local_record(
                    skill_md_path=skill_md_path,
                    root_dir=root_dir,
                    source=source,
                )
            except (OSError, UnicodeDecodeError):
                continue
            except Exception:
                continue
            if record is None:
                continue
            if record.name in seen_names:
                continue
            if record.name in disabled:
                continue
            seen_names.add(record.name)
            records.append(record)
    return records


def find_local_skill_record(
    local_skills_dir: Path,
    name: str,
    *,
    platform: str | None = None,
    skip_disabled: bool = False,
) -> SkillRecord | None:
    disabled = set() if skip_disabled else _resolve_disabled_skill_names(platform=platform)

    for root_dir in get_skill_roots(local_skills_dir):
        if not root_dir.exists():
            continue
        source = "local" if root_dir == local_skills_dir else "external"
        direct_path = root_dir / name
        candidates: List[Path] = []
        if direct_path.is_dir() and (direct_path / "SKILL.md").exists():
            candidates.append(direct_path / "SKILL.md")
        elif direct_path.with_suffix(".md").exists():
            candidates.append(direct_path.with_suffix(".md"))

        for skill_md_path in candidates:
            record = _build_local_record(
                skill_md_path=skill_md_path,
                root_dir=root_dir,
                source=source,
            )
            if record and record.name not in disabled:
                return record

    for record in iter_local_skill_records(
        local_skills_dir,
        skip_disabled=skip_disabled,
        platform=platform,
    ):
        if record.skill_dir and record.skill_dir.name == name:
            return record

    for root_dir in get_skill_roots(local_skills_dir):
        if not root_dir.exists():
            continue
        source = "local" if root_dir == local_skills_dir else "external"
        try:
            candidates = sorted(root_dir.rglob(f"{name}.md"))
        except Exception:
            continue
        for found_md in candidates:
            if found_md.name == "SKILL.md":
                continue
            try:
                record = _build_local_record(
                    skill_md_path=found_md,
                    root_dir=root_dir,
                    source=source,
                )
            except Exception:
                record = None
            if record and record.name not in disabled:
                return record

    return None


def build_plugin_skill_record(
    *,
    namespace: str,
    bare_name: str,
    skill_md_path: Path,
) -> SkillRecord:
    content = skill_md_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    description = extract_skill_description(frontmatter) or _description_from_body(body)
    return SkillRecord(
        name=f"{namespace}:{bare_name}",
        description=description,
        frontmatter=frontmatter,
        skill_md_path=skill_md_path,
        skill_dir=skill_md_path.parent,
        source="plugin",
        namespace=namespace,
        bare_name=bare_name,
    )


def records_to_name_map(records: Iterable[SkillRecord]) -> Dict[str, SkillRecord]:
    return {record.identifier: record for record in records}
