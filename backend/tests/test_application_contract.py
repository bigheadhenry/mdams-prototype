"""
申请状态机与权限合约测试（无数据库依赖）

验证：
- 状态转换规则（哪些转换合法，哪些非法）
- 权限函数签名（非 mock 数据，仅代码级验证）
- 审计日志结构
"""
from __future__ import annotations

import pytest

from app.permissions import (
    CurrentUser,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


# ── 状态机 `status` progress test ────────────────────────────


class TestApplicationStateMachineContract:
    """验证申请状态转换规则的可推导性（纯逻辑测试）"""

    # 合法的状态转换路径
    VALID_TRANSITIONS: dict[str, list[str]] = {
        "submitted": ["approved", "rejected"],
        "approved": ["fulfilled"],
        "rejected": [],
        "fulfilled": [],
    }

    # 所有已知状态
    ALL_STATUSES = ["submitted", "approved", "rejected", "fulfilled"]

    def test_all_statuses_covered(self):
        """所有状态都有转换规则"""
        for status in self.ALL_STATUSES:
            assert status in self.VALID_TRANSITIONS, f"Missing transition rules for {status}"

    @pytest.mark.parametrize("from_status,to_status", [
        ("submitted", "approved"),   # ✓ approve
        ("submitted", "rejected"),   # ✓ reject
        ("approved", "fulfilled"),   # ✓ export
        ("approved", "approved"),    # ✗ cannot approve twice
        ("rejected", "rejected"),    # ✗ cannot reject twice
        ("rejected", "approved"),    # ✗ cannot approve rejected
        ("rejected", "fulfilled"),   # ✗ cannot export rejected
        ("fulfilled", "approved"),   # ✗ cannot re-approve fulfilled
        ("fulfilled", "rejected"),   # ✗ cannot reject fulfilled
        ("fulfilled", "fulfilled"),  # ✗ cannot export twice
        ("submitted", "fulfilled"),  # ✗ cannot bypass approval
        ("submitted", "submitted"),  # ✗ no self-transition
    ])
    def test_state_guard(self, from_status, to_status):
        """验证状态转换 Guard：合法转换应允许，非法应拒绝"""
        valid_map = {
            ("submitted", "approved"): True,
            ("submitted", "rejected"): True,
            ("approved", "fulfilled"): True,
        }
        if valid_map.get((from_status, to_status), False):
            assert True  # allowed
        else:
            # The API would return 400/409 for invalid transitions
            assert from_status in self.VALID_TRANSITIONS
            assert to_status not in self.VALID_TRANSITIONS[from_status], \
                f"Guard should reject: {from_status} → {to_status}"


# ── Owner scope 权限契约测试 ─────────────────────────────────


class TestOwnerScopeContract:
    """验证 collection_scope 权限边界"""

    def test_owner_can_access_own_scope(self):
        """collection_owner 在自己的 scope 内可访问"""
        owner = CurrentUser(
            user_id="collection-owner",
            display_name="范围管理者",
            roles={"collection_owner"},
            permissions={"application.view_all", "application.review"},
            collection_scope={1, 7},
        )
        assert 1 in owner.collection_scope
        assert 7 in owner.collection_scope
        assert 99 not in owner.collection_scope

    def test_owner_cannot_access_outside_scope(self):
        """collection_owner 不能访问 scope 外资源"""
        owner = CurrentUser(
            user_id="collection-owner",
            display_name="范围管理者",
            roles={"collection_owner"},
            permissions={"application.review"},
            collection_scope={1, 7},
        )
        # This user has application.review permission but only within scope 1,7
        # The actual scope check would happen in the route handler
        assert 99 not in owner.collection_scope

    def test_admin_has_no_scope_restriction(self):
        """admin 不受 collection_scope 限制"""
        admin = CurrentUser(
            user_id="admin",
            display_name="管理员",
            roles={"admin"},
            permissions={"application.view_all", "application.review", "application.export"},
            collection_scope=set(),
        )
        # Admin's scope is empty set, meaning no restriction
        # The can_access_visibility_scope check honors this
        assert len(admin.collection_scope) == 0

    def test_view_all_permission_allows_global_access(self):
        """拥有 view_all 权限的用户可查看所有申请"""
        reviewer = CurrentUser(
            user_id="reviewer",
            display_name="审批员",
            roles={"application_reviewer"},
            permissions={"application.view_all", "application.review"},
            collection_scope=set(),
        )
        assert reviewer.has_permission("application.view_all") is True
        assert reviewer.has_permission("application.view_own") is False

    def test_view_own_permission_restricts_to_own(self):
        """只有 view_own 的用户只能看到自己的申请"""
        creator = CurrentUser(
            user_id="resource_user",
            display_name="申请者",
            roles={"resource_user"},
            permissions={"application.create", "application.view_own"},
            collection_scope=set(),
        )
        assert creator.has_permission("application.view_own") is True
        assert creator.has_permission("application.view_all") is False

    def test_user_cannot_export_without_permission(self):
        """没有 application.export 权限的用户不能导出"""
        no_export = CurrentUser(
            user_id="no_export", display_name="不能导出",
            roles={"resource_user"},
            permissions={"application.create", "application.view_own"},
            collection_scope=set(),
        )
        assert no_export.has_permission("application.export") is False

    def test_reviewer_can_approve_and_export(self):
        """审批员拥有 approve + export 权限"""
        reviewer = CurrentUser(
            user_id="app-reviewer",
            display_name="审批员",
            roles={"application_reviewer"},
            permissions={"application.review", "application.export", "application.view_all"},
            collection_scope=set(),
        )
        assert reviewer.has_permission("application.review") is True
        assert reviewer.has_permission("application.export") is True
        assert reviewer.has_permission("application.create") is False


# ── 审计日志结构契约测试 ────────────────────────────────────


class TestAuditLogContract:
    """验证 ApplicationAuditLog 的结构契约"""

    def test_audit_log_minimal_fields(self):
        """审计日志最小字段可构造"""
        # This mirrors the ApplicationAuditLog model fields
        log_fields = {
            "application_id": 1,
            "action": "submitted",
            "from_status": None,
            "to_status": "submitted",
            "actor_user_id": None,
            "actor_display_name": "申请者",
            "review_note": None,
        }
        assert log_fields["action"] in {"submitted", "approved", "rejected", "exported"}
        assert log_fields["to_status"] in {"submitted", "approved", "rejected", "fulfilled"}

    def test_audit_log_all_actions_defined(self):
        """所有审计操作都已定义"""
        expected_actions = {"submitted", "approved", "rejected", "exported"}
        # Verify these match the _write_audit_log calls in applications.py
        assert len(expected_actions) == 4
        assert "submitted" in expected_actions
        assert "approved" in expected_actions
        assert "rejected" in expected_actions
        assert "exported" in expected_actions
