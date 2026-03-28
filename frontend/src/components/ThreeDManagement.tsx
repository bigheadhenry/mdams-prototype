import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Drawer,
  Form,
  Image,
  Input,
  InputNumber,
  Statistic,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { DeleteOutlined, DownloadOutlined, EyeOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import axios from 'axios';
import type { ThreeDAssetSummary, ThreeDCollectionObjectSummary, ThreeDDetailResponse } from '../types/assets';
import ThreeDViewer from './ThreeDViewer';

const { Paragraph, Text, Title } = Typography;

const PROFILE_OPTIONS = [
  { value: 'model', label: '模型' },
  { value: 'point_cloud', label: '点云' },
  { value: 'oblique_photo', label: '倾斜摄影图像' },
  { value: 'package', label: '三维资源包' },
  { value: 'other', label: '其他' },
];

const WEB_PREVIEW_STATUS_OPTIONS = [
  { value: 'ready', label: 'ready' },
  { value: 'pending', label: 'pending' },
  { value: 'disabled', label: 'disabled' },
];

const SAMPLE_MODELS = [
  { title: '示例对象原始版（glTF + BIN + PNG）', url: '/test-models/museum-vase-source.gltf' },
  { title: '示例对象 Web 展示版（GLB）', url: '/test-models/museum-vase-preview.glb' },
  { title: '示例对象高细节版（GLB）', url: '/test-models/museum-vase-detail.glb' },
];

const buildLocalViewer = (title: string, url: string): ThreeDDetailResponse['viewer'] => ({
  enabled: true,
  reason: null,
  renderer: 'model-viewer',
  preview_file: {
    role: 'model',
    role_label: '示例模型',
    filename: title,
    actual_filename: title,
    file_path: url,
    file_size: 0,
    mime_type: 'model/gltf+json',
    is_primary: true,
    sort_order: 0,
    download_url: url,
    preview_url: url,
  },
  preview_url: url,
  supported_roles: ['model'],
});

type ThreeDObjectGroup = {
  key: string;
  label: string;
  versions: ThreeDAssetSummary[];
  resourceType: string;
  profileLabel: string | null;
  objectNumber: string | null;
  objectName: string | null;
  currentVersion: ThreeDAssetSummary | null;
  webPreviewVersion: ThreeDAssetSummary | null;
  latestVersion: ThreeDAssetSummary | null;
  storageTier: string | null;
  preservationStatus: string | null;
  updatedAt: string | null;
  readyCount: number;
  totalFileCount: number;
};

const getVersionOrder = (item: ThreeDAssetSummary) => item.version_order ?? 0;

const getGroupKey = (item: ThreeDAssetSummary) => (item.resource_group || item.title || item.filename || `resource-${item.id}`).trim();

const getGroupLabel = (item: ThreeDAssetSummary) => item.resource_group?.trim() || item.title?.trim() || item.filename;

const getPreferredDetailVersion = (group: ThreeDObjectGroup) =>
  group.webPreviewVersion ?? group.currentVersion ?? group.latestVersion;

const ThreeDManagement: React.FC = () => {
  const [items, setItems] = useState<ThreeDAssetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedModelFiles, setSelectedModelFiles] = useState<File[]>([]);
  const [selectedPointCloudFiles, setSelectedPointCloudFiles] = useState<File[]>([]);
  const [selectedObliqueFiles, setSelectedObliqueFiles] = useState<File[]>([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detail, setDetail] = useState<ThreeDDetailResponse | null>(null);
  const [collectionObjects, setCollectionObjects] = useState<ThreeDCollectionObjectSummary[]>([]);
  const [collectionObjectLoading, setCollectionObjectLoading] = useState(false);
  const [sampleModelUrl, setSampleModelUrl] = useState(SAMPLE_MODELS[0]?.url ?? '/test-models/cube.gltf');
  const [form] = Form.useForm();
    const sampleModel = useMemo(
    () => SAMPLE_MODELS.find((model) => model.url === sampleModelUrl) ?? SAMPLE_MODELS[0],
    [sampleModelUrl],
  );
  const sampleViewer = useMemo(
    () => buildLocalViewer(sampleModel?.title ?? '示例模型', sampleModel?.url ?? sampleModelUrl),
    [sampleModel, sampleModelUrl],
  );
  const collectionObjectOptions = useMemo(
    () =>
      collectionObjects.map((item) => ({
        value: item.id,
        label: `${item.object_number || `#${item.id}`} · ${item.object_name || '未命名藏品对象'}`,
        title: item.object_name || item.object_number || `#${item.id}`,
      })),
    [collectionObjects],
  );  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await axios.get<ThreeDAssetSummary[]>('/api/three-d/resources');
      setItems(res.data);
    } finally {
      setLoading(false);
    }
  };

  const fetchCollectionObjects = async (query?: string) => {
    setCollectionObjectLoading(true);
    try {
      const res = await axios.get<ThreeDCollectionObjectSummary[]>('/api/three-d/collection-objects', {
        params: query ? { q: query, limit: 50 } : { limit: 50 },
      });
      setCollectionObjects(res.data);
    } finally {
      setCollectionObjectLoading(false);
    }
  };

  useEffect(() => {
    void fetchItems();
    void fetchCollectionObjects();
  }, []);

  const openDetail = async (id: number) => {
    setDetailOpen(true);
    setDetailLoading(true);
    try {
      const res = await axios.get<ThreeDDetailResponse>(`/api/three-d/resources/${id}`);
      setDetail(res.data);
    } catch (err) {
      console.error(err);
      message.error('加载三维资源详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUpload = async (values: Record<string, unknown>) => {
    const hasFiles =
      selectedModelFiles.length > 0 || selectedPointCloudFiles.length > 0 || selectedObliqueFiles.length > 0;
    if (!hasFiles) {
      message.warning('请至少选择一种三维文件');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      selectedModelFiles.forEach((file) => formData.append('model_files', file));
      selectedPointCloudFiles.forEach((file) => formData.append('point_cloud_files', file));
      selectedObliqueFiles.forEach((file) => formData.append('oblique_files', file));
      Object.entries(values).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          formData.append(key, String(value));
        }
      });

      await axios.post('/api/three-d/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success('三维资源上传成功');
      form.resetFields();
      setSelectedModelFiles([]);
      setSelectedPointCloudFiles([]);
      setSelectedObliqueFiles([]);
      await fetchItems();
    } catch (err) {
      console.error(err);
      message.error('三维资源上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    await axios.delete(`/api/three-d/resources/${id}`);
    message.success('三维资源已删除');
    await fetchItems();
  };

  const groupedItems = useMemo<ThreeDObjectGroup[]>(() => {
    const groups = new Map<string, ThreeDObjectGroup>();

    items.forEach((item) => {
      const key = getGroupKey(item);
      const label = getGroupLabel(item);
      const nextGroup =
        groups.get(key) ??
        ({
          key,
          label,
          versions: [],
          resourceType: item.resource_type,
          profileLabel: item.profile_label ?? null,
          objectNumber: item.object_number ?? null,
          objectName: item.object_name ?? null,
          currentVersion: null,
          webPreviewVersion: null,
          latestVersion: null,
          storageTier: item.storage_tier ?? null,
          preservationStatus: item.preservation_status ?? null,
          updatedAt: null,
          readyCount: 0,
          totalFileCount: 0,
        } as ThreeDObjectGroup);

      nextGroup.versions.push(item);
      nextGroup.resourceType = nextGroup.resourceType || item.resource_type;
      nextGroup.profileLabel = nextGroup.profileLabel || item.profile_label || null;
      nextGroup.objectNumber = nextGroup.objectNumber || item.object_number || null;
      nextGroup.objectName = nextGroup.objectName || item.object_name || null;
      nextGroup.storageTier = nextGroup.storageTier || item.storage_tier || null;
      nextGroup.preservationStatus = nextGroup.preservationStatus || item.preservation_status || null;
      if (!nextGroup.updatedAt || item.created_at > nextGroup.updatedAt) {
        nextGroup.updatedAt = item.created_at;
      }
      groups.set(key, nextGroup);
    });

    return Array.from(groups.values())
      .map((group) => {
        const versions = [...group.versions].sort((a, b) => {
          const orderDiff = getVersionOrder(a) - getVersionOrder(b);
          if (orderDiff !== 0) {
            return orderDiff;
          }
          return a.created_at.localeCompare(b.created_at);
        });
        const currentVersion = versions.find((version) => version.is_current) ?? versions[versions.length - 1] ?? null;
        const webPreviewVersion =
          versions.find((version) => version.is_web_preview && version.web_preview_status === 'ready') ?? null;
        const latestVersion = versions[versions.length - 1] ?? null;
        return {
          ...group,
          versions,
          currentVersion,
          webPreviewVersion,
          latestVersion,
          readyCount: versions.filter((version) => version.is_web_preview && version.web_preview_status === 'ready').length,
          totalFileCount: versions.reduce((sum, version) => sum + (version.file_count ?? 0), 0),
        };
      })
      .sort((a, b) => {
        if (a.updatedAt && b.updatedAt && a.updatedAt !== b.updatedAt) {
          return b.updatedAt.localeCompare(a.updatedAt);
        }
        return a.label.localeCompare(b.label);
      });
  }, [items]);

  const overview = useMemo(() => {
    const webPreviewGroups = groupedItems.filter((group) => group.webPreviewVersion);
    const totalFileCount = groupedItems.reduce((sum, group) => sum + group.totalFileCount, 0);
    return {
      objectCount: groupedItems.length,
      versionCount: items.length,
      webPreviewGroupCount: webPreviewGroups.length,
      currentVersionCount: groupedItems.filter((group) => group.currentVersion).length,
      totalFileCount,
    };
  }, [groupedItems, items.length]);

  const groupColumns: ColumnsType<ThreeDObjectGroup> = [
    {
      title: '数字对象',
      key: 'label',
      render: (_: unknown, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.label}</Text>
          <Text type="secondary">
            {record.objectNumber || '未关联藏品号'}
            {record.objectName ? ` · ${record.objectName}` : ''}
          </Text>
          <Text type="secondary">
            {record.profileLabel || '其他'} · {record.resourceType}
          </Text>
        </Space>
      ),
    },
    {
      title: '版本数',
      key: 'version_count',
      render: (_, record) => record.versions.length,
    },
    {
      title: '当前版本',
      key: 'current_version',
      render: (_, record) =>
        record.currentVersion ? (
          <Space direction="vertical" size={0}>
            <Tag color={record.currentVersion.is_current ? 'blue' : 'default'}>
              {record.currentVersion.version_label || 'original'}
            </Tag>
            <Text type="secondary">#{record.currentVersion.version_order ?? 0}</Text>
          </Space>
        ) : (
          <Tag>未设置</Tag>
        ),
    },
    {
      title: 'Web 展示版',
      key: 'web_preview_version',
      render: (_, record) =>
        record.webPreviewVersion ? (
          <Space direction="vertical" size={0}>
            <Tag color="green">{record.webPreviewVersion.version_label || 'original'}</Tag>
            <Text type="secondary">{record.webPreviewVersion.web_preview_status || 'disabled'}</Text>
          </Space>
        ) : (
          <Tag color="default">未配置</Tag>
        ),
    },
    {
      title: '保存层',
      key: 'storage_tier',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Tag color={record.storageTier === 'archive' ? 'blue' : record.storageTier === 'delivery' ? 'green' : 'gold'}>
            {record.storageTier || 'archive'}
          </Tag>
          <Text type="secondary">{record.preservationStatus || 'pending'}</Text>
        </Space>
      ),
    },
    {
      title: '文件总数',
      key: 'total_file_count',
      render: (_, record) => record.totalFileCount,
    },
    {
      title: '更新时间',
      key: 'updated_at',
      render: (_, record) => record.updatedAt || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => {
        const preferred = getPreferredDetailVersion(record);
        return (
          <Space wrap>
            <Button
              icon={<EyeOutlined />}
              disabled={!preferred}
              onClick={() => {
                if (preferred) {
                  void openDetail(preferred.id);
                }
              }}
            >
              查看详情
            </Button>
            <Button
              icon={<DownloadOutlined />}
              disabled={!preferred}
              onClick={() => {
                if (preferred) {
                  window.location.href = `/api/three-d/resources/${preferred.id}/download`;
                }
              }}
            >
              下载当前版
            </Button>
          </Space>
        );
      },
    },
  ];

  const versionColumns: ColumnsType<ThreeDAssetSummary> = [
    {
      title: '版本',
      key: 'version_label',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Space wrap>
            <Tag color={record.is_current ? 'blue' : 'default'}>{record.version_label || 'original'}</Tag>
            {record.is_current ? <Tag color="gold">当前</Tag> : null}
          </Space>
          <Text type="secondary">#{record.version_order ?? 0}</Text>
        </Space>
      ),
    },
    {
      title: 'Web 展示',
      key: 'web_preview',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Tag color={record.web_preview_status === 'ready' ? 'green' : record.web_preview_status === 'pending' ? 'gold' : 'default'}>
            {record.web_preview_status || 'disabled'}
          </Tag>
          <Text type="secondary">{record.is_web_preview ? '允许展示' : '不展示'}</Text>
        </Space>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (value: string | null | undefined) => <Text>{value || '-'}</Text>,
    },
    {
      title: '主文件',
      dataIndex: 'filename',
      key: 'filename',
      render: (value: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{value}</Paragraph>,
    },
    {
      title: '文件数',
      dataIndex: 'file_count',
      key: 'file_count',
      render: (value: number | undefined) => value ?? 0,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => <Tag color={value === 'ready' ? 'green' : value === 'error' ? 'red' : 'blue'}>{value}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space wrap>
          <Button icon={<EyeOutlined />} onClick={() => void openDetail(record.id)}>
            详情
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = `/api/three-d/resources/${record.id}/download`;
            }}
          >
            下载
          </Button>
          <Button danger icon={<DeleteOutlined />} onClick={() => void handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const previewFiles = detail?.structure.files.filter((file) => file.role === 'oblique_photo') ?? [];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={16}>
        <Col span={24}>
          <Card bordered={false}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Title level={4} style={{ margin: 0 }}>
                三维数据管理子系统
              </Title>
              <Text type="secondary">
                从管理角度，一个数字对象对应一组数字资源。这里默认按资源组聚合展示，版本展开后再看原始版、v1、v2 等记录。
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card
        title="测试模型"
        bordered={false}
        extra={
          <Select
            style={{ width: 220 }}
            value={sampleModelUrl}
            onChange={setSampleModelUrl}
            options={SAMPLE_MODELS.map((model) => ({ label: model.title, value: model.url }))}
          />
        }
      >
        <ThreeDViewer viewer={sampleViewer} title={sampleModel?.title} />
      </Card>

      <Card title="上传三维资源" bordered={false}>
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item label="标题" name="title">
                <Input placeholder="例如：古建筑三维资源包" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="资源组" name="resource_group">
                <Input placeholder="同一数字对象的资源组标识" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="版本号" name="version_label" initialValue="original">
                <Input placeholder="original / v1 / v2" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="版本顺序" name="version_order" initialValue={0}>
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="当前版本" name="is_current" valuePropName="checked" initialValue={true}>
                <Checkbox />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="允许 Web 展示" name="is_web_preview" valuePropName="checked" initialValue={false}>
                <Checkbox />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Web 展示状态" name="web_preview_status" initialValue="disabled">
                <Select options={WEB_PREVIEW_STATUS_OPTIONS} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Web 展示原因" name="web_preview_reason">
                <Input placeholder="不展示的原因或说明" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="Profile" name="profile_key" initialValue="package">
                <Select options={PROFILE_OPTIONS} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="项目名称" name="project_name">
                <Input placeholder="项目名称" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="创建者" name="creator">
                <Input placeholder="创建者" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="创建者单位" name="creator_org">
                <Input placeholder="创建者单位" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="关联藏品对象" name="collection_object_id">
                <Select
                  showSearch
                  allowClear
                  loading={collectionObjectLoading}
                  placeholder="按藏品号或名称检索已有藏品对象"
                  options={collectionObjectOptions}
                  filterOption={false}
                  onSearch={(value) => void fetchCollectionObjects(value)}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="藏品号" name="object_number">
                <Input placeholder="例如：故00154701" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="藏品名称" name="object_name">
                <Input placeholder="例如：青花瓷瓶" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="藏品类型" name="object_type">
                <Input placeholder="可移动文物 / 不可移动文物 / 其他" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="收藏单位" name="collection_unit">
                <Input placeholder="收藏单位或部门" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="对象摘要" name="object_summary">
                <Input placeholder="对象级说明" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="对象关键词" name="object_keywords">
                <Input placeholder="逗号分隔关键词" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="格式名称" name="format_name">
                <Input placeholder="glb / ply / jpg / mixed" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="顶点数" name="vertex_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="面数" name="face_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="材质数" name="material_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="贴图数" name="texture_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="点数" name="point_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="LOD 层级" name="lod_count">
                <InputNumber style={{ width: '100%' }} min={0} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="坐标系" name="coordinate_system">
                <Input placeholder="WGS84 / 本地坐标系" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="单位" name="unit">
                <Input placeholder="m / cm / mm" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="存储层级" name="storage_tier" initialValue="archive">
                <Select
                  options={[
                    { value: 'working', label: 'working' },
                    { value: 'delivery', label: 'delivery' },
                    { value: 'archive', label: 'archive' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="保存状态" name="preservation_status" initialValue="pending">
                <Select
                  options={[
                    { value: 'pending', label: 'pending' },
                    { value: 'preserved', label: 'preserved' },
                    { value: 'archived', label: 'archived' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="保存说明" name="preservation_note">
                <Input placeholder="保存或归档说明" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item label="模型文件">
                <input
                  type="file"
                  accept=".glb,.gltf,.obj,.fbx,.stl,.usdz"
                  multiple
                  onChange={(event) => setSelectedModelFiles(Array.from(event.target.files || []))}
                />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item label="点云文件">
                <input
                  type="file"
                  accept=".ply,.las,.laz,.xyz,.pts"
                  multiple
                  onChange={(event) => setSelectedPointCloudFiles(Array.from(event.target.files || []))}
                />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item label="倾斜摄影图像">
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.tif,.tiff,.bmp"
                  multiple
                  onChange={(event) => setSelectedObliqueFiles(Array.from(event.target.files || []))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Space>
            <Button type="primary" htmlType="submit" loading={uploading} icon={<UploadOutlined />}>
              上传资源包
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => void fetchItems()}>
              刷新列表
            </Button>
          </Space>
        </Form>
      </Card>

      <Card title="数字对象概览" bordered={false}>
        <Row gutter={16}>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="数字对象" value={overview.objectCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="版本总数" value={overview.versionCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="可展示对象" value={overview.webPreviewGroupCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="文件总数" value={overview.totalFileCount} />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            <Card size="small" title="最近对象" bordered={false}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {groupedItems.slice(0, 4).map((group) => {
                  const preferred = getPreferredDetailVersion(group);
                  return (
                    <Space key={group.key} align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space direction="vertical" size={0}>
                        <Text strong>{group.label}</Text>
                        <Text type="secondary">
                          {group.versions.length} 个版本 · {group.totalFileCount} 个文件
                        </Text>
                      </Space>
                      <Space wrap>
                        <Tag color={group.webPreviewVersion ? 'green' : 'default'}>
                          {group.webPreviewVersion ? '可展示' : '未展示'}
                        </Tag>
                        <Button
                          size="small"
                          type="link"
                          disabled={!preferred}
                          onClick={() => {
                            if (preferred) {
                              void openDetail(preferred.id);
                            }
                          }}
                        >
                          打开
                        </Button>
                      </Space>
                    </Space>
                  );
                })}
              </Space>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card size="small" title="对象级状态" bordered={false}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {groupedItems.slice(0, 4).map((group) => (
                  <Space key={`${group.key}-state`} align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>{group.label}</Text>
                    <Space wrap>
                      <Tag color={group.currentVersion ? 'blue' : 'default'}>
                        当前：{group.currentVersion?.version_label || '未设'}
                      </Tag>
                      <Tag color={group.webPreviewVersion ? 'green' : 'default'}>
                        Web：{group.webPreviewVersion?.version_label || '未设'}
                      </Tag>
                    </Space>
                  </Space>
                ))}
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>

      <Card title="数字对象视图" bordered={false}>
        <Table
          rowKey="key"
          loading={loading}
          dataSource={groupedItems}
          columns={groupColumns}
          expandable={{
            expandedRowRender: (record) => (
              <Table
                rowKey="id"
                pagination={false}
                dataSource={record.versions}
                columns={versionColumns}
                size="small"
              />
            ),
            rowExpandable: (record) => record.versions.length > 1,
          }}
        />
      </Card>

      <Drawer
        title={detail?.title || '三维资源详情'}
        open={detailOpen}
        onClose={() => {
          setDetailOpen(false);
          setDetail(null);
        }}
        width={1080}
      >
        {detailLoading || !detail ? (
          <div>加载中...</div>
        ) : (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="标题">{detail.title}</Descriptions.Item>
              <Descriptions.Item label="资源组">{detail.resource_group || '-'}</Descriptions.Item>
              <Descriptions.Item label="版本">{detail.version_label || 'original'}</Descriptions.Item>
              <Descriptions.Item label="版本顺序">{detail.version_order ?? 0}</Descriptions.Item>
              <Descriptions.Item label="当前版本">{detail.is_current ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label="Web 展示">{detail.web_preview_status || 'disabled'}</Descriptions.Item>
              <Descriptions.Item label="Web 展示说明">{detail.web_preview_reason || '-'}</Descriptions.Item>
              <Descriptions.Item label="主文件">{detail.file.filename}</Descriptions.Item>
              <Descriptions.Item label="Profile">{detail.profile_label || detail.profile_key || '-'}</Descriptions.Item>
              <Descriptions.Item label="资源类型">{detail.resource_type_label}</Descriptions.Item>
              <Descriptions.Item label="状态">{detail.status}</Descriptions.Item>
              <Descriptions.Item label="关联藏品对象">
                {detail.collection_object ? (
                  <Space direction="vertical" size={0}>
                    <Text strong>#{detail.collection_object.id}</Text>
                    <Text type="secondary">
                      {detail.collection_object.object_number || '未填写藏品号'}
                      {detail.collection_object.object_name ? ` · ${detail.collection_object.object_name}` : ''}
                    </Text>
                  </Space>
                ) : (
                  '-'
                )}
              </Descriptions.Item>
              <Descriptions.Item label="藏品号">{detail.collection_object?.object_number || '-'}</Descriptions.Item>
              <Descriptions.Item label="藏品名称">{detail.collection_object?.object_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="保存层级">{detail.preservation.storage_tier || '-'}</Descriptions.Item>
              <Descriptions.Item label="保存状态">{detail.preservation.preservation_status || '-'}</Descriptions.Item>
              <Descriptions.Item label="保存说明">{detail.preservation.preservation_note || '-'}</Descriptions.Item>
              <Descriptions.Item label="构成">{detail.structure.summary}</Descriptions.Item>
            </Descriptions>

            <ThreeDViewer viewer={detail.viewer} title={detail.title} />

            <Card size="small" title="图像预览">
              <Row gutter={[12, 12]}>
                {previewFiles.length > 0 ? (
                  previewFiles.map((file) => {
                    const imageUrl = file.preview_url || file.download_url;
                    return (
                      <Col key={`${file.role}-${file.actual_filename}-${file.sort_order ?? 0}`} xs={24} sm={12} md={8}>
                        <Card size="small" bodyStyle={{ padding: 12 }}>
                          <Space direction="vertical" style={{ width: '100%' }}>
                            {imageUrl ? (
                              <Image
                                src={imageUrl}
                                alt={file.actual_filename}
                                style={{ width: '100%', maxHeight: 220, objectFit: 'cover' }}
                              />
                            ) : null}
                            <Text strong>{file.actual_filename}</Text>
                            <Text type="secondary">{file.role_label}</Text>
                          </Space>
                        </Card>
                      </Col>
                    );
                  })
                ) : (
                  <Col span={24}>
                    <Text type="secondary">当前资源没有可直接预览的倾斜摄影图像。</Text>
                  </Col>
                )}
              </Row>
            </Card>

            <Card size="small" title="文件构成">
              <Table
                rowKey={(record) => `${record.role}-${record.actual_filename}-${record.sort_order ?? 0}`}
                pagination={false}
                columns={[
                  { title: '角色', dataIndex: 'role_label', key: 'role_label' },
                  {
                    title: '文件名',
                    dataIndex: 'actual_filename',
                    key: 'actual_filename',
                    render: (value: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{value}</Paragraph>,
                  },
                  {
                    title: '大小',
                    dataIndex: 'file_size',
                    key: 'file_size',
                    render: (value: number) => `${(value / 1024 / 1024).toFixed(2)} MB`,
                  },
                  {
                    title: '主文件',
                    dataIndex: 'is_primary',
                    key: 'is_primary',
                    render: (value: boolean) => (value ? <Tag color="green">是</Tag> : <Tag>否</Tag>),
                  },
                ]}
                dataSource={detail.structure.files}
              />
            </Card>

            <Row gutter={16}>
              <Col xs={24} lg={12}>
                <Card size="small" title="文件分组">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {detail.structure.groups.map((group) => (
                      <Space key={group.role} align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
                        <Text>{group.role_label}</Text>
                        <Text>
                          {group.file_count} 个，{(group.total_file_size / 1024 / 1024).toFixed(2)} MB
                        </Text>
                      </Space>
                    ))}
                  </Space>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title="技术元数据">
                  <pre style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {JSON.stringify(detail.technical_metadata, null, 2)}
                  </pre>
                </Card>
              </Col>
            </Row>

            <Card size="small" title="生产链·">
              <Table
                rowKey="id"
                pagination={false}
                dataSource={detail.production_records}
                columns={[
                  { title: '阶段', dataIndex: 'stage', key: 'stage' },
                  { title: '事件', dataIndex: 'event_type', key: 'event_type' },
                  { title: '状态', dataIndex: 'status', key: 'status' },
                  { title: '执行人', dataIndex: 'actor', key: 'actor', render: (value: string | null | undefined) => value || '-' },
                  { title: '时间', dataIndex: 'occurred_at', key: 'occurred_at' },
                ]}
              />
            </Card>

            <Card size="small" title="分层元数据">
              <pre style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                {JSON.stringify(detail.metadata_layers, null, 2)}
              </pre>
            </Card>

            <Space>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => {
                  window.location.href = detail.outputs.download_url;
                }}
              >
                下载资源包
              </Button>
            </Space>
          </Space>
        )}
      </Drawer>
    </Space>
  );
};

export default ThreeDManagement;
