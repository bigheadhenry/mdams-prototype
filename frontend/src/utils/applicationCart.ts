import type { ApplicationCartItem, UnifiedResourceDetail, UnifiedResourceSummary } from '../types/assets';

type UnifiedApplicationResource = UnifiedResourceSummary | UnifiedResourceDetail;

export const buildApplicationCartItemFromUnifiedResource = (
  resource: UnifiedApplicationResource,
): ApplicationCartItem => ({
  cartKey: resource.id,
  assetId:
    resource.source_system === 'image_2d' && Number.isFinite(Number(resource.source_id))
      ? Number(resource.source_id)
      : null,
  sourceSystem: resource.source_system,
  sourceId: resource.source_id,
  resourceType: resource.resource_type,
  title: resource.title,
  manifestUrl: resource.manifest_url,
  sourceLabel: resource.source_label,
  objectNumber: resource.source_id,
  era: resource.era || null,
  objectLevel: resource.object_level || null,
  canSubmit: true,
});
