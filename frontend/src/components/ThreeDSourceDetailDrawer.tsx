import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Image,
  message,
  Row,
  Space,
  Table,
  Tabs,
  Tag,
  Timeline,
  Typography,
} from 'antd';
import {
  CopyOutlined,
  DownloadOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import ThreeDViewer from './ThreeDViewer';
import ThreeDTurntablePreview from './ThreeDTurntablePreview';
import type { ThreeDDetailResponse } from '../types/assets';

const { Paragraph, Text } = Typography;

interface ThreeDSourceDetailDrawerProps {
  open: boolean;
  data: ThreeDDetailResponse | null;
  onClose: () => void;
}

const STATUS_COLOR_MAP: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const formatBytes = (value?: number | null) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} 字节`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const isImageMime = (mime?: string | null): boolean => Boolean(mime && mime.startsWith('image/'));

const getFileExtUpper = (filename?: string | null): string => {
  if (!filename) return '?';
  const dotIdx = filename.lastIndexOf('.');
  if (dotIdx < 0 || dotIdx === filename.length - 1) return '?';
  return filename.substring(dotIdx + 1).toUpperCase().slice(0, 6);
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value && typeof value === 'object' && !Array.isArray(value));

const buildMetadataRows = (metadata?: Record<string, unknown> | null) =>
  Object.entries(metadata || {})
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => ({ key, field: key, value }));

const renderMetadataValue = (value: unknown, depth = 0): React.ReactNode => {
  if (value === null || value === undefined || value === '') return '-';
  if (Array.isArray(value)) {
    if (!value.length) return '-';
    return (
      <Space wrap>
        {value.map((item, index) => (
          <Tag key={index}>{typeof item === 'object' ? JSON.stringify(item) : String(item)}</Tag>
        ))}
      </Space>
    );
  }
  if (isRecord(value)) {
    if (depth >= 2) {
      return Object.keys(value).length ? `${Object.keys(value).length} 个字段` : '-';
    }
    return (
      <Table
        size="small"
        pagination={false}
        rowKey="key"
        dataSource={buildMetadataRows(value)}
        columns={[
          { title: '字段', dataIndex: 'field', key: 'field', width: 180 },
          {
            title: '值',
            dataIndex: 'value',
            key: 'value',
            render: (v: unknown) => renderMetadataValue(v, depth + 1),
          },
        ]}
      />
    );
  }
  return String(value);
};

const MetadataTable: React.FC<{ data?: Record<string, unknown> | null }> = ({ data }) => (
  <Table
    size="small"
    pagination={false}
    rowKey="key"
    dataSource={buildMetadataRows(data)}
    locale={{ emptyText: '暂无数据' }}
    columns={[
      { title: '字段', dataIndex: 'field', key: 'field', width: 220 },
      { title: '值', dataIndex: 'value', key: 'value', render: (v: unknown) => renderMetadataValue(v) },
    ]}
  />
);

const ThreeDSourceDetailDrawer: React.FC<ThreeDSourceDetailDrawerProps> = ({
  open,
  data,
  onClose,
}) => {
  const [drawerWidth, setDrawerWidth] = useState<number | string>(1080);

  useEffect(() => {
    const calcWidth = () => {
      const w = typeof window !== 'undefined' ? window.innerWidth : 1280;
      setDrawerWidth(w <= 1280 ? '100%' : 1080);
    };
    calcWidth();
    window.addEventListener('resize', calcWidth);
    return () => window.removeEventListener('resize', calcWidth);
  }, []);

  const productionTimeline = useMemo(() => {
    if (!data) return [];
    return [...data.production_records].sort((a, b) =>
      (b.occurred_at || '').localeCompare(a.occurred_at || ''),
    );
  }, [data]);

  const previewFiles = useMemo(() => {
    if (!data) return [];
    return data.structure.files.filter((f) => f.preview_url || f.download_url);
  }, [data]);

  const handleCopyManifest = () => {
    if (!data) return;
    const url = data.outputs.download_url;
    if (navigator.clipboard) {
      navigator.clipboard
        .writeText(url)
        .then(() => message.success('已复制资源包链接'))
        .catch(() => message.error('复制失败，请手动复制'));
    } else {
      message.info(url);
    }
  };

  const handleDownload = () => {
    if (data?.outputs.download_url) {
      window.location.href = data.outputs.download_url;
    }
  };

  if (!data) {
    return (
      <Drawer title="三维源详情" open={open} onClose={onClose} width={drawerWidth}>
        <Alert type="warning" message="暂无源详情数据，请先选择一个三维表现。" />
      </Drawer>
    );
  }

  const overviewItems = [
    { label: '标题', value: data.title },
    { label: '资源组', value: data.resource_group || '-' },
    { label: '主文件', value: data.file.filename },
    { label: '资源类型', value: data.resource_type_label },
    { label: '状态', value: data.status },
    { label: '保存层级', value: data.preservation.storage_tier || '-' },
    { label: '保存状态', value: data.preservation.preservation_status || '-' },
    { label: '当前表现', value: data.is_current ? '是' : '否' },
  ];

  const tabsItems = [
    {
      key: 'overview',
      label: '概览',
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Alert type="info" showIcon message={data.structure.summary || '暂无结构说明'} />
          <Descriptions
            bordered
            size="small"
            column={{ xs: 1, sm: 1, md: 2 }}
            labelStyle={{ width: 120 }}
          >
            {overviewItems.map((item) => (
              <Descriptions.Item key={item.label} label={item.label}>
                {item.value}
              </Descriptions.Item>
            ))}
          </Descriptions>
          {data.collection_object ? (
            <Card size="small" title="关联藏品对象">
              <Descriptions size="small" column={1}>
                <Descriptions.Item label="藏品 ID">#{data.collection_object.id}</Descriptions.Item>
                <Descriptions.Item label="藏品号">
                  {data.collection_object.object_number || '未填写'}
                </Descriptions.Item>
                <Descriptions.Item label="名称">
                  {data.collection_object.object_name || '-'}
                </Descriptions.Item>
                {data.collection_object.summary && (
                  <Descriptions.Item label="简介">
                    {data.collection_object.summary}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          ) : (
            <Alert type="info" showIcon message="未关联藏品对象" />
          )}
          {data.preservation.preservation_note && (
            <Alert
              type="warning"
              showIcon
              message="保存说明"
              description={data.preservation.preservation_note}
            />
          )}
        </Space>
      ),
    },
    {
      key: 'preview',
      label: '预览',
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {data.viewer ? (
            <Card size="small" title="三维查看器">
              <ThreeDViewer viewer={data.viewer ?? undefined} title={data.title} />
            </Card>
          ) : (
            <Alert type="info" showIcon message="该表现不支持 3D 查看器" />
          )}
          <Card size="small" title="轻量旋转预览">
            <ThreeDTurntablePreview
              title={data.title}
              previewData={(data.metadata_layers.raw_metadata as Record<string, unknown> | undefined)?.preview_data as never}
              height={220}
            />
          </Card>
          <Card size="small" title="预览图集" bodyStyle={{ padding: 12 }}>
            {previewFiles.length === 0 ? (
              <Text type="secondary">当前资源没有可直接预览的图像。</Text>
            ) : (
              <Row gutter={[12, 12]}>
                {previewFiles.map((file) => {
                  const imageUrl = file.preview_url || file.download_url;
                  const isImage = isImageMime(file.mime_type);
                  const fileKey = `${file.role}-${file.actual_filename}-${file.sort_order ?? 0}`;
                  return (
                    <Col key={fileKey} xs={24} sm={12} md={8}>
                      <Card size="small" bodyStyle={{ padding: 8 }}>
                        {imageUrl && isImage ? (
                          <Image
                            src={imageUrl}
                            alt={file.actual_filename}
                            style={{ width: '100%', maxHeight: 180, objectFit: 'cover' }}
                            fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                          />
                        ) : (
                          <div
                            style={{
                              width: '100%',
                              height: 180,
                              background: '#f5f5f5',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              borderRadius: 6,
                              gap: 6,
                            }}
                          >
                            <FileTextOutlined style={{ fontSize: 32, color: '#bfbfbf' }} />
                            <Text type="secondary" style={{ fontSize: 12, fontFamily: 'monospace' }}>
                              {getFileExtUpper(file.actual_filename)}
                            </Text>
                          </div>
                        )}
                        <Space direction="vertical" size={0} style={{ marginTop: 6 }}>
                          <Text strong style={{ fontSize: 12 }}>
                            {file.actual_filename}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {file.role_label}
                          </Text>
                        </Space>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            )}
          </Card>
        </Space>
      ),
    },
    {
      key: 'files',
      label: `文件 (${data.structure.files.length})`,
      children: (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Card size="small" title="文件分组">
            <Space wrap size={[8, 8]}>
              {data.structure.groups.map((group) => (
                <Tag key={group.role} color="blue" style={{ padding: '4px 10px' }}>
                  {group.role_label} · {group.file_count} 个 · {formatBytes(group.total_file_size)}
                </Tag>
              ))}
            </Space>
          </Card>
          <Card size="small" title="文件构成">
            <Table
              rowKey={(record) => `${record.role}-${record.actual_filename}-${record.sort_order ?? 0}`}
              size="small"
              pagination={{ pageSize: 10, hideOnSinglePage: true, showSizeChanger: false }}
              columns={[
                {
                  title: '角色',
                  dataIndex: 'role_label',
                  key: 'role_label',
                  width: 120,
                  filters: Array.from(new Set(data.structure.files.map((f) => f.role_label))).map((label) => ({
                    text: label,
                    value: label,
                  })),
                  onFilter: (value, record) => record.role_label === value,
                },
                {
                  title: '文件名',
                  dataIndex: 'actual_filename',
                  key: 'actual_filename',
                  ellipsis: true,
                  render: (value: string) => (
                    <Paragraph copyable={{ text: value }} style={{ marginBottom: 0 }}>
                      <Text style={{ fontSize: 12 }}>{value}</Text>
                    </Paragraph>
                  ),
                },
                {
                  title: '大小',
                  dataIndex: 'file_size',
                  key: 'file_size',
                  width: 100,
                  sorter: (a, b) => a.file_size - b.file_size,
                  render: (value: number) => formatBytes(value),
                },
                {
                  title: '主文件',
                  dataIndex: 'is_primary',
                  key: 'is_primary',
                  width: 80,
                  render: (value: boolean) =>
                    value ? <Tag color="green">是</Tag> : <Tag>否</Tag>,
                },
              ]}
              dataSource={data.structure.files}
            />
          </Card>
        </Space>
      ),
    },
    {
      key: 'metadata',
      label: '元数据',
      children: (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card size="small" title="技术元数据" style={{ height: '100%' }}>
              <MetadataTable data={data.technical_metadata} />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card size="small" title="分层元数据" style={{ height: '100%' }}>
              <MetadataTable data={data.metadata_layers as unknown as Record<string, unknown>} />
            </Card>
          </Col>
          <Col span={24}>
            <Card size="small" title="次要字段">
              <Descriptions bordered column={{ xs: 1, sm: 2 }} size="small">
                <Descriptions.Item label="表现版本号">{data.version_label || '原始版'}</Descriptions.Item>
                <Descriptions.Item label="表现顺序">{data.version_order ?? 0}</Descriptions.Item>
                <Descriptions.Item label="Web 展示">{data.web_preview_status || 'disabled'}</Descriptions.Item>
                <Descriptions.Item label="Web 展示原因">{data.web_preview_reason || '-'}</Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'production',
      label: `生产链 (${productionTimeline.length})`,
      children: productionTimeline.length === 0 ? (
        <Alert type="info" showIcon message="暂无生产事件记录" />
      ) : (
        <Timeline
          mode="left"
          items={productionTimeline.map((record) => ({
            color: STATUS_COLOR_MAP[record.status] || 'gray',
            label: record.occurred_at,
            children: (
              <Space direction="vertical" size={2}>
                <Space wrap>
                  <Text strong>{record.event_type}</Text>
                  <Tag color={STATUS_COLOR_MAP[record.status] || 'default'}>
                    {record.stage}
                  </Tag>
                  <Tag>{record.status}</Tag>
                  {record.actor && <Text type="secondary">· {record.actor}</Text>}
                </Space>
                <Text type="secondary">{record.description || record.evidence || '-'}</Text>
              </Space>
            ),
          }))}
        />
      ),
    },
  ];

  return (
    <Drawer
      title={
        <Space size={8}>
          <Text strong>{data.title}</Text>
          <Tag color={STATUS_COLOR_MAP[data.status] || 'default'}>{data.status}</Tag>
          {data.is_current && <Tag color="blue">当前表现</Tag>}
        </Space>
      }
      open={open}
      onClose={onClose}
      width={drawerWidth}
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <Button icon={<CopyOutlined />} onClick={handleCopyManifest}>
            复制资源包链接
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
            下载资源包
          </Button>
        </div>
      }
    >
      <Tabs items={tabsItems} defaultActiveKey="overview" />
    </Drawer>
  );
};

export default ThreeDSourceDetailDrawer;
