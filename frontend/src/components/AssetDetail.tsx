import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Descriptions, Divider, List, Space, Spin, Tag, Typography } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import axios from 'axios';
import type {
  AssetDetailFileRecord,
  AssetDetailResponse,
  AssetDetailTimelineItem,
  AssetMetadataLayers,
  AssetTechnicalMetadata,
  LifecycleEntry,
} from '../types/assets';

const { Paragraph, Text } = Typography;

interface AssetDetailProps {
  assetId: number;
  onBack: () => void;
  onPreview?: (manifestUrl: string) => void;
}

const statusColorMap: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const timelineColorMap: Record<string, string> = {
  done: 'green',
  pending: 'blue',
  error: 'red',
};

const formatBytes = (value?: number | null) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} bytes`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const metadataLabelMap: Record<string, string> = {
  resource_id: 'Resource ID',
  source_system: 'Source System',
  source_label: 'Source Label',
  resource_type: 'Resource Type',
  resource_type_label: 'Resource Type Label',
  visibility_scope: 'Visibility Scope',
  collection_object_id: 'Collection Object ID',
  title: 'Title',
  status: 'Status',
  preview_enabled: 'Preview Enabled',
  profile_key: 'Profile Key',
  profile_label: 'Profile Label',
  profile_sheet: 'Profile Sheet',
  created_at: 'Created At',
  project_type: 'Project Type',
  project_name: 'Project Name',
  photographer: 'Photographer',
  photographer_org: 'Photographer Org',
  copyright_owner: 'Copyright Owner',
  capture_time: 'Capture Time',
  image_category: 'Image Category',
  image_name: 'Image Name',
  capture_content: 'Capture Content',
  representative_image: 'Representative Image',
  remark: 'Remark',
  tags: 'Tags',
  record_account: 'Record Account',
  record_time: 'Record Time',
  image_record_time: 'Image Record Time',
  original_file_name: 'Original File Name',
  image_file_name: 'Image File Name',
  identifier_type: 'Identifier Type',
  identifier_value: 'Identifier Value',
  file_size: 'File Size',
  format_name: 'Format Name',
  format_version: 'Format Version',
  registry_name: 'Registry Name',
  registry_item: 'Registry Item',
  byte_order: 'Byte Order',
  checksum_algorithm: 'Checksum Algorithm',
  checksum: 'Checksum',
  checksum_generator: 'Checksum Generator',
  width: 'Width',
  height: 'Height',
  color_space: 'Color Space',
  ingest_method: 'Ingest Method',
  fixity_sha256: 'SHA256',
  conversion_method: 'Conversion Method',
  original_file_path: 'Original File Path',
  original_file_size: 'Original File Size',
  original_mime_type: 'Original MIME Type',
  error_message: 'Error Message',
  object_number: 'Object Number',
  object_name: 'Object Name',
  object_level: 'Object Level',
  object_category: 'Object Category',
  object_subcategory: 'Object Subcategory',
  management_group: 'Management Group',
  photographer_phone: 'Photographer Phone',
  visible_to_custodians_only: 'Visible To Custodians Only',
  region_level_1: 'Region Level 1',
  region_level_2: 'Region Level 2',
  building_name: 'Building Name',
  orientation: 'Orientation',
  part_level_1: 'Part Level 1',
  part_level_2: 'Part Level 2',
  part_level_3: 'Part Level 3',
  building_component: 'Building Component',
  art_photography_type: 'Art Photography Type',
  collection_type: 'Collection Type',
  palace_area: 'Palace Area',
  season: 'Season',
  plant: 'Plant',
  animal: 'Animal',
  solar_term: 'Solar Term',
  other: 'Other',
  theme: 'Theme',
  cultural_topic: 'Cultural Topic',
  exhibition_topic: 'Exhibition Topic',
  main_location: 'Main Location',
  main_person: 'Main Person',
  panorama_type: 'Panorama Type',
  location: 'Location',
  archive_number: 'Archive Number',
  plant_type: 'Plant Type',
  plant_name: 'Plant Name',
  region: 'Region',
  specific_location: 'Specific Location',
  grade: 'Grade',
  archaeology_image_category: 'Archaeology Image Category',
};

const renderMetadataValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (Array.isArray(value)) return value.map((item) => String(item)).join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

const renderMetadataSection = (section?: Record<string, unknown> | null) => {
  if (!section || Object.keys(section).length === 0) {
    return null;
  }

  return (
    <Descriptions bordered column={1} size="small">
      {Object.entries(section).map(([key, value]) => (
        <Descriptions.Item key={key} label={metadataLabelMap[key] || key}>
          {renderMetadataValue(value)}
        </Descriptions.Item>
      ))}
    </Descriptions>
  );
};

const renderFileRecord = (record: AssetDetailFileRecord, fallbackTitle: string) => (
  <Descriptions bordered column={1} size="small">
    <Descriptions.Item label="Role">{record.role_label || record.role || '-'}</Descriptions.Item>
    <Descriptions.Item label="File Name">{record.filename || '-'}</Descriptions.Item>
    <Descriptions.Item label="Actual File">{record.actual_filename || record.filename || '-'}</Descriptions.Item>
    <Descriptions.Item label="MIME Type">{record.mime_type || '-'}</Descriptions.Item>
    <Descriptions.Item label="File Size">{formatBytes(record.file_size)}</Descriptions.Item>
    <Descriptions.Item label="File Path">
      {record.file_path ? <Paragraph copyable style={{ marginBottom: 0 }}>{record.file_path}</Paragraph> : '-'}
    </Descriptions.Item>
    <Descriptions.Item label="Current">{record.is_current ? 'Yes' : 'No'}</Descriptions.Item>
    <Descriptions.Item label="Original">{record.is_original ? 'Yes' : 'No'}</Descriptions.Item>
    <Descriptions.Item label="Fallback Title">{fallbackTitle}</Descriptions.Item>
    {record.same_as_primary !== undefined && (
      <Descriptions.Item label="Same As Primary">{record.same_as_primary ? 'Yes' : 'No'}</Descriptions.Item>
    )}
    {record.derivation_method && (
      <Descriptions.Item label="Derivation Method">{record.derivation_method}</Descriptions.Item>
    )}
  </Descriptions>
);

const renderLifecycleItem = (item: LifecycleEntry) => (
  <List.Item>
    <Space direction="vertical" size="small" style={{ width: '100%' }}>
      <Space wrap>
        <Text strong>{item.label}</Text>
        <Tag color={timelineColorMap[item.status] || 'default'}>{item.status_label}</Tag>
      </Space>
      <Text type="secondary">{item.description}</Text>
      {item.timestamp && <Text type="secondary">Timestamp: {item.timestamp}</Text>}
      {item.evidence && <Text type="secondary">Evidence: {item.evidence}</Text>}
    </Space>
  </List.Item>
);

const AssetDetail: React.FC<AssetDetailProps> = ({ assetId, onBack, onPreview }) => {
  const [detail, setDetail] = useState<AssetDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await axios.get<AssetDetailResponse>(`/api/assets/${assetId}`);
      setDetail(res.data);
      setError(null);
    } catch (err: unknown) {
      console.error(err);
      if (axios.isAxiosError(err)) {
        const detailMessage = err.response?.data && typeof err.response.data === 'object'
          ? (err.response.data as { detail?: string }).detail
          : undefined;
        setError(detailMessage || 'Failed to load asset detail');
      } else {
        setError('Failed to load asset detail');
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }, [assetId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  useEffect(() => {
    if (!detail || detail.status !== 'processing') return;
    const timer = setInterval(() => fetchDetail(true), 3000);
    return () => clearInterval(timer);
  }, [detail, fetchDetail]);

  const previewEnabled = useMemo(
    () => Boolean(detail?.access_paths.preview_enabled ?? detail?.access.preview_enabled),
    [detail],
  );
  const manifestUrl = useMemo(
    () => detail?.access_paths.manifest?.url || detail?.access.manifest_url,
    [detail],
  );

  if (loading) return <Spin tip="Loading asset detail..." />;

  if (error) {
    return (
      <Card>
        <Alert type="error" message="Load failed" description={error} />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>Back</Button>
        </div>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card>
        <Alert type="warning" message="No detail available" />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>Back</Button>
        </div>
      </Card>
    );
  }

  const technicalMetadata: AssetTechnicalMetadata = detail.technical_metadata || {};
  const metadataLayers: AssetMetadataLayers | undefined = detail.metadata_layers;
  const statusInfo = detail.status_info;
  const structure = detail.structure;
  const primaryFile = structure.primary_file;
  const originalFile = structure.original_file;
  const derivatives = structure.derivatives || [];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        title="Asset Detail"
        extra={<Button icon={<ArrowLeftOutlined />} onClick={onBack}>Back</Button>}
      >
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Title">{detail.title}</Descriptions.Item>
          <Descriptions.Item label="Identifier">
            <Paragraph copyable style={{ marginBottom: 0 }}>{detail.identifier}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="Resource Type">{detail.resource_type_label}</Descriptions.Item>
          <Descriptions.Item label="Visibility Scope">{detail.visibility_scope}</Descriptions.Item>
          <Descriptions.Item label="Collection Object ID">{detail.collection_object_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={statusColorMap[statusInfo.code] || 'default'}>{statusInfo.label}</Tag>
            {statusInfo.message && <Text style={{ marginLeft: 8 }}>{statusInfo.message}</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="Created At">{detail.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Lifecycle Events">
        <List bordered dataSource={detail.lifecycle} renderItem={renderLifecycleItem} />
      </Card>

      <Card title="Process Timeline">
        {detail.process_timeline.length > 0 ? (
          <List
            bordered
            dataSource={detail.process_timeline}
            renderItem={(item: AssetDetailTimelineItem) => (
              <List.Item>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space wrap>
                    <Text strong>{item.label || item.step}</Text>
                    <Tag color={timelineColorMap[item.status || ''] || 'default'}>
                      {item.status_label || item.status}
                    </Tag>
                  </Space>
                  <Text type="secondary">{item.description || '-'}</Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Alert type="warning" showIcon message="No process timeline available" />
        )}
      </Card>

      <Card title="Structure and Files">
        <Alert type="info" showIcon message={structure.summary || 'No structure summary'} />

        <Divider orientation="left">Primary File</Divider>
        {renderFileRecord(primaryFile, detail.title)}

        <Divider orientation="left">Original File</Divider>
        {renderFileRecord(originalFile, detail.title)}

        <Divider orientation="left">Derivative Files</Divider>
        {derivatives.length > 0 ? (
          <List
            bordered
            dataSource={derivatives}
            renderItem={(item: AssetDetailFileRecord) => (
              <List.Item>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text strong>{item.role_label || item.role || '-'}</Text>
                  <Text>File Name: {item.filename || '-'}</Text>
                  <Text>MIME Type: {item.mime_type || '-'}</Text>
                  <Text>File Size: {formatBytes(item.file_size)}</Text>
                  <Text>Derivation Method: {item.derivation_method || '-'}</Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Alert type="warning" showIcon message="No derivative files available" />
        )}

        <Divider orientation="left">Packaging</Divider>
        <Alert
          type={structure.packaging?.bagit_supported ? 'success' : 'info'}
          showIcon
          message={structure.packaging?.bagit_note || 'BagIt output not specified'}
        />
      </Card>

      <Card title="Technical Metadata">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Width">{technicalMetadata.width ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Height">{technicalMetadata.height ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="SHA256">
            {technicalMetadata.fixity_sha256 ? (
              <Paragraph copyable code style={{ marginBottom: 0 }}>{technicalMetadata.fixity_sha256}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Ingest Method">{technicalMetadata.ingest_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Conversion Method">{technicalMetadata.conversion_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Original File Path">{technicalMetadata.original_file_path ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Error Message">{technicalMetadata.error_message ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {metadataLayers && (
        <Card title="Layered Metadata">
          <Alert
            type="info"
            showIcon
            message={`schema ${metadataLayers.schema_version || 'unknown'} / ${metadataLayers.profile?.label || 'unknown profile'}`}
            style={{ marginBottom: 16 }}
          />

          {metadataLayers.core && Object.keys(metadataLayers.core).length > 0 && (
            <>
              <Divider orientation="left">Platform Core</Divider>
              {renderMetadataSection(metadataLayers.core)}
            </>
          )}

          {metadataLayers.management && Object.keys(metadataLayers.management).length > 0 && (
            <>
              <Divider orientation="left">Shared Management Metadata</Divider>
              {renderMetadataSection(metadataLayers.management)}
            </>
          )}

          {metadataLayers.technical && Object.keys(metadataLayers.technical).length > 0 && (
            <>
              <Divider orientation="left">Technical Image Metadata</Divider>
              {renderMetadataSection(metadataLayers.technical)}
            </>
          )}

          {metadataLayers.profile?.fields && Object.keys(metadataLayers.profile.fields).length > 0 && (
            <>
              <Divider orientation="left">Profile Metadata</Divider>
              {renderMetadataSection(metadataLayers.profile.fields)}
            </>
          )}

          {metadataLayers.raw_metadata && Object.keys(metadataLayers.raw_metadata).length > 0 && (
            <>
              <Divider orientation="left">Raw Metadata</Divider>
              <pre style={{ maxHeight: 320, overflow: 'auto', fontSize: 12, marginBottom: 0 }}>
                {JSON.stringify(metadataLayers.raw_metadata, null, 2)}
              </pre>
            </>
          )}
        </Card>
      )}

      <Card title="Access and Outputs">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Manifest">
            {manifestUrl ? <Paragraph copyable style={{ marginBottom: 0 }}>{manifestUrl}</Paragraph> : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Preview Status">{previewEnabled ? 'Enabled' : 'Disabled'}</Descriptions.Item>
          <Descriptions.Item label="Current File Download">
            {detail.output_actions.download_current_file?.url ? (
              <Paragraph copyable style={{ marginBottom: 0 }}>{detail.output_actions.download_current_file.url}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="BagIt Download">
            {detail.output_actions.download_bag?.url ? (
              <Paragraph copyable style={{ marginBottom: 0 }}>{detail.output_actions.download_bag.url}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <Space wrap>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            disabled={!previewEnabled || !manifestUrl}
            onClick={() => onPreview && manifestUrl && onPreview(manifestUrl)}
          >
            Open Mirador
          </Button>
          <Button
            icon={<LinkOutlined />}
            disabled={!manifestUrl}
            onClick={() => manifestUrl && window.open(manifestUrl, '_blank', 'noopener,noreferrer')}
          >
            View IIIF Manifest
          </Button>
          <Button
            icon={<DownloadOutlined />}
            disabled={!detail.output_actions.download_current_file?.url}
            onClick={() => {
              if (detail.output_actions.download_current_file?.url) {
                window.location.href = detail.output_actions.download_current_file.url;
              }
            }}
          >
            Download Current File
          </Button>
          <Button
            icon={<DownloadOutlined />}
            disabled={!detail.output_actions.download_bag?.url}
            onClick={() => {
              if (detail.output_actions.download_bag?.url) {
                window.location.href = detail.output_actions.download_bag.url;
              }
            }}
          >
            Download BagIt Package
          </Button>
        </Space>
      </Card>
    </Space>
  );
};

export default AssetDetail;
