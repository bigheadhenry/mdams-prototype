import React from 'react';
import { Alert, Button, Card, Empty, Form, Input, List, Space, Tag, Typography } from 'antd';
import { DeleteOutlined, FileDoneOutlined } from '@ant-design/icons';
import type { ApplicationCartItem } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

interface ApplicationCartProps {
  items: ApplicationCartItem[];
  onRemove: (assetId: number) => void;
  onUpdateNote: (assetId: number, note: string) => void;
  onSubmit: (payload: {
    requesterName: string;
    requesterOrg?: string;
    contactEmail?: string;
    purpose: string;
    usageScope?: string;
  }) => Promise<void>;
  submitting?: boolean;
}

const ApplicationCart: React.FC<ApplicationCartProps> = ({ items, onRemove, onUpdateNote, onSubmit, submitting = false }) => {
  const [form] = Form.useForm();

  const hint = items.length === 0 ? '当前还没有待申请资源，先去预览或列表里加入图片。' : `当前已选 ${items.length} 项资源，可以统一提交成一张申请单。`;

  if (items.length === 0) {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Empty description="申请车还是空的，先去预览或列表里加入图片。" />
        </Card>
      </Space>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Tag color="blue">二维影像利用申请</Tag>
          <Title level={4} style={{ margin: 0 }}>
            申请车
          </Title>
          <Text type="secondary">这里先作为申请草稿区使用，后续提交后会进入正式审批流程。</Text>
        </Space>
      </Card>

      <Alert type="info" showIcon message="当前阶段说明" description={hint} />

      <Card title="申请信息">
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            await onSubmit({
              requesterName: values.requesterName,
              requesterOrg: values.requesterOrg,
              contactEmail: values.contactEmail,
              purpose: values.purpose,
              usageScope: values.usageScope,
            });
            form.resetFields();
          }}
        >
          <Form.Item name="requesterName" label="申请人" rules={[{ required: true, message: '请填写申请人姓名' }]}>
            <Input placeholder="例如：Jing Sun" />
          </Form.Item>
          <Form.Item name="requesterOrg" label="所属机构">
            <Input placeholder="例如：故宫博物院" />
          </Form.Item>
          <Form.Item name="contactEmail" label="联系邮箱">
            <Input placeholder="例如：bigheadhenry@gmail.com" />
          </Form.Item>
          <Form.Item name="purpose" label="申请用途" rules={[{ required: true, message: '请填写申请用途' }]}>
            <Input.TextArea rows={3} placeholder="例如：出版配图、展览说明、研究引用" />
          </Form.Item>
          <Form.Item name="usageScope" label="使用范围">
            <Input placeholder="例如：内部研究 / 对外出版 / 展览展示" />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<FileDoneOutlined />} loading={submitting}>
            提交申请单
          </Button>
        </Form>
      </Card>

      <Card title="申请明细">
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item>
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Space wrap>
                    <Tag color="geekblue">Asset #{item.assetId}</Tag>
                    <Tag color="purple">
                      {item.sourceSystem && item.sourceId ? `${item.sourceSystem}/${item.sourceId}` : `Asset #${item.assetId}`}
                    </Tag>
                    {item.objectNumber ? <Tag color="gold">{item.objectNumber}</Tag> : null}
                    {item.sourceLabel ? <Tag>{item.sourceLabel}</Tag> : null}
                  </Space>

                  <div>
                    <Text strong>{item.title}</Text>
                    <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                      Manifest: {item.manifestUrl}
                    </Paragraph>
                  </div>

                  <Input.TextArea
                    rows={3}
                    placeholder="填写该资源的申请备注，例如用途、分辨率、交付说明。"
                    value={item.note || ''}
                    onChange={(event) => onUpdateNote(item.assetId, event.target.value)}
                  />

                  <Space wrap>
                    <Button danger icon={<DeleteOutlined />} onClick={() => onRemove(item.assetId)}>
                      移出申请车
                    </Button>
                  </Space>
                </Space>
              </Card>
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
};

export default ApplicationCart;
