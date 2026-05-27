import type { MenuKey } from '../auth/permissions';
import type { AssetSummary } from '../types/assets';

export const MENU_LABELS: Record<MenuKey, string> = {
  '1': '总览',
  '2': '二维资源',
  '3': '申请车',
  '4': '入库处理',
  '5': '统一资源目录',
  '6': '统一资源详情',
  '7': '三维管理',
  '8': '申请管理',
  '9': '影像信息录入',
};

const ASSET_STATUS_LABELS: Record<string, string> = {
  ready: '就绪',
  processing: '处理中',
  error: '异常',
};

const AUTH_MODE_LABELS: Record<string, string> = {
  session: '会话认证',
  fallback: '回退认证',
  'legacy-header': '兼容请求头认证',
};

export const getAssetStatusLabel = (status: string) => ASSET_STATUS_LABELS[status] || status || '-';

export const getAuthModeLabel = (mode?: string | null) => {
  if (!mode) return '-';
  return AUTH_MODE_LABELS[mode] || mode;
};

export const buildPreviewUrl = (record: AssetSummary) => {
  const version = encodeURIComponent(`${record.created_at}-${record.file_size}`);
  return `/api/assets/${record.id}/preview?v=${version}`;
};
