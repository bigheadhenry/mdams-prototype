import { describe, it, expect } from 'vitest';
import { buildApplicationCartItemFromUnifiedResource } from '../applicationCart';
import type { UnifiedResourceSummary, UnifiedResourceDetail } from '../../types/assets';

describe('buildApplicationCartItemFromUnifiedResource', () => {
  const baseResource: UnifiedResourceSummary = {
    id: 'res-001',
    source_system: 'image_2d',
    source_id: '12345',
    source_label: 'Museum A',
    title: 'Mona Lisa',
    resource_type: 'image',
    manifest_url: 'https://example.com/manifest/12345',
    status: 'active',
    preview_enabled: true,
    detail_url: 'https://example.com/detail/12345',
    updated_at: '2025-01-01T00:00:00Z',
    profile_key: null,
    profile_label: null,
    thumbnail_url: null,
    preview_data: null,
    era: 'Renaissance',
    object_level: 'high',
    resolution: null,
    format: null,
    main_person: null,
    main_location: null,
  };

  it('builds cart item with assetId for image_2d with valid numeric source_id', () => {
    const item = buildApplicationCartItemFromUnifiedResource(baseResource);
    expect(item).toEqual({
      cartKey: 'res-001',
      assetId: 12345,
      sourceSystem: 'image_2d',
      sourceId: '12345',
      resourceType: 'image',
      title: 'Mona Lisa',
      manifestUrl: 'https://example.com/manifest/12345',
      sourceLabel: 'Museum A',
      objectNumber: '12345',
      era: 'Renaissance',
      objectLevel: 'high',
      canSubmit: true,
    });
  });

  it('sets assetId to null for image_2d with non-numeric source_id', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      source_id: 'not-a-number',
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);
    expect(item.assetId).toBeNull();
    expect(item.cartKey).toBe('res-001');
    expect(item.sourceSystem).toBe('image_2d');
  });

  it('sets assetId to null for non-image_2d source system', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      source_system: 'three_d',
      source_id: 'obj-456',
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);
    expect(item.assetId).toBeNull();
    expect(item.objectNumber).toBe('obj-456');
  });

  it('handles UnifiedResourceDetail with same fields', () => {
    const detail: UnifiedResourceDetail = {
      ...baseResource,
      source_detail_url: 'https://example.com/detail/12345',
      source_record_type: 'asset_detail',
    };
    const item = buildApplicationCartItemFromUnifiedResource(detail);
    expect(item.cartKey).toBe('res-001');
    expect(item.assetId).toBe(12345);
  });

  it('handles null era and objectLevel', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      era: null,
      object_level: null,
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);
    expect(item.era).toBeNull();
    expect(item.objectLevel).toBeNull();
  });

  it('preserves sourceSystem as-is for non-image_2d systems', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      source_system: 'video',
      source_id: 'vid-789',
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);
    expect(item.sourceSystem).toBe('video');
    expect(item.assetId).toBeNull();
  });

  it('maps all remaining fields correctly', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      source_system: 'audio',
      source_id: 'audio-001',
      source_label: 'Audio Archive',
      title: 'Beethoven Symphony No.5',
      resource_type: 'audio',
      manifest_url: 'https://example.com/manifest/audio-001',
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);

    expect(item.cartKey).toBe('res-001');
    expect(item.assetId).toBeNull();
    expect(item.sourceSystem).toBe('audio');
    expect(item.sourceId).toBe('audio-001');
    expect(item.resourceType).toBe('audio');
    expect(item.title).toBe('Beethoven Symphony No.5');
    expect(item.manifestUrl).toBe('https://example.com/manifest/audio-001');
    expect(item.sourceLabel).toBe('Audio Archive');
    expect(item.objectNumber).toBe('audio-001');
    expect(item.canSubmit).toBe(true);
  });

  it('handles image_2d with source_id that is numeric string but also parseable', () => {
    const resource: UnifiedResourceSummary = {
      ...baseResource,
      source_id: '0',
    };
    const item = buildApplicationCartItemFromUnifiedResource(resource);
    expect(item.assetId).toBe(0);
  });
});
