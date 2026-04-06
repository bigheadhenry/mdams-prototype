import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  AutoComplete,
  Button,
  Card,
  Checkbox,
  Col,
  Descriptions,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';
import type { AuthContext, AuthUserSummary } from '../auth/permissions';
import type {
  CulturalObjectLookupResponse,
  CulturalObjectSampleListResponse,
  ImageIngestSheetDetailResponse,
  ImageIngestSheetSavePayload,
  ImageIngestSheetSummary,
  ImageRecordDetailResponse,
  ImageRecordSavePayload,
  ImageRecordSummary,
} from '../types/assets';

const { Paragraph, Text, Title } = Typography;

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  in_progress: 'processing',
  completed: 'success',
  ready_for_upload: 'processing',
  returned: 'warning',
  uploaded_pending_validation: 'purple',
};

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  in_progress: '进行中',
  completed: '已完成',
  ready_for_upload: '待上传',
  returned: '已退回',
  uploaded_pending_validation: '已上传待校验',
};

const IMAGE_TYPE_OPTIONS = [
  { label: '文物影像', value: 'movable_artifact' },
  { label: '文物建筑影像', value: 'immovable_artifact' },
  { label: '艺术摄影影像', value: 'art_photography' },
  { label: '业务活动影像', value: 'business_activity' },
  { label: '全景影像', value: 'panorama' },
  { label: '古树影像', value: 'ancient_tree' },
  { label: '考古影像', value: 'archaeology' },
  { label: '其他影像', value: 'other' },
];

const PROJECT_TYPE_OPTIONS = [
  { label: '编目', value: 'catalogue' },
  { label: '采集', value: 'documentation' },
  { label: '研究', value: 'research' },
  { label: '保护修复', value: 'conservation' },
  { label: '活动', value: 'event' },
  { label: '其他', value: 'other' },
];

type ProfileFieldDefinition = {
  key: string;
  label: string;
  required?: boolean;
};

const PROFILE_FIELD_MAP: Record<string, ProfileFieldDefinition[]> = {
  movable_artifact: [
    { key: 'object_number', label: '文物号', required: true },
    { key: 'object_name', label: '文物名称' },
    { key: 'object_level', label: '文物级别' },
    { key: 'object_category', label: '文物类别' },
    { key: 'object_subcategory', label: '文物细类' },
    { key: 'management_group', label: '管理科组' },
    { key: 'photographer', label: '提照人员' },
    { key: 'photographer_phone', label: '提照人员电话' },
    { key: 'visible_to_custodians_only', label: '仅藏品管理者可见' },
  ],
  immovable_artifact: [
    { key: 'region_level_1', label: '一级区域' },
    { key: 'region_level_2', label: '二级区域' },
    { key: 'building_name', label: '文物建筑名称', required: true },
    { key: 'orientation', label: '方位' },
    { key: 'part_level_1', label: '部位一' },
    { key: 'part_level_2', label: '部位二' },
    { key: 'part_level_3', label: '部位三' },
    { key: 'building_component', label: '建筑构件' },
  ],
  art_photography: [
    { key: 'art_photography_type', label: '艺术摄影类型' },
    { key: 'collection_type', label: '藏品类型' },
    { key: 'palace_area', label: '所在宫区' },
    { key: 'season', label: '季节' },
    { key: 'plant', label: '植物' },
    { key: 'animal', label: '动物' },
    { key: 'solar_term', label: '节气' },
    { key: 'other', label: '其他' },
    { key: 'theme', label: '主题' },
    { key: 'cultural_topic', label: '文化专题' },
    { key: 'exhibition_topic', label: '展览专题' },
  ],
  business_activity: [
    { key: 'main_location', label: '主要地点', required: true },
    { key: 'main_person', label: '主要人物' },
  ],
  panorama: [
    { key: 'panorama_type', label: '全景类型' },
    { key: 'location', label: '位置' },
  ],
  ancient_tree: [
    { key: 'archive_number', label: '档案编号', required: true },
    { key: 'plant_type', label: '植物类型' },
    { key: 'plant_name', label: '植物名称' },
    { key: 'region', label: '所在区域' },
    { key: 'specific_location', label: '具体位置' },
    { key: 'grade', label: '等级' },
  ],
  archaeology: [{ key: 'archaeology_image_category', label: '考古影像分类' }],
  other: [],
};

function getStatusLabel(value?: string | null) {
  if (!value) return '-';
  return STATUS_LABELS[value] || value;
}

function getImageTypeLabel(value?: string | null) {
  if (!value) return '-';
  return IMAGE_TYPE_OPTIONS.find((item) => item.value === value)?.label || value;
}

type SheetFormValues = {
  title?: string;
  image_type?: string;
  project_type?: string;
  project_name?: string;
  assigned_photographer_user_id?: number | null;
  photographer_org?: string;
  copyright_owner?: string;
  capture_time?: string;
  remark?: string;
};

type ItemFormValues = {
  title?: string;
  visibility_scope?: string;
  collection_object_id?: number | null;
  management?: {
    capture_content?: string;
    tags_text?: string;
    representative_image?: boolean;
    identifier_type?: string;
    identifier_value?: string;
  };
  profile_fields?: Record<string, unknown>;
};

interface ImageRecordWorkbenchProps {
  authContext: AuthContext;
  availableUsers: AuthUserSummary[];
}

function toSheetFormValues(sheet: ImageIngestSheetDetailResponse | null): SheetFormValues {
  return {
    title: sheet?.title || '',
    image_type: sheet?.image_type || 'other',
    project_type: sheet?.project_type || undefined,
    project_name: sheet?.project_name || '',
    assigned_photographer_user_id: sheet?.assigned_photographer_user_id ?? null,
    photographer_org: sheet?.photographer_org || '',
    copyright_owner: sheet?.copyright_owner || '',
    capture_time: sheet?.capture_time || '',
    remark: sheet?.remark || '',
  };
}

function toItemFormValues(item: ImageRecordDetailResponse | null): ItemFormValues {
  const management = (item?.metadata_info.management as Record<string, unknown> | undefined) || {};
  const profileFields = (item?.metadata_info.profile?.fields as Record<string, unknown> | undefined) || {};

  return {
    title: item?.title || '',
    visibility_scope: item?.visibility_scope || 'open',
    collection_object_id: item?.collection_object_id ?? null,
    management: {
      capture_content: typeof management.capture_content === 'string' ? management.capture_content : '',
      tags_text: Array.isArray(management.tags) ? management.tags.join(', ') : typeof management.tags === 'string' ? management.tags : '',
      representative_image: Boolean(management.representative_image),
      identifier_type: typeof management.identifier_type === 'string' ? management.identifier_type : '',
      identifier_value: typeof management.identifier_value === 'string' ? management.identifier_value : '',
    },
    profile_fields: profileFields,
  };
}

const ImageRecordWorkbench: React.FC<ImageRecordWorkbenchProps> = ({ authContext, availableUsers }) => {
  const [sheetForm] = Form.useForm<SheetFormValues>();
  const [itemForm] = Form.useForm<ItemFormValues>();
  const [sheets, setSheets] = useState<ImageIngestSheetSummary[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<ImageIngestSheetDetailResponse | null>(null);
  const [selectedItem, setSelectedItem] = useState<ImageRecordDetailResponse | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [loadingSheetDetail, setLoadingSheetDetail] = useState(false);
  const [loadingItemDetail, setLoadingItemDetail] = useState(false);
  const [savingSheet, setSavingSheet] = useState(false);
  const [savingItem, setSavingItem] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [sampleLoading, setSampleLoading] = useState(false);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [sampleTotal, setSampleTotal] = useState(0);
  const [sampleOptions, setSampleOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [lookupHint, setLookupHint] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canCreate = authContext.permissions.includes('image.record.create');
  const canEdit = authContext.permissions.includes('image.record.edit');
  const canSubmit = authContext.permissions.includes('image.record.submit');
  const canReturn = authContext.permissions.includes('image.record.return');
  const canUpload = authContext.permissions.includes('image.file.upload');
  const canMatch = authContext.permissions.includes('image.file.match');

  const photographerOptions = useMemo(
    () =>
      availableUsers
        .filter((user) =>
          user.roles.some((role) => role.key === 'image_photographer_upload' || role.key === 'system_admin'),
        )
        .map((user) => ({
          label: `${user.display_name} (${user.username})`,
          value: user.id,
          displayName: user.display_name,
        })),
    [availableUsers],
  );

  const currentImageType = Form.useWatch('image_type', sheetForm) || selectedSheet?.image_type || 'other';
  const selectedProfileFields = PROFILE_FIELD_MAP[currentImageType] || PROFILE_FIELD_MAP.other;

  const loadSheets = useCallback(async () => {
    setLoadingSheets(true);
    try {
      const response = await axios.get<ImageIngestSheetSummary[]>('/api/image-records/sheets', {
        params: { q: searchValue || undefined },
      });
      setSheets(response.data);
    } catch (error) {
      console.error(error);
      message.error('加载录入单列表失败');
      setSheets([]);
    } finally {
      setLoadingSheets(false);
    }
  }, [searchValue]);

  const loadItemDetail = useCallback(async (itemId: number | null) => {
    if (!itemId) {
      setSelectedItemId(null);
      setSelectedItem(null);
      itemForm.setFieldsValue(toItemFormValues(null));
      setLookupHint('');
      return;
    }

    setLoadingItemDetail(true);
    try {
      const response = await axios.get<ImageRecordDetailResponse>(`/api/image-records/${itemId}`);
      setSelectedItemId(itemId);
      setSelectedItem(response.data);
      itemForm.setFieldsValue(toItemFormValues(response.data));
      setLookupHint('');
    } catch (error) {
      console.error(error);
      message.error('加载当前明细失败');
    } finally {
      setLoadingItemDetail(false);
    }
  }, [itemForm]);

  const loadSheetDetail = useCallback(async (sheetId: number, preferredItemId?: number | null) => {
    setLoadingSheetDetail(true);
    try {
      const response = await axios.get<ImageIngestSheetDetailResponse>(`/api/image-records/sheets/${sheetId}`);
      setSelectedSheet(response.data);
      sheetForm.setFieldsValue(toSheetFormValues(response.data));

      const fallbackItemId = preferredItemId ?? response.data.items[0]?.id ?? null;
      if (fallbackItemId) {
        void loadItemDetail(fallbackItemId);
      } else {
        setSelectedItem(null);
        setSelectedItemId(null);
        itemForm.setFieldsValue(toItemFormValues(null));
      }
    } catch (error) {
      console.error(error);
      message.error('加载录入单详情失败');
    } finally {
      setLoadingSheetDetail(false);
    }
  }, [itemForm, loadItemDetail, sheetForm]);

  const loadArtifactSamples = useCallback(async () => {
    setSampleLoading(true);
    try {
      const response = await axios.get<CulturalObjectSampleListResponse>('/api/image-records/artifact-samples');
      setSampleTotal(response.data.total);
      setSampleOptions(
        response.data.items.map((item) => ({
          value: item.object_number,
          label: `${item.object_number} | ${item.object_name || '-'}`,
        })),
      );
    } catch (error) {
      console.error(error);
    } finally {
      setSampleLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSheets();
  }, [loadSheets]);

  useEffect(() => {
    void loadArtifactSamples();
  }, [loadArtifactSamples]);

  const handleNewSheet = () => {
    setSelectedSheet(null);
    setSelectedItem(null);
    setSelectedItemId(null);
    setLookupHint('');
    sheetForm.setFieldsValue({
      title: '',
      image_type: 'movable_artifact',
      project_type: undefined,
      project_name: '',
      assigned_photographer_user_id: null,
      photographer_org: '',
      copyright_owner: '',
      capture_time: '',
      remark: '',
    });
    itemForm.setFieldsValue(toItemFormValues(null));
  };

  const handleNewItem = () => {
    setSelectedItem(null);
    setSelectedItemId(null);
    setLookupHint('');
    itemForm.setFieldsValue({
      title: '',
      visibility_scope: 'open',
      collection_object_id: null,
      management: {
        capture_content: '',
        tags_text: '',
        representative_image: false,
        identifier_type: '',
        identifier_value: '',
      },
      profile_fields: {},
    });
  };

  const saveSheet = async () => {
    const values = await sheetForm.validateFields();
    const selectedPhotographer = photographerOptions.find(
      (option) => option.value === values.assigned_photographer_user_id,
    );

    const payload: ImageIngestSheetSavePayload = {
      title: values.title || values.project_name || null,
      image_type: values.image_type || 'other',
      project_type: values.project_type || null,
      project_name: values.project_name || null,
      photographer: selectedPhotographer?.displayName || null,
      photographer_org: values.photographer_org || null,
      copyright_owner: values.copyright_owner || null,
      capture_time: values.capture_time || null,
      remark: values.remark || null,
      assigned_photographer_user_id: values.assigned_photographer_user_id ?? null,
      metadata_info: {},
    };

    setSavingSheet(true);
    try {
      if (selectedSheet) {
        const response = await axios.patch<ImageIngestSheetDetailResponse>(
          `/api/image-records/sheets/${selectedSheet.id}`,
          payload,
        );
        setSelectedSheet(response.data);
        sheetForm.setFieldsValue(toSheetFormValues(response.data));
        await loadSheets();
        message.success('录入单已保存');
      } else {
        const response = await axios.post<ImageIngestSheetDetailResponse>('/api/image-records/sheets', payload);
        await loadSheets();
        await loadSheetDetail(response.data.id);
        message.success('录入单已创建');
      }
    } catch (error) {
      console.error(error);
      message.error('保存录入单失败');
    } finally {
      setSavingSheet(false);
    }
  };

  const buildItemPayload = (values: ItemFormValues): ImageRecordSavePayload => {
    const tags = (values.management?.tags_text || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    return {
      title: values.title || null,
      visibility_scope: values.visibility_scope || 'open',
      collection_object_id: values.collection_object_id ?? null,
      profile_key: currentImageType,
      management: {
        image_name: values.title || null,
        capture_content: values.management?.capture_content || null,
        representative_image: Boolean(values.management?.representative_image),
        tags,
        identifier_type: values.management?.identifier_type || null,
        identifier_value: values.management?.identifier_value || null,
      },
      profile_fields: values.profile_fields || {},
      raw_metadata: {},
    };
  };

  const saveItem = async () => {
    if (!selectedSheet) {
      message.warning('请先新建或选择录入单');
      return;
    }

    const values = await itemForm.validateFields();
    const payload = buildItemPayload(values);
    setSavingItem(true);
    try {
      let response;
      if (selectedItemId) {
        response = await axios.patch<ImageRecordDetailResponse>(
          `/api/image-records/sheets/items/${selectedItemId}`,
          payload,
        );
      } else {
        response = await axios.post<ImageRecordDetailResponse>(
          `/api/image-records/sheets/${selectedSheet.id}/items`,
          payload,
        );
      }
      await loadSheetDetail(selectedSheet.id, response.data.id);
      await loadSheets();
      message.success(selectedItemId ? '明细已保存' : '明细已创建');
    } catch (error) {
      console.error(error);
      message.error('保存明细失败');
    } finally {
      setSavingItem(false);
    }
  };

  const submitSelectedItem = async () => {
    if (!selectedItemId || !selectedSheet) return;
    setActionLoading(true);
    try {
      await axios.post(`/api/image-records/${selectedItemId}/submit`);
      await loadSheetDetail(selectedSheet.id, selectedItemId);
      await loadSheets();
      message.success('明细已提交，进入待上传');
    } catch (error) {
      console.error(error);
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      if (detail?.missing_labels) {
        message.error(`缺少必填项：${detail.missing_labels.join('、')}`);
      } else {
        message.error('提交明细失败');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const returnSelectedItem = async () => {
    if (!selectedItemId || !selectedSheet) return;
    setActionLoading(true);
    try {
      await axios.post(`/api/image-records/${selectedItemId}/return`, { note: 'Returned from sheet workbench' });
      await loadSheetDetail(selectedSheet.id, selectedItemId);
      await loadSheets();
      message.success('明细已退回');
    } catch (error) {
      console.error(error);
      message.error('退回明细失败');
    } finally {
      setActionLoading(false);
    }
  };

  const uploadTempFile = async (file: File) => {
    if (!selectedItemId || !selectedSheet) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    try {
      await axios.post(`/api/image-records/${selectedItemId}/upload-temp`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await loadSheetDetail(selectedSheet.id, selectedItemId);
      message.success('候选文件已上传并完成分析');
    } catch (error) {
      console.error(error);
      message.error('上传候选文件失败');
    } finally {
      setUploading(false);
    }
  };

  const confirmMatch = async (mode: 'bind' | 'replace') => {
    if (!selectedItemId || !selectedItem?.pending_upload || !selectedSheet) return;
    setActionLoading(true);
    try {
      await axios.post(`/api/image-records/${selectedItemId}/${mode === 'bind' ? 'confirm-bind' : 'confirm-replace'}`, {
        temp_upload_token: selectedItem.pending_upload.token,
      });
      await loadSheetDetail(selectedSheet.id, selectedItemId);
      await loadSheets();
      message.success(mode === 'bind' ? '已确认绑定资产' : '已确认替换资产');
    } catch (error) {
      console.error(error);
      message.error(mode === 'bind' ? '确认绑定失败' : '确认替换失败');
    } finally {
      setActionLoading(false);
    }
  };

  const runArtifactLookup = async (value?: string) => {
    const objectNumber = (value || String(itemForm.getFieldValue(['profile_fields', 'object_number']) || '')).trim();
    if (!objectNumber) return;

    setLookupLoading(true);
    try {
      const response = await axios.get<CulturalObjectLookupResponse>('/api/image-records/artifact-lookup', {
        params: { object_number: objectNumber },
      });
      setLookupHint(response.data.message || '');
      if (response.data.record) {
        const current = (itemForm.getFieldValue('profile_fields') || {}) as Record<string, unknown>;
        itemForm.setFieldsValue({
          profile_fields: {
            ...current,
            object_number: response.data.record.object_number,
            object_name: response.data.record.object_name || current.object_name,
            object_level: response.data.record.object_level || current.object_level,
            object_category: response.data.record.object_category || current.object_category,
            object_subcategory: response.data.record.object_subcategory || current.object_subcategory,
            management_group: response.data.record.management_group || current.management_group,
          },
        });
      }
    } catch (error) {
      console.error(error);
      setLookupHint('');
      message.error('文物号查询失败');
    } finally {
      setLookupLoading(false);
    }
  };

  const itemColumns: ColumnsType<ImageRecordSummary> = [
    { title: '行号', dataIndex: 'line_no', key: 'line_no', width: 70 },
    { title: '影像名称', dataIndex: 'title', key: 'title', render: (value: string) => value || '-' },
    {
      title: '文物号',
      dataIndex: 'object_number',
      key: 'object_number',
      width: 140,
      render: (value: string | null | undefined) => value || '-',
    },
    {
      title: '代表影像',
      dataIndex: 'representative_image',
      key: 'representative_image',
      width: 120,
      render: (value: boolean | undefined) => (value ? <Tag color="gold">是</Tag> : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 160,
      render: (value: string) => <Tag color={STATUS_COLORS[value] || 'default'}>{getStatusLabel(value)}</Tag>,
    },
  ];

  return (
    <Row gutter={16} align="top">
      <Col span={7}>
        <Card
          title="录入单列表"
          extra={
            <Button type="primary" onClick={handleNewSheet} disabled={!canCreate}>
              新建录入单
            </Button>
          }
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <Input.Search
              allowClear
              placeholder="搜索录入单"
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              onSearch={() => void loadSheets()}
            />
            <Spin spinning={loadingSheets}>
              <List
                bordered
                dataSource={sheets}
                locale={{ emptyText: <Empty description="暂无录入单" /> }}
                renderItem={(sheet) => (
                  <List.Item
                    style={{
                      cursor: 'pointer',
                      background: selectedSheet?.id === sheet.id ? '#f5faff' : undefined,
                    }}
                    onClick={() => void loadSheetDetail(sheet.id)}
                  >
                    <Space direction="vertical" size={2} style={{ width: '100%' }}>
                      <Space>
                        <Text strong>{sheet.sheet_no}</Text>
                        <Tag color={STATUS_COLORS[sheet.status] || 'default'}>{getStatusLabel(sheet.status)}</Tag>
                      </Space>
                      <Text>{sheet.project_name || sheet.title || '-'}</Text>
                      <Text type="secondary">
                        {getImageTypeLabel(sheet.image_type)} | {sheet.item_count} 条明细 | 已上传 {sheet.uploaded_item_count} 条
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Spin>
          </Space>
        </Card>
      </Col>

      <Col span={17}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Card
            title="录入单头信息"
            extra={
              <Button
                type="primary"
                loading={savingSheet}
                onClick={() => void saveSheet()}
                disabled={!canCreate && !canEdit}
              >
                保存录入单
              </Button>
            }
          >
            <Form<SheetFormValues> form={sheetForm} layout="vertical">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="image_type" label="影像类型" rules={[{ required: true, message: '请选择影像类型' }]}>
                    <Select options={IMAGE_TYPE_OPTIONS} disabled={Boolean(selectedSheet?.items.length)} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="project_type" label="项目类型">
                    <Select allowClear options={PROJECT_TYPE_OPTIONS} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="assigned_photographer_user_id" label="摄影师" rules={[{ required: true, message: '请选择摄影师' }]}>
                    <Select allowClear options={photographerOptions} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="photographer_org" label="摄影师单位">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="capture_time" label="拍摄时间" rules={[{ required: true, message: '请输入拍摄时间' }]}>
                    <Input placeholder="例如：2026-04-06" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="copyright_owner" label="版权所有">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="title" label="录入单标题">
                    <Input placeholder="可选，便于识别该批次" />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="remark" label="备注">
                    <Input.TextArea rows={2} />
                  </Form.Item>
                </Col>
              </Row>
            </Form>

            {selectedSheet ? (
              <Descriptions size="small" column={4}>
                <Descriptions.Item label="录入单号">{selectedSheet.sheet_no}</Descriptions.Item>
                <Descriptions.Item label="状态">{getStatusLabel(selectedSheet.status)}</Descriptions.Item>
                <Descriptions.Item label="明细数量">{selectedSheet.item_count}</Descriptions.Item>
                <Descriptions.Item label="已上传">{selectedSheet.uploaded_item_count}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                新建录入单后即可开始批次化录入。
              </Paragraph>
            )}
          </Card>

          <Row gutter={16} align="top">
            <Col span={10}>
              <Card
                title="明细列表"
                extra={
                  <Button onClick={handleNewItem} disabled={!selectedSheet || !canCreate}>
                    新建明细
                  </Button>
                }
              >
                {selectedSheet ? (
                  <Spin spinning={loadingSheetDetail}>
                    <Table<ImageRecordSummary>
                      rowKey="id"
                      size="small"
                      pagination={false}
                      columns={itemColumns}
                      dataSource={selectedSheet.items}
                      locale={{ emptyText: '暂无明细' }}
                      onRow={(record) => ({
                        onClick: () => {
                          void loadItemDetail(record.id);
                        },
                      })}
                    />
                  </Spin>
                ) : (
                  <Empty description="请先选择或新建录入单" />
                )}
              </Card>
            </Col>

            <Col span={14}>
              <Card
                title="明细编辑区"
                extra={
                  <Space>
                    <Button onClick={handleNewItem} disabled={!selectedSheet}>
                      重置
                    </Button>
                    <Button
                      type="primary"
                      loading={savingItem}
                      onClick={() => void saveItem()}
                      disabled={!selectedSheet || (!canCreate && !canEdit)}
                    >
                      {selectedItemId ? '保存明细' : '创建明细'}
                    </Button>
                  </Space>
                }
              >
                {selectedSheet ? (
                  <Spin spinning={loadingItemDetail}>
                    <Form<ItemFormValues> form={itemForm} layout="vertical">
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            name="title"
                            label="影像名称"
                            rules={[{ required: true, message: '请输入影像名称' }]}
                          >
                            <Input />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name="visibility_scope" label="可见范围">
                            <Select
                              options={[
                                { label: '公开', value: 'open' },
                                { label: '仅责任馆藏', value: 'owner_only' },
                              ]}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name="collection_object_id" label="馆藏对象 ID">
                            <InputNumber style={{ width: '100%' }} />
                          </Form.Item>
                        </Col>
                        <Col span={24}>
                          <Form.Item name={['management', 'capture_content']} label="拍摄内容">
                            <Input.TextArea rows={2} />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item name={['management', 'tags_text']} label="标签">
                            <Input placeholder="多个标签请用逗号分隔" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name={['management', 'identifier_type']} label="对象标识符类型">
                            <Input />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item name={['management', 'identifier_value']} label="对象标识符值">
                            <Input />
                          </Form.Item>
                        </Col>
                        {currentImageType === 'movable_artifact' ? (
                          <Col span={24}>
                            <Form.Item name={['management', 'representative_image']} valuePropName="checked">
                              <Checkbox>设为该文物代表影像</Checkbox>
                            </Form.Item>
                          </Col>
                        ) : null}
                      </Row>

                      <Divider style={{ marginTop: 8, marginBottom: 16 }} />
                      <Title level={5}>类型专属字段</Title>

                      {currentImageType === 'movable_artifact' ? (
                        <Alert
                          type="info"
                          showIcon
                          style={{ marginBottom: 16 }}
                          message={`前端联调样本：${sampleLoading ? '加载中...' : `${sampleTotal} 条`}`}
                          description="输入文物号后会自动调用模拟文物接口回填信息，也支持使用“暂无号”。"
                        />
                      ) : null}

                      <Row gutter={16}>
                        {selectedProfileFields.map((field) => {
                          const rules = field.required ? [{ required: true, message: `请输入${field.label}` }] : undefined;
                          if (field.key === 'object_number' && currentImageType === 'movable_artifact') {
                            return (
                              <Col span={12} key={field.key}>
                                <Form.Item name={['profile_fields', field.key]} label={field.label} rules={rules}>
                                  <AutoComplete
                                    options={sampleOptions}
                                    onSelect={(value) => {
                                      itemForm.setFieldValue(['profile_fields', 'object_number'], value);
                                      void runArtifactLookup(value);
                                    }}
                                  >
                                    <Input.Search
                                      allowClear
                                      enterButton="查询"
                                      loading={lookupLoading}
                                      onSearch={(value) => void runArtifactLookup(value)}
                                      onBlur={() => {
                                        const objectNumber = String(itemForm.getFieldValue(['profile_fields', 'object_number']) || '').trim();
                                        if (objectNumber) {
                                          void runArtifactLookup(objectNumber);
                                        }
                                      }}
                                    />
                                  </AutoComplete>
                                </Form.Item>
                              </Col>
                            );
                          }

                          if (field.key === 'visible_to_custodians_only') {
                            return (
                              <Col span={12} key={field.key}>
                                <Form.Item name={['profile_fields', field.key]} valuePropName="checked">
                                  <Checkbox>{field.label}</Checkbox>
                                </Form.Item>
                              </Col>
                            );
                          }

                          return (
                            <Col span={12} key={field.key}>
                              <Form.Item name={['profile_fields', field.key]} label={field.label} rules={rules}>
                                <Input />
                              </Form.Item>
                            </Col>
                          );
                        })}
                      </Row>

                      {lookupHint ? (
                        <Alert type="success" showIcon style={{ marginBottom: 16 }} message={lookupHint} />
                      ) : null}

                      {selectedItem ? (
                        <>
                          {!selectedItem.validation.ready_for_submit ? (
                            <Alert
                              type="warning"
                              showIcon
                              style={{ marginBottom: 16 }}
                              message="当前明细仍有必填项未完成，暂不能提交。"
                              description={selectedItem.validation.missing_labels.join('、')}
                            />
                          ) : null}

                          <Space style={{ marginBottom: 16 }} wrap>
                            {canSubmit && (selectedItem.status === 'draft' || selectedItem.status === 'returned') ? (
                              <Button type="primary" loading={actionLoading} onClick={() => void submitSelectedItem()}>
                                提交明细
                              </Button>
                            ) : null}
                            {canReturn && selectedItem.status === 'ready_for_upload' ? (
                              <Button loading={actionLoading} onClick={() => void returnSelectedItem()}>
                                退回明细
                              </Button>
                            ) : null}
                            {canUpload ? (
                              <>
                                <input
                                  ref={fileInputRef}
                                  type="file"
                                  style={{ display: 'none' }}
                                  accept=".jpg,.jpeg,.png,.tif,.tiff,.psd,.psb"
                                  onChange={(event) => {
                                    const nextFile = event.target.files?.[0];
                                    if (nextFile) {
                                      void uploadTempFile(nextFile);
                                    }
                                    event.target.value = '';
                                  }}
                                />
                                <Button loading={uploading} onClick={() => fileInputRef.current?.click()}>
                                  上传候选文件
                                </Button>
                              </>
                            ) : null}
                            {canMatch && selectedItem.pending_upload?.can_confirm_bind ? (
                              <Button loading={actionLoading} onClick={() => void confirmMatch('bind')}>
                                确认绑定
                              </Button>
                            ) : null}
                            {canMatch && selectedItem.pending_upload?.can_confirm_replace ? (
                              <Button danger loading={actionLoading} onClick={() => void confirmMatch('replace')}>
                                确认替换
                              </Button>
                            ) : null}
                          </Space>

                          <Descriptions bordered size="small" column={2}>
                            <Descriptions.Item label="记录号">{selectedItem.record_no}</Descriptions.Item>
                            <Descriptions.Item label="状态">{getStatusLabel(selectedItem.status)}</Descriptions.Item>
                            <Descriptions.Item label="摄影师">
                              {selectedItem.assigned_photographer_display_name || '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="当前资产">
                              {selectedItem.asset ? selectedItem.asset.filename || `资产 #${selectedItem.asset.asset_id}` : '暂无绑定'}
                            </Descriptions.Item>
                          </Descriptions>

                          {selectedItem.pending_upload ? (
                            <Alert
                              style={{ marginTop: 16 }}
                              type="info"
                              showIcon
                              message={`待确认文件：${selectedItem.pending_upload.filename}`}
                              description={selectedItem.pending_upload.warnings.join(' | ') || '文件已准备好，可继续确认。'}
                            />
                          ) : null}
                        </>
                      ) : (
                        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                          请先保存明细，再进行提交、上传和绑定操作。
                        </Paragraph>
                      )}
                    </Form>
                  </Spin>
                ) : (
                  <Empty description="请先选择或新建录入单" />
                )}
              </Card>
            </Col>
          </Row>
        </Space>
      </Col>
    </Row>
  );
};

export default ImageRecordWorkbench;
