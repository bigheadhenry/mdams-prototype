import React, { useState, useEffect, useMemo } from 'react';
import {
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Steps,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  CheckCircleOutlined,
  CloudUploadOutlined,
  LinkOutlined,
  UploadOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import type { ThreeDCollectionObjectSummary } from '../types/assets';

const { Text, Title } = Typography;

type ThreeDUploadRole = 'model' | 'point_cloud' | 'oblique_photo';

const MAX_THREE_D_UPLOAD_FILE_SIZE = 10 * 1024 * 1024 * 1024;

const ALLOWED_UPLOAD_EXTENSIONS: Record<ThreeDUploadRole, string[]> = {
  model: ['glb', 'gltf', 'obj', 'fbx', 'stl', 'usdz'],
  point_cloud: ['ply', 'las', 'laz', 'xyz', 'pts'],
  oblique_photo: ['jpg', 'jpeg', 'png', 'tif', 'tiff', 'bmp'],
};

const getFileExtension = (filename: string) => {
  const index = filename.lastIndexOf('.');
  return index >= 0 ? filename.slice(index + 1).toLowerCase() : '';
};

const pickValidUploadFiles = (files: File[], role: ThreeDUploadRole) => {
  const allowed = new Set(ALLOWED_UPLOAD_EXTENSIONS[role]);
  const accepted: File[] = [];
  const rejected: string[] = [];

  files.forEach((file) => {
    const extension = getFileExtension(file.name);
    if (!extension || !allowed.has(extension)) {
      rejected.push(`${file.name}: unsupported extension`);
      return;
    }
    if (file.size <= 0) {
      rejected.push(`${file.name}: empty file`);
      return;
    }
    if (file.size > MAX_THREE_D_UPLOAD_FILE_SIZE) {
      rejected.push(`${file.name}: exceeds 10GB`);
      return;
    }
    accepted.push(file);
  });

  return { accepted, rejected };
};

const getUploadErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
  }
  return '3D ingest failed. Please check the selected files and try again.';
};

/* ─── 选项常量 ─── */
const PROFILE_OPTIONS = [
  { value: 'model', label: '模型' },
  { value: 'point_cloud', label: '点云' },
  { value: 'oblique_photo', label: '倾斜摄影图像' },
  { value: 'package', label: '三维资源包' },
  { value: 'other', label: '其他' },
];

const WEB_PREVIEW_STATUS_OPTIONS = [
  { value: 'ready', label: '已就绪' },
  { value: 'pending', label: '准备中' },
  { value: 'disabled', label: '未启用' },
];

/* ─── 步骤定义 ─── */
const STEPS = [
  { title: '资源类型', icon: <DatabaseOutlined /> },
  { title: '文件上传', icon: <CloudUploadOutlined /> },
  { title: '藏品关联', icon: <LinkOutlined /> },
  { title: '元数据', icon: <FileTextOutlined /> },
  { title: '确认入库', icon: <CheckCircleOutlined /> },
];

interface ThreeDIngestWizardProps {
  collectionObjects: ThreeDCollectionObjectSummary[];
  collectionObjectLoading: boolean;
  onFetchCollectionObjects: (query?: string) => void;
  onSuccess: () => void;
  onCancel: () => void;
}

const ThreeDIngestWizard: React.FC<ThreeDIngestWizardProps> = ({
  collectionObjects,
  collectionObjectLoading,
  onFetchCollectionObjects,
  onSuccess,
  onCancel,
}) => {
  const [current, setCurrent] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();

  const [profileKey, setProfileKey] = useState<string>('package');
  const [selectedModelFiles, setSelectedModelFiles] = useState<File[]>([]);
  const [selectedPointCloudFiles, setSelectedPointCloudFiles] = useState<File[]>([]);
  const [selectedObliqueFiles, setSelectedObliqueFiles] = useState<File[]>([]);

  const collectionObjectOptions = useMemo(
    () =>
      collectionObjects.map((item) => ({
        value: item.id,
        label: `${item.object_number || `#${item.id}`} · ${item.object_name || '未命名'}`,
      })),
    [collectionObjects],
  );

  useEffect(() => {
    void onFetchCollectionObjects();
  }, [onFetchCollectionObjects]);

  const isModel = profileKey === 'model' || profileKey === 'package';
  const isPointCloud = profileKey === 'point_cloud' || profileKey === 'package';
  const isOblique = profileKey === 'oblique_photo' || profileKey === 'package';

  const hasAnyFile =
    selectedModelFiles.length > 0 ||
    selectedPointCloudFiles.length > 0 ||
    selectedObliqueFiles.length > 0;

  const handleFileSelection = (
    files: FileList | null,
    role: ThreeDUploadRole,
    setFiles: React.Dispatch<React.SetStateAction<File[]>>,
  ) => {
    const { accepted, rejected } = pickValidUploadFiles(Array.from(files || []), role);
    setFiles(accepted);
    if (rejected.length > 0) {
      message.warning(`Skipped ${rejected.length} invalid file(s): ${rejected.slice(0, 3).join('; ')}`);
    }
  };

  const handleUpload = async () => {
    const values = form.getFieldsValue();
    const invalidFiles = [
      ...pickValidUploadFiles(selectedModelFiles, 'model').rejected,
      ...pickValidUploadFiles(selectedPointCloudFiles, 'point_cloud').rejected,
      ...pickValidUploadFiles(selectedObliqueFiles, 'oblique_photo').rejected,
    ];
    if (invalidFiles.length > 0) {
      message.error(`Please remove invalid file(s): ${invalidFiles.slice(0, 3).join('; ')}`);
      return;
    }
    if (!hasAnyFile) {
      message.warning('请至少选择一种三维文件');
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      selectedModelFiles.forEach((f) => fd.append('model_files', f));
      selectedPointCloudFiles.forEach((f) => fd.append('point_cloud_files', f));
      selectedObliqueFiles.forEach((f) => fd.append('oblique_files', f));
      fd.append('profile_key', profileKey);
      Object.entries(values).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          fd.append(key, String(value));
        }
      });
      await axios.post('/api/three-d/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success('三维资源入库成功！');
      form.resetFields();
      setSelectedModelFiles([]);
      setSelectedPointCloudFiles([]);
      setSelectedObliqueFiles([]);
      onSuccess();
    } catch (error) {
      message.error(getUploadErrorMessage(error));
    } finally {
      setUploading(false);
    }
  };

  const summaryValues = form.getFieldsValue();

  const renderStep = () => {
    switch (current) {
      /* ── 步骤 0：资源类型 ── */
      case 0:
        return (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Text strong>请选择要入库的三维资源类型：</Text>
            <Select
              style={{ width: 320 }}
              size="large"
              value={profileKey}
              onChange={(v) => setProfileKey(v)}
              options={PROFILE_OPTIONS}
            />
            <Text type="secondary">
              {profileKey === 'model' && '将上传 3D 模型文件（.glb, .gltf, .obj, .fbx, .stl, .usdz）'}
              {profileKey === 'point_cloud' && '将上传点云文件（.ply, .las, .laz, .xyz, .pts）'}
              {profileKey === 'oblique_photo' && '将上传倾斜摄影图像（.jpg, .png, .tif 等）'}
              {profileKey === 'package' && '将上传混合资源包：可同时包含模型、点云、倾斜摄影等文件'}
              {profileKey === 'other' && '将上传其他类型三维数据文件'}
            </Text>
          </Space>
        );

      /* ── 步骤 1：文件上传 ── */
      case 1:
        return (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {isModel && (
              <Card size="small" title="模型文件" extra={<Tag color="blue">{selectedModelFiles.length} 个</Tag>}>
                <input type="file" accept=".glb,.gltf,.obj,.fbx,.stl,.usdz" multiple
                  onChange={(e) => handleFileSelection(e.target.files, 'model', setSelectedModelFiles)} />
                {selectedModelFiles.length > 0 && (
                  <Space direction="vertical" size={4} style={{ marginTop: 8 }}>
                    {selectedModelFiles.map((f, i) => (
                      <Text key={i} type="secondary" style={{ fontSize: 12 }}>{f.name} ({(f.size / 1024 / 1024).toFixed(2)} MB)</Text>
                    ))}
                  </Space>
                )}
              </Card>
            )}
            {isPointCloud && (
              <Card size="small" title="点云文件" extra={<Tag color="cyan">{selectedPointCloudFiles.length} 个</Tag>}>
                <input type="file" accept=".ply,.las,.laz,.xyz,.pts" multiple
                  onChange={(e) => handleFileSelection(e.target.files, 'point_cloud', setSelectedPointCloudFiles)} />
                {selectedPointCloudFiles.length > 0 && (
                  <Space direction="vertical" size={4} style={{ marginTop: 8 }}>
                    {selectedPointCloudFiles.map((f, i) => (
                      <Text key={i} type="secondary" style={{ fontSize: 12 }}>{f.name} ({(f.size / 1024 / 1024).toFixed(2)} MB)</Text>
                    ))}
                  </Space>
                )}
              </Card>
            )}
            {isOblique && (
              <Card size="small" title="倾斜摄影图像" extra={<Tag color="orange">{selectedObliqueFiles.length} 个</Tag>}>
                <input type="file" accept=".jpg,.jpeg,.png,.tif,.tiff,.bmp" multiple
                  onChange={(e) => handleFileSelection(e.target.files, 'oblique_photo', setSelectedObliqueFiles)} />
                {selectedObliqueFiles.length > 0 && (
                  <Space direction="vertical" size={4} style={{ marginTop: 8 }}>
                    {selectedObliqueFiles.map((f, i) => (
                      <Text key={i} type="secondary" style={{ fontSize: 12 }}>{f.name} ({(f.size / 1024 / 1024).toFixed(2)} MB)</Text>
                    ))}
                  </Space>
                )}
              </Card>
            )}
            {!hasAnyFile && <Text type="secondary">请至少上传一个文件</Text>}
          </Space>
        );

      /* ── 步骤 2：藏品关联 ── */
      case 2:
        return (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Form.Item label="关联已有藏品对象" name="collection_object_id" noStyle>
              <Select
                showSearch allowClear
                loading={collectionObjectLoading}
                placeholder="按藏品号或名称检索已有藏品对象"
                options={collectionObjectOptions}
                filterOption={false}
                onSearch={(v) => onFetchCollectionObjects(v)}
                style={{ width: '100%' }}
              />
            </Form.Item>
            <Text type="secondary">或填写新的藏品信息：</Text>
            <Row gutter={16}>
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
                  <Input placeholder="可移动文物 / 不可移动文物" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item label="收藏单位" name="collection_unit">
                  <Input placeholder="收藏单位" />
                </Form.Item>
              </Col>
            </Row>
          </Space>
        );

      /* ── 步骤 3：元数据 ── */
      case 3:
        return (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Card size="small" title="基础信息">
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
                  <Form.Item label="表现类型" name="representation_type" initialValue="derivative">
                    <Select options={[
                      { value: 'original_master', label: '原始保存级' },
                      { value: 'web_display', label: 'Web 展示级' },
                      { value: 'mobile_lightweight', label: '移动轻量级' },
                      { value: 'research_detail', label: '高精度研究级' },
                      { value: 'derivative', label: '其他派生' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item label="表现版本号" name="version_label" initialValue="original">
                    <Input placeholder="original / v1 / v2" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item label="表现顺序" name="version_order" initialValue={0}>
                    <InputNumber style={{ width: '100%' }} min={0} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item label="当前表现" name="is_current" valuePropName="checked" initialValue={true}>
                    <Checkbox />
                  </Form.Item>
                </Col>
              </Row>
            </Card>

            <Card size="small" title="Web 展示配置">
              <Row gutter={16}>
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
                  <Form.Item label="展示原因/说明" name="web_preview_reason">
                    <Input placeholder="不展示的原因" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>

            <Card size="small" title="技术参数">
              <Row gutter={16}>
                {isModel && (
                  <>
                    <Col xs={24} md={8}><Form.Item label="顶点数" name="vertex_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                    <Col xs={24} md={8}><Form.Item label="面数" name="face_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                    <Col xs={24} md={8}><Form.Item label="材质数" name="material_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                    <Col xs={24} md={8}><Form.Item label="贴图数" name="texture_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                  </>
                )}
                {isPointCloud && (
                  <Col xs={24} md={8}><Form.Item label="点数" name="point_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                )}
                <Col xs={24} md={8}><Form.Item label="LOD 层级" name="lod_count"><InputNumber style={{ width: '100%' }} min={0} /></Form.Item></Col>
                <Col xs={24} md={8}><Form.Item label="坐标系" name="coordinate_system"><Input placeholder="WGS84" /></Form.Item></Col>
                <Col xs={24} md={8}><Form.Item label="单位" name="unit"><Input placeholder="m / cm / mm" /></Form.Item></Col>
                <Col xs={24} md={12}><Form.Item label="格式名称" name="format_name"><Input placeholder="glb / ply / jpg" /></Form.Item></Col>
              </Row>
            </Card>

            <Card size="small" title="保存策略">
              <Row gutter={16}>
                <Col xs={24} md={8}>
                  <Form.Item label="存储层级" name="storage_tier" initialValue="archive">
                    <Select options={[
                      { value: 'working', label: '工作区' },
                      { value: 'delivery', label: '交付区' },
                      { value: 'archive', label: '归档区' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item label="保存状态" name="preservation_status" initialValue="pending">
                    <Select options={[
                      { value: 'pending', label: '待处理' },
                      { value: 'preserved', label: '已保存' },
                      { value: 'archived', label: '已归档' },
                    ]} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item label="保存说明" name="preservation_note">
                    <Input placeholder="保存或归档说明" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Space>
        );

      /* ── 步骤 4：确认 ── */
      case 4:
        return (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Title level={5}>入库确认</Title>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="资源类型">
                <Tag color="blue">{PROFILE_OPTIONS.find((o) => o.value === profileKey)?.label || profileKey}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="标题">{summaryValues.title || '未填写'}</Descriptions.Item>
              <Descriptions.Item label="资源组">{summaryValues.resource_group || '未填写'}</Descriptions.Item>
              <Descriptions.Item label="表现版本">{summaryValues.version_label || 'original'}</Descriptions.Item>
              <Descriptions.Item label="模型文件">{selectedModelFiles.length} 个</Descriptions.Item>
              <Descriptions.Item label="点云文件">{selectedPointCloudFiles.length} 个</Descriptions.Item>
              <Descriptions.Item label="倾斜摄影">{selectedObliqueFiles.length} 个</Descriptions.Item>
              <Descriptions.Item label="藏品号">{summaryValues.object_number || '未关联'}</Descriptions.Item>
              <Descriptions.Item label="Web 展示">{summaryValues.is_web_preview ? '允许' : '不允许'}</Descriptions.Item>
            </Descriptions>
          </Space>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Steps current={current} size="small" style={{ marginBottom: 32 }}>
        {STEPS.map((step, index) => (
          <Steps.Step key={index} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      <Form form={form} layout="vertical">
        <Card bordered={false} style={{ minHeight: 320 }}>
          {renderStep()}
        </Card>
      </Form>

      <Row justify="space-between" style={{ marginTop: 24 }}>
        <Col>
          <Button onClick={onCancel}>取消</Button>
        </Col>
        <Col>
          <Space>
            {current > 0 && (
              <Button onClick={() => setCurrent(current - 1)}>上一步</Button>
            )}
            {current < 4 && (
              <Button type="primary" onClick={() => {
                if (current === 1 && !hasAnyFile) {
                  message.warning('请至少上传一个文件');
                  return;
                }
                setCurrent(current + 1);
              }}>
                下一步
              </Button>
            )}
            {current === 4 && (
              <Button
                type="primary"
                icon={<UploadOutlined />}
                loading={uploading}
                onClick={handleUpload}
              >
                确认入库
              </Button>
            )}
          </Space>
        </Col>
      </Row>
    </div>
  );
};

export default ThreeDIngestWizard;
