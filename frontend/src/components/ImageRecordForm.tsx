import React, { useEffect } from 'react';
import { Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Typography } from 'antd';
import type { AuthUserSummary } from '../auth/permissions';
import type { ImageRecordDetailResponse, ImageRecordSavePayload } from '../types/assets';

const { Paragraph, Text } = Typography;

type ProfileFieldDefinition = {
  key: string;
  label: string;
  requiredHint?: boolean;
};

const profileOptions = [
  { label: '可移动文物', value: 'movable_artifact' },
  { label: '不可移动文物', value: 'immovable_artifact' },
  { label: '业务活动', value: 'business_activity' },
  { label: '古树', value: 'ancient_tree' },
  { label: '其他', value: 'other' },
];

const profileFieldMap: Record<string, ProfileFieldDefinition[]> = {
  movable_artifact: [
    { key: 'object_number', label: '文物号' },
    { key: 'object_name', label: '文物名称', requiredHint: true },
    { key: 'object_level', label: '文物级别' },
  ],
  immovable_artifact: [
    { key: 'building_name', label: '文物建筑名称', requiredHint: true },
    { key: 'orientation', label: '方位' },
    { key: 'building_component', label: '建筑构件' },
  ],
  business_activity: [
    { key: 'main_location', label: '主要地点', requiredHint: true },
    { key: 'main_person', label: '主要人物' },
  ],
  ancient_tree: [
    { key: 'archive_number', label: '档案编号', requiredHint: true },
    { key: 'plant_name', label: '植物名称' },
    { key: 'region', label: '所在区域' },
  ],
  other: [],
};

interface ImageRecordFormValues {
  record_no?: string;
  title?: string;
  visibility_scope?: string;
  collection_object_id?: number | null;
  profile_key?: string;
  assigned_photographer_user_id?: number | null;
  management?: Record<string, unknown>;
  profile_fields?: Record<string, unknown>;
}

interface ImageRecordFormProps {
  record: ImageRecordDetailResponse | null;
  availableUsers: AuthUserSummary[];
  saving: boolean;
  onCancel: () => void;
  onSave: (payload: ImageRecordSavePayload) => Promise<void>;
}

function toInitialValues(record: ImageRecordDetailResponse | null): ImageRecordFormValues {
  const metadata = record?.metadata_info;
  const management = (metadata?.management as Record<string, unknown> | undefined) || {};
  const profileFields = (metadata?.profile?.fields as Record<string, unknown> | undefined) || {};

  return {
    record_no: record?.record_no || '',
    title: record?.title || '',
    visibility_scope: record?.visibility_scope || 'open',
    collection_object_id: record?.collection_object_id ?? null,
    profile_key: record?.profile_key || 'other',
    assigned_photographer_user_id: record?.assigned_photographer_user_id ?? null,
    management,
    profile_fields: profileFields,
  };
}

const ImageRecordForm: React.FC<ImageRecordFormProps> = ({ record, availableUsers, saving, onCancel, onSave }) => {
  const [form] = Form.useForm<ImageRecordFormValues>();
  const profileKey = Form.useWatch('profile_key', form) || record?.profile_key || 'other';

  useEffect(() => {
    form.setFieldsValue(toInitialValues(record));
  }, [form, record]);

  const submit = async (values: ImageRecordFormValues) => {
    await onSave({
      record_no: values.record_no || null,
      title: values.title || null,
      visibility_scope: values.visibility_scope || 'open',
      collection_object_id: values.collection_object_id ?? null,
      profile_key: values.profile_key || 'other',
      assigned_photographer_user_id:
        typeof values.assigned_photographer_user_id === 'number' ? values.assigned_photographer_user_id : null,
      management: values.management || {},
      profile_fields: values.profile_fields || {},
      raw_metadata: {},
    });
  };

  const selectedProfileFields = profileFieldMap[profileKey] || profileFieldMap.other;

  return (
    <Card
      title={record ? `编辑影像记录 ${record.record_no}` : '新建影像记录'}
      extra={
        <Space>
          <Button onClick={onCancel}>取消</Button>
          <Button type="primary" loading={saving} onClick={() => void form.submit()}>
            保存草稿
          </Button>
        </Space>
      }
      data-testid="image-record-form"
    >
      <Paragraph type="secondary">
        草稿保存尽量宽松。提交到待上传时，系统会检查项目名称、影像类别和 profile 必填字段。
      </Paragraph>

      <Form<ImageRecordFormValues> form={form} layout="vertical" onFinish={(values) => void submit(values)}>
        <Card size="small" title="核心信息" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="record_no" label="记录号">
                <Input placeholder="留空则由系统生成" />
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item name="title" label="标题">
                <Input placeholder="输入影像记录标题" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="visibility_scope" label="可见范围" initialValue="open">
                <Select
                  options={[
                    { label: '开放', value: 'open' },
                    { label: '责任人可见', value: 'owner_only' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="collection_object_id" label="藏品对象 ID">
                <InputNumber style={{ width: '100%' }} placeholder="可选" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="profile_key" label="Profile" initialValue="other">
                <Select options={profileOptions} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card size="small" title="管理信息" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name={['management', 'project_name']} label="项目名称">
                <Input placeholder="提交时必填" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name={['management', 'image_category']} label="影像类别">
                <Input placeholder="提交时必填" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="assigned_photographer_user_id" label="分配摄影人员">
                <Select
                  allowClear
                  placeholder="可选"
                  options={availableUsers
                    .filter((user) =>
                      user.roles.some((role) => role.key === 'image_photographer_upload' || role.key === 'system_admin'),
                    )
                    .map((user) => ({
                      label: `${user.display_name} (${user.username})`,
                      value: user.id,
                    }))}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name={['management', 'photographer']} label="摄影者">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name={['management', 'photographer_org']} label="摄影者单位">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name={['management', 'capture_time']} label="拍摄时间">
                <Input placeholder="例如 2026-04-06" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name={['management', 'capture_content']} label="拍摄内容">
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name={['management', 'remark']} label="备注">
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card size="small" title="Profile 信息">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">
              当前 profile: <Text strong>{profileOptions.find((item) => item.value === profileKey)?.label || profileKey}</Text>
            </Text>
            <Row gutter={16}>
              {selectedProfileFields.length === 0 ? (
                <Col span={24}>
                  <Text type="secondary">当前 profile 暂无专属字段。</Text>
                </Col>
              ) : (
                selectedProfileFields.map((field) => (
                  <Col span={8} key={field.key}>
                    <Form.Item
                      name={['profile_fields', field.key]}
                      label={field.requiredHint ? `${field.label}（提交必填）` : field.label}
                    >
                      <Input />
                    </Form.Item>
                  </Col>
                ))
              )}
            </Row>
          </Space>
        </Card>
      </Form>
    </Card>
  );
};

export default ImageRecordForm;
