"""Enterprise-scope visibility policy for skills."""

from __future__ import annotations

from typing import Any, Mapping

from agent.scope import EnterpriseScope
from agent.scope_resolver import resolve_enterprise_scope
from agent.skill_utils import extract_skill_visibility_policy


def resolve_effective_enterprise_scope(
    enterprise_scope: EnterpriseScope | None = None,
) -> EnterpriseScope:
    return enterprise_scope or resolve_enterprise_scope()


def _matches_allowed_values(value: str, allowed: list[str] | None) -> bool:
    if not allowed:
        return True
    return value in allowed


def _matches_scope_rule(
    enterprise_scope: EnterpriseScope,
    rule: Mapping[str, str],
) -> bool:
    if not rule:
        return False
    tenant_id = str(rule.get("tenant_id") or "").strip()
    workspace_id = str(rule.get("workspace_id") or "").strip()
    agent_id = str(rule.get("agent_id") or "").strip()
    if tenant_id and enterprise_scope.tenant_id != tenant_id:
        return False
    if workspace_id and enterprise_scope.workspace_id != workspace_id:
        return False
    if agent_id and enterprise_scope.agent_id != agent_id:
        return False
    return True


def extract_visibility_policy(skill_meta: Mapping[str, Any]) -> dict[str, Any]:
    explicit_policy = skill_meta.get("visibility_policy")
    if isinstance(explicit_policy, dict):
        return explicit_policy

    frontmatter = skill_meta.get("frontmatter")
    if isinstance(frontmatter, dict):
        return extract_skill_visibility_policy(frontmatter)
    return {}


def skill_visible_to_scope(
    enterprise_scope: EnterpriseScope | None,
    skill_meta: Mapping[str, Any],
) -> bool:
    """Return True when the current enterprise scope may see this skill.

    Legacy behavior is preserved when:
    - the skill has no visibility policy, or
    - there is no active enterprise scope.
    """
    policy = extract_visibility_policy(skill_meta)
    if not policy:
        return True

    scope = resolve_effective_enterprise_scope(enterprise_scope)
    if not scope.is_scoped():
        return True

    if not _matches_allowed_values(scope.tenant_id, policy.get("tenant_ids")):
        return False
    if not _matches_allowed_values(scope.workspace_id, policy.get("workspace_ids")):
        return False
    if not _matches_allowed_values(scope.agent_id, policy.get("agent_ids")):
        return False

    scoped_rules = policy.get("scopes") or []
    if scoped_rules:
        return any(_matches_scope_rule(scope, rule) for rule in scoped_rules)

    return True


def skill_list_visible_to_scope(
    enterprise_scope: EnterpriseScope | None,
    skill_meta: Mapping[str, Any],
) -> bool:
    return skill_visible_to_scope(enterprise_scope, skill_meta)


def skill_view_visible_to_scope(
    enterprise_scope: EnterpriseScope | None,
    skill_meta: Mapping[str, Any],
) -> bool:
    return skill_visible_to_scope(enterprise_scope, skill_meta)
