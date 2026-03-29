export type MenuKey = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8';

export type RoleName =
  | 'image_structured_editor'
  | 'image_ingest_operator'
  | 'image_ingest_reviewer'
  | 'image_resource_manager'
  | 'three_d_operator'
  | 'application_reviewer'
  | 'collection_owner'
  | 'resource_user'
  | 'system_admin';

export type PermissionName =
  | 'dashboard.view'
  | 'image.view'
  | 'image.edit'
  | 'image.delete'
  | 'image.upload'
  | 'image.ingest_review'
  | 'three_d.view'
  | 'three_d.edit'
  | 'three_d.upload'
  | 'platform.view'
  | 'application.create'
  | 'application.view_own'
  | 'application.view_all'
  | 'application.review'
  | 'application.export'
  | 'system.manage';

export interface AuthRoleSummary {
  key: string;
  label: string;
}

export interface AuthUserSummary {
  username: string;
  display_name: string;
  roles: AuthRoleSummary[];
  collection_scope: number[];
}

export interface AuthContext {
  user_id: string;
  display_name: string;
  roles: string[];
  permissions: string[];
  collection_scope: number[];
  auth_mode: string;
}

export interface AuthLoginResponse {
  token: string;
  user: AuthContext;
}

export const ROLE_LABELS: Record<RoleName, string> = {
  image_structured_editor: '二维结构化录入',
  image_ingest_operator: '二维非结构化处理',
  image_ingest_reviewer: '二维入库审核',
  image_resource_manager: '二维资源管理',
  three_d_operator: '三维处理上传',
  application_reviewer: '申请审批',
  collection_owner: '藏品管理者',
  resource_user: '数据浏览与申请',
  system_admin: '系统管理员',
};

export const MENU_PERMISSION_RULES: Record<MenuKey, PermissionName[]> = {
  '1': ['dashboard.view'],
  '2': ['image.view'],
  '3': ['application.create'],
  '4': ['image.upload', 'image.ingest_review', 'image.edit'],
  '5': ['platform.view'],
  '6': ['platform.view'],
  '7': ['three_d.view'],
  '8': ['application.view_all', 'application.review', 'application.export'],
};

export function canAccessMenu(auth: AuthContext, menuKey: MenuKey): boolean {
  return MENU_PERMISSION_RULES[menuKey].some((permission) => auth.permissions.includes(permission));
}

export function getVisibleMenuKeys(auth: AuthContext): MenuKey[] {
  return (Object.keys(MENU_PERMISSION_RULES) as MenuKey[]).filter((key) => canAccessMenu(auth, key));
}

export function can(auth: AuthContext, permission: PermissionName): boolean {
  return auth.permissions.includes(permission);
}

export function getRoleLabels(auth: AuthContext): string[] {
  return auth.roles.map((role) => ROLE_LABELS[role as RoleName] || role);
}
