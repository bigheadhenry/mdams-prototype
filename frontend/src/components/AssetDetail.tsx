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
  if (value < 1024) return `${value} 字节`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const metadataLabelMap: Record<string, string> = {
  resource_id: '资源标识',
  source_system: '来源系统',
  source_label: '来源名称',
  resource_type: '资源类型',
  resource_type_label: '资源类型名称',
  visibility_scope: '可见范围',
  collection_object_id: '馆藏对象 ID',
  title: '标题',
  status: '状态',
  preview_enabled: '是否可预览',
  profile_key: '元数据模板键',
  profile_label: '元数据模板',
  profile_sheet: '元数据模板表',
  created_at: '创建时间',
  project_type: '项目类型',
  project_name: '项目名称',
  photographer: '摄影师',
  photographer_org: '摄影师单位',
  copyright_owner: '版权所有',
  capture_time: '拍摄时间',
  image_category: '影像类型',
  image_name: '影像名称',
  capture_content: '拍摄内容',
  representative_image: '代表影像',
  remark: '备注',
  tags: '标签',
  record_account: '录入账号',
  record_time: '录入时间',
  image_record_time: '影像录入时间',
  original_file_name: '原始文件名',
  image_file_name: '影像文件名',
  identifier_type: '对象标识符类型',
  identifier_value: '对象标识符值',
  file_size: '文件大小',
  format_name: '格式名称',
  format_version: '格式版本',
  registry_name: '标准来源',
  registry_item: '标准条目',
  byte_order: '字节序',
  checksum_algorithm: '校验算法',
  checksum: '校验值',
  checksum_generator: '校验生成器',
  width: '宽度',
  height: '高度',
  color_space: '色彩空间',
  ingest_method: '入库方式',
  fixity_sha256: 'SHA256',
  conversion_method: '转换方式',
  original_file_path: '原始文件路径',
  original_file_size: '原始文件大小',
  original_mime_type: '原始 MIME 类型',
  error_message: '错误信息',
  object_number: '文物号',
  object_name: '文物名称',
  object_level: '文物级别',
  object_category: '文物类别',
  object_subcategory: '文物细类',
  management_group: '管理科组',
  photographer_phone: '提照人员电话',
  visible_to_custodians_only: '仅藏品管理者可见',
  region_level_1: '一级区域',
  region_level_2: '二级区域',
  building_name: '文物建筑名称',
  orientation: '方位',
  part_level_1: '部位一',
  part_level_2: '部位二',
  part_level_3: '部位三',
  building_component: '建筑构件',
  art_photography_type: '艺术摄影类型',
  collection_type: '藏品类型',
  palace_area: '所在宫区',
  season: '季节',
  plant: '植物',
  animal: '动物',
  solar_term: '节气',
  other: '其他',
  theme: '主题',
  cultural_topic: '文化专题',
  exhibition_topic: '展览专题',
  main_location: '主要地点',
  main_person: '主要人物',
  panorama_type: '全景类型',
  location: '位置',
  archive_number: '档案编号',
  plant_type: '植物类型',
  plant_name: '植物名称',
  region: '所在区域',
  specific_location: '具体位置',
  grade: '等级',
  archaeology_image_category: '考古影像分类',
};

const renderMetadataValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'boolean') return value ? '是' : '否';
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
    <Descriptions.Item label="文件角色">{record.role_label || record.role || '-'}</Descriptions.Item>
    <Descriptions.Item label="文件名">{record.filename || '-'}</Descriptions.Item>
    <Descriptions.Item label="实际文件">{record.actual_filename || record.filename || '-'}</Descriptions.Item>
    <Descriptions.Item label="MIME 类型">{record.mime_type || '-'}</Descriptions.Item>
    <Descriptions.Item label="文件大小">{formatBytes(record.file_size)}</Descriptions.Item>
    <Descriptions.Item label="文件路径">
      {record.file_path ? <Paragraph copyable style={{ marginBottom: 0 }}>{record.file_path}</Paragraph> : '-'}
    </Descriptions.Item>
    <Descriptions.Item label="当前版本">{record.is_current ? '是' : '否'}</Descriptions.Item>
    <Descriptions.Item label="原始文件">{record.is_original ? '是' : '否'}</Descriptions.Item>
    <Descriptions.Item label="回退标题">{fallbackTitle}</Descriptions.Item>
    {record.same_as_primary !== undefined && (
      <Descriptions.Item label="与主文件一致">{record.same_as_primary ? '是' : '否'}</Descriptions.Item>
    )}
    {record.derivation_method && (
      <Descriptions.Item label="衍生方式">{record.derivation_method}</Descriptions.Item>
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
      {item.timestamp && <Text type="secondary">时间：{item.timestamp}</Text>}
      {item.evidence && <Text type="secondary">依据：{item.evidence}</Text>}
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
        setError(detailMessage || '加载资源详情失败');
      } else {
        setError('加载资源详情失败');
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

  if (loading) return <Spin tip="正在加载资源详情..." />;

  if (error) {
    return (
      <Card>
        <Alert type="error" message="加载失败" description={error} />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回</Button>
        </div>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card>
        <Alert type="warning" message="暂无资源详情" />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回</Button>
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
        title="资源详情"
        extra={<Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回</Button>}
      >
        <Descriptions bordered column={1}>
          <Descriptions.Item label="标题">{detail.title}</Descriptions.Item>
          <Descriptions.Item label="统一标识">
            <Paragraph copyable style={{ marginBottom: 0 }}>{detail.identifier}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="资源类型">{detail.resource_type_label}</Descriptions.Item>
          <Descriptions.Item label="可见范围">{detail.visibility_scope}</Descriptions.Item>
          <Descriptions.Item label="馆藏对象 ID">{detail.collection_object_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColorMap[statusInfo.code] || 'default'}>{statusInfo.label}</Tag>
            {statusInfo.message && <Text style={{ marginLeft: 8 }}>{statusInfo.message}</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{detail.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="生命周期事件">
        <List bordered dataSource={detail.lifecycle} renderItem={renderLifecycleItem} />
      </Card>

      <Card title="处理时间线">
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
          <Alert type="warning" showIcon message="暂无处理时间线" />
        )}
      </Card>

      <Card title="文件结构">
        <Alert type="info" showIcon message={structure.summary || '暂无结构信息'} />

        <Divider orientation="left">主文件</Divider>
        {renderFileRecord(primaryFile, detail.title)}

        <Divider orientation="left">原始文件</Divider>
        {renderFileRecord(originalFile, detail.title)}

        <Divider orientation="left">衍生文件</Divider>
        {derivatives.length > 0 ? (
          <List
            bordered
            dataSource={derivatives}
            renderItem={(item: AssetDetailFileRecord) => (
              <List.Item>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text strong>{item.role_label || item.role || '-'}</Text>
                  <Text>文件名：{item.filename || '-'}</Text>
                  <Text>MIME 类型：{item.mime_type || '-'}</Text>
                  <Text>文件大小：{formatBytes(item.file_size)}</Text>
                  <Text>衍生方式：{item.derivation_method || '-'}</Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Alert type="warning" showIcon message="暂无衍生文件" />
        )}

        <Divider orientation="left">打包信息</Divider>
        <Alert
          type={structure.packaging?.bagit_supported ? 'success' : 'info'}
          showIcon
          message={structure.packaging?.bagit_note || '未配置 BagIt 打包输出'}
        />
      </Card>

      <Card title="技术元数据">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="宽度">{technicalMetadata.width ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="高度">{technicalMetadata.height ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="SHA256">
            {technicalMetadata.fixity_sha256 ? (
              <Paragraph copyable code style={{ marginBottom: 0 }}>{technicalMetadata.fixity_sha256}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="入库方式">{technicalMetadata.ingest_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="转换方式">{technicalMetadata.conversion_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="原始文件路径">{technicalMetadata.original_file_path ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="错误信息">{technicalMetadata.error_message ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {metadataLayers && (
        <Card title="分层元数据">
          <Alert
            type="info"
            showIcon
            message={`结构版本 ${metadataLayers.schema_version || '未知'} / 模板 ${metadataLayers.profile?.label || '未知'}`}
            style={{ marginBottom: 16 }}
          />

          {metadataLayers.core && Object.keys(metadataLayers.core).length > 0 && (
            <>
              <Divider orientation="left">平台核心信息</Divider>
              {renderMetadataSection(metadataLayers.core)}
            </>
          )}

          {metadataLayers.management && Object.keys(metadataLayers.management).length > 0 && (
            <>
              <Divider orientation="left">共享管理元数据</Divider>
              {renderMetadataSection(metadataLayers.management)}
            </>
          )}

          {metadataLayers.technical && Object.keys(metadataLayers.technical).length > 0 && (
            <>
              <Divider orientation="left">技术影像元数据</Divider>
              {renderMetadataSection(metadataLayers.technical)}
            </>
          )}

          {metadataLayers.profile?.fields && Object.keys(metadataLayers.profile.fields).length > 0 && (
            <>
              <Divider orientation="left">类型专属元数据</Divider>
              {renderMetadataSection(metadataLayers.profile.fields)}
            </>
          )}

          {metadataLayers.raw_metadata && Object.keys(metadataLayers.raw_metadata).length > 0 && (
            <>
              <Divider orientation="left">原始元数据</Divider>
              <pre style={{ maxHeight: 320, overflow: 'auto', fontSize: 12, marginBottom: 0 }}>
                {JSON.stringify(metadataLayers.raw_metadata, null, 2)}
              </pre>
            </>
          )}
        </Card>
      )}

      <Card title="访问与输出">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Manifest 地址">
            {manifestUrl ? <Paragraph copyable style={{ marginBottom: 0 }}>{manifestUrl}</Paragraph> : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="预览状态">{previewEnabled ? '可预览' : '不可预览'}</Descriptions.Item>
          <Descriptions.Item label="当前文件下载地址">
            {detail.output_actions.download_current_file?.url ? (
              <Paragraph copyable style={{ marginBottom: 0 }}>{detail.output_actions.download_current_file.url}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="BagIt 下载地址">
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
            打开 Mirador
          </Button>
          <Button
            icon={<LinkOutlined />}
            disabled={!manifestUrl}
            onClick={() => manifestUrl && window.open(manifestUrl, '_blank', 'noopener,noreferrer')}
          >
            查看 IIIF Manifest
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
            下载当前文件
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
            下载 BagIt 包
          </Button>
        </Space>
      </Card>
    </Space>
  );
};

export default AssetDetail;
