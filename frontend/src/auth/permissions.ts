export type MenuKey = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';

export type RoleName =
  | 'image_structured_editor'
  | 'image_ingest_operator'
  | 'image_ingest_reviewer'
  | 'image_resource_manager'
  | 'image_metadata_entry'
  | 'image_photographer_upload'
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
  | 'image.record.create'
  | 'image.record.view'
  | 'image.record.edit'
  | 'image.record.submit'
  | 'image.record.return'
  | 'image.record.list'
  | 'image.record.view_ready_for_upload'
  | 'image.file.upload'
  | 'image.file.match'
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
  id: number;
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
  image_structured_editor: '二维结构化编辑员',
  image_ingest_operator: '二维入库操作员',
  image_ingest_reviewer: '二维入库审核员',
  image_resource_manager: '二维资源管理员',
  image_metadata_entry: '影像元数据录入员',
  image_photographer_upload: '摄影上传人员',
  three_d_operator: '三维操作员',
  application_reviewer: '申请审核员',
  collection_owner: '馆藏责任人',
  resource_user: '资源使用者',
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
  '9': ['image.record.list', 'image.record.view_ready_for_upload'],
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
