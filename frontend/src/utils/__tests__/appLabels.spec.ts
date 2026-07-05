import { describe, it, expect } from 'vitest';
import {
  MENU_LABELS,
  getAssetStatusLabel,
  getAuthModeLabel,
  buildPreviewUrl,
} from '../appLabels';
import type { AssetSummary } from '../../types/assets';

describe('MENU_LABELS', () => {
  it('returns correct Chinese label for each known menu key', () => {
    expect(MENU_LABELS['1']).toBe('总览');
    expect(MENU_LABELS['2']).toBe('二维资源');
    expect(MENU_LABELS['3']).toBe('申请车');
    expect(MENU_LABELS['4']).toBe('入库处理');
    expect(MENU_LABELS['5']).toBe('统一资源目录');
    expect(MENU_LABELS['6']).toBe('统一资源详情');
    expect(MENU_LABELS['7']).toBe('三维管理');
    expect(MENU_LABELS['8']).toBe('申请管理');
    expect(MENU_LABELS['9']).toBe('影像信息录入');
  });

  it('has all 9 menu entries', () => {
    expect(Object.keys(MENU_LABELS)).toHaveLength(9);
  });
});

describe('getAssetStatusLabel', () => {
  it('returns correct Chinese label for known statuses', () => {
    expect(getAssetStatusLabel('ready')).toBe('就绪');
    expect(getAssetStatusLabel('processing')).toBe('处理中');
    expect(getAssetStatusLabel('error')).toBe('异常');
  });

  it('returns the original string for an unknown status', () => {
    expect(getAssetStatusLabel('unknown_status')).toBe('unknown_status');
    expect(getAssetStatusLabel('pending')).toBe('pending');
  });

  it('returns "-" for empty/undefined-like status', () => {
    expect(getAssetStatusLabel('')).toBe('-');
  });
});

describe('getAuthModeLabel', () => {
  it('returns correct Chinese label for known modes', () => {
    expect(getAuthModeLabel('session')).toBe('会话认证');
    expect(getAuthModeLabel('fallback')).toBe('回退认证');
    expect(getAuthModeLabel('legacy-header')).toBe('兼容请求头认证');
  });

  it('returns the original string for an unknown mode', () => {
    expect(getAuthModeLabel('oauth')).toBe('oauth');
    expect(getAuthModeLabel('jwt')).toBe('jwt');
  });

  it('returns "-" for null or undefined', () => {
    expect(getAuthModeLabel(null)).toBe('-');
    expect(getAuthModeLabel(undefined)).toBe('-');
  });

  it('returns "-" for empty string', () => {
    expect(getAuthModeLabel('')).toBe('-');
  });
});

describe('buildPreviewUrl', () => {
  it('builds preview URL with version hash', () => {
    const record = {
      id: 'abc-123',
      created_at: '2025-06-01T10:00:00Z',
      file_size: 2048576,
    } as AssetSummary;

    const url = buildPreviewUrl(record);
    expect(url).toMatch(/^\/api\/assets\/abc-123\/preview\?v=/);
    expect(url).toContain('2025-06-01T10%3A00%3A00Z'); // encoded colon
    expect(url).toContain('2048576');
  });
});
