import { describe, it, expect } from 'vitest';
import {
  canAccessMenu,
  getVisibleMenuKeys,
  can,
  getRoleLabels,
  ROLE_LABELS,
  type AuthContext,
} from '../permissions';

const adminAuth: AuthContext = {
  user_id: 'admin',
  display_name: 'Admin',
  roles: ['system_admin'],
  permissions: [
    'dashboard.view', 'image.view', 'image.edit', 'image.delete',
    'image.upload', 'image.ingest_review', 'image.record.create',
    'image.record.view', 'image.record.edit', 'image.record.submit',
    'image.record.return', 'image.record.list', 'image.record.view_ready_for_upload',
    'image.file.upload', 'image.file.match', 'three_d.view', 'three_d.edit',
    'three_d.upload', 'platform.view', 'application.create', 'application.view_own',
    'application.view_all', 'application.review', 'application.export', 'system.manage',
  ],
  collection_scope: [],
  auth_mode: 'session',
};

const viewerAuth: AuthContext = {
  user_id: 'viewer',
  display_name: 'Viewer',
  roles: ['resource_user'],
  permissions: ['platform.view', 'application.create'],
  collection_scope: [],
  auth_mode: 'session',
};

describe('can', () => {
  it('returns true when user has the permission', () => {
    expect(can(adminAuth, 'dashboard.view')).toBe(true);
  });

  it('returns false when user lacks the permission', () => {
    expect(can(viewerAuth, 'image.edit')).toBe(false);
  });

  it('returns false for empty permissions', () => {
    const emptyAuth: AuthContext = {
      user_id: 'none', display_name: 'None', roles: [],
      permissions: [], collection_scope: [], auth_mode: 'session',
    };
    expect(can(emptyAuth, 'dashboard.view')).toBe(false);
  });
});

describe('canAccessMenu', () => {
  it('admin can access all menus', () => {
    expect(canAccessMenu(adminAuth, '1')).toBe(true);  // dashboard
    expect(canAccessMenu(adminAuth, '2')).toBe(true);  // images
    expect(canAccessMenu(adminAuth, '7')).toBe(true);  // 3d
  });

  it('viewer can access platform and application menus', () => {
    expect(canAccessMenu(viewerAuth, '5')).toBe(true);   // platform
    expect(canAccessMenu(viewerAuth, '3')).toBe(true);   // application cart
    expect(canAccessMenu(viewerAuth, '2')).toBe(false);  // image management
    expect(canAccessMenu(viewerAuth, '7')).toBe(false);  // 3d
  });

  it('menu 6 (empty rule) is inaccessible to everyone', () => {
    expect(canAccessMenu(adminAuth, '6')).toBe(false);
    expect(canAccessMenu(viewerAuth, '6')).toBe(false);
  });
});

describe('getVisibleMenuKeys', () => {
  it('admin sees all menus (except empty-rule menu 6)', () => {
    const keys = getVisibleMenuKeys(adminAuth);
    expect(keys).toContain('1');
    expect(keys).toContain('2');
    expect(keys).toContain('7');
    expect(keys).not.toContain('6');
  });

  it('resource_user sees only platform + application (role override)', () => {
    const keys = getVisibleMenuKeys(viewerAuth);
    expect(keys).toEqual(['5', '3']);
  });
});

describe('getRoleLabels', () => {
  it('returns Chinese labels for known roles', () => {
    const labels = getRoleLabels(adminAuth);
    expect(labels).toContain('系统管理员');
  });

  it('returns original key for unknown roles', () => {
    const unknownAuth: AuthContext = {
      user_id: 'x', display_name: 'X', roles: ['unknown_role'],
      permissions: [], collection_scope: [], auth_mode: 'session',
    };
    const labels = getRoleLabels(unknownAuth);
    expect(labels).toEqual(['unknown_role']);
  });
});

describe('ROLE_LABELS', () => {
  it('has all expected role labels', () => {
    expect(ROLE_LABELS.system_admin).toBe('系统管理员');
    expect(ROLE_LABELS.resource_user).toBe('资源使用者');
    expect(ROLE_LABELS.collection_owner).toBe('馆藏责任人');
  });
});
