import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Descriptions, Input, Select, Space, Table, Tag, Typography } from 'antd';
import { EyeOutlined, FileTextOutlined, LinkOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import type { UnifiedResourceSourceSummary, UnifiedResourceSummary } from '../types/assets';

const { Paragraph, Text } = Typography;
const { Search } = Input;

const PROFILE_OPTIONS = [
  { value: 'other', label: 'Other' },
  { value: 'movable_artifact', label: 'Movable Artifact' },
  { value: 'immovable_artifact', label: 'Immovable Artifact' },
  { value: 'art_photography', label: 'Art Photography' },
  { value: 'business_activity', label: 'Business Activity' },
  { value: 'panorama', label: 'Panorama' },
  { value: 'ancient_tree', label: 'Ancient Tree' },
  { value: 'archaeology', label: 'Archaeology' },
  { value: 'model', label: '3D Model' },
  { value: 'point_cloud', label: 'Point Cloud' },
  { value: 'oblique_photo', label: 'Oblique Photo' },
  { value: 'package', label: '3D Package' },
];

interface PlatformDirectoryProps {
  onPreview: (manifestUrl: string) => void;
  onOpenAssetDetail?: (assetId: number) => void;
  onOpenUnifiedResourceDetail?: (resourceId: string) => void;
}

const PlatformDirectory: React.FC<PlatformDirectoryProps> = ({
  onPreview,
  onOpenAssetDetail,
  onOpenUnifiedResourceDetail,
}) => {
  const [sources, setSources] = useState<UnifiedResourceSourceSummary[]>([]);
  const [resources, setResources] = useState<UnifiedResourceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<string | undefined>();
  const [previewState, setPreviewState] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [profileKey, setProfileKey] = useState<string | undefined>();

  const fetchDirectory = async (
    nextQuery = query,
    nextStatus = status,
    nextPreview = previewState,
    nextResourceType = resourceType,
    nextProfileKey = profileKey,
  ) => {
    setLoading(true);
    try {
      const params: Record<string, string | boolean> = {};
      if (nextQuery.trim()) params.q = nextQuery.trim();
      if (nextStatus) params.status = nextStatus;
      if (nextPreview === 'true') params.preview_enabled = true;
      if (nextPreview === 'false') params.preview_enabled = false;
      if (nextResourceType) params.resource_type = nextResourceType;
      if (nextProfileKey) params.profile_key = nextProfileKey;

      const [sourcesRes, resourcesRes] = await Promise.all([
        axios.get<UnifiedResourceSourceSummary[]>('/api/platform/sources'),
        axios.get<UnifiedResourceSummary[]>('/api/platform/resources', { params }),
      ]);
      setSources(sourcesRes.data);
      setResources(resourcesRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchDirectory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = useMemo(
    () => [
      {
        title: 'Unified ID',
        dataIndex: 'id',
        key: 'id',
        render: (value: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{value}</Paragraph>,
      },
      { title: 'Source', dataIndex: 'source_label', key: 'source_label' },
      { title: 'Title', dataIndex: 'title', key: 'title' },
      { title: 'Resource Type', dataIndex: 'resource_type', key: 'resource_type' },
      {
        title: 'Profile',
        dataIndex: 'profile_label',
        key: 'profile_label',
        render: (value: string | undefined, record: UnifiedResourceSummary) => (
          <Tag>{value || record.profile_key || 'Other'}</Tag>
        ),
      },
      {
        title: 'Status',
        dataIndex: 'status',
        key: 'status',
        render: (value: string, record: UnifiedResourceSummary) => (
          <Space wrap>
            <Tag color={record.preview_enabled ? 'green' : 'blue'}>
              {record.preview_enabled ? 'Previewable' : 'Download only'}
            </Tag>
            <Tag>{value}</Tag>
          </Space>
        ),
      },
      {
        title: 'Updated At',
        dataIndex: 'updated_at',
        key: 'updated_at',
        render: (value: string) => <Text type="secondary">{value}</Text>,
      },
      {
        title: 'Actions',
        key: 'action',
        render: (_value: unknown, record: UnifiedResourceSummary) => (
          <Space wrap>
            <Button
              data-testid={`platform-preview-${record.source_id}`}
              icon={<EyeOutlined />}
              disabled={!record.preview_enabled}
              onClick={() => onPreview(record.manifest_url)}
            >
              Preview
            </Button>
            <Button
              data-testid={`platform-unified-detail-${record.source_id}`}
              icon={<LinkOutlined />}
              onClick={() => onOpenUnifiedResourceDetail?.(record.id)}
            >
              Unified Detail
            </Button>
            <Button
              data-testid={`platform-source-detail-${record.source_id}`}
              icon={<FileTextOutlined />}
              onClick={() => {
                const assetId = Number(record.source_id);
                if (!Number.isNaN(assetId) && onOpenAssetDetail) {
                  onOpenAssetDetail(assetId);
                }
              }}
            >
              Source Detail
            </Button>
          </Space>
        ),
      },
    ],
    [onOpenAssetDetail, onOpenUnifiedResourceDetail, onPreview],
  );

  return (
    <Space data-testid="platform-directory" direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="Unified Resource Directory">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Space wrap style={{ width: '100%' }}>
            <Search
              data-testid="platform-search"
              allowClear
              placeholder="Search title, filename, MIME or resource ID"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onSearch={(value) => void fetchDirectory(value, status, previewState, resourceType, profileKey)}
              style={{ width: 320 }}
            />
            <Select
              allowClear
              placeholder="Status"
              value={status}
              onChange={(value) => {
                setStatus(value);
                void fetchDirectory(query, value, previewState, resourceType, profileKey);
              }}
              style={{ width: 160 }}
              options={[
                { value: 'ready', label: 'ready' },
                { value: 'processing', label: 'processing' },
                { value: 'error', label: 'error' },
              ]}
            />
            <Select
              allowClear
              placeholder="Preview"
              value={previewState}
              onChange={(value) => {
                setPreviewState(value);
                void fetchDirectory(query, status, value, resourceType, profileKey);
              }}
              style={{ width: 160 }}
              options={[
                { value: 'true', label: 'Previewable' },
                { value: 'false', label: 'Download only' },
              ]}
            />
            <Select
              allowClear
              placeholder="Resource Type"
              value={resourceType}
              onChange={(value) => {
                setResourceType(value);
                void fetchDirectory(query, status, previewState, value, profileKey);
              }}
              style={{ width: 240 }}
              options={[
                { value: 'image_2d_cultural_object', label: '2D Image' },
                { value: 'three_d_model', label: '3D Model' },
                { value: 'three_d_point_cloud', label: 'Point Cloud' },
                { value: 'three_d_oblique_photo', label: 'Oblique Photo' },
                { value: 'three_d_package', label: '3D Package' },
              ]}
            />
            <Select
              allowClear
              placeholder="Profile"
              value={profileKey}
              onChange={(value) => {
                setProfileKey(value);
                void fetchDirectory(query, status, previewState, resourceType, value);
              }}
              style={{ width: 180 }}
              options={PROFILE_OPTIONS}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void fetchDirectory()} />
          </Space>

          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Source Count">{sources.length}</Descriptions.Item>
            <Descriptions.Item label="Resource Count">{resources.length}</Descriptions.Item>
          </Descriptions>
        </Space>

        <Alert
          style={{ marginTop: 16 }}
          type="info"
          showIcon
          message="The unified directory aggregates multiple subsystem sources and provides a single search and detail entry."
        />
      </Card>

      <Card title="Source Summary">
        <Descriptions bordered column={1} size="small">
          {sources.map((source) => (
            <Descriptions.Item key={source.source_system} label={source.source_label}>
              <Space direction="vertical" size={0}>
                <Text>System ID: {source.source_system}</Text>
                <Text>Resource Type: {source.resource_type}</Text>
                <Text>Resource Count: {source.resource_count}</Text>
                <Text>Entrypoint: {source.entrypoint}</Text>
                <Text>Healthy: {source.healthy ? 'Yes' : 'No'}</Text>
              </Space>
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>

      <Card title="Unified Resource List">
        <Table
          rowKey="id"
          loading={loading}
          dataSource={resources}
          columns={columns}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </Space>
  );
};

export default PlatformDirectory;
