import React, { useCallback, useMemo, useState } from 'react';
import { Alert, Button, Card, Empty, Form, Input, List, Modal, Select, Space, Tag, Typography, message } from 'antd';
import { DatabaseOutlined, DeleteOutlined, FileDoneOutlined, FolderOpenOutlined, ImportOutlined, SearchOutlined, SortAscendingOutlined } from '@ant-design/icons';
import ImportDialog from './ImportDialog';
import type { ApplicationCartItem, ImportSelectionItem } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

interface ApplicationCartProps {
  items: ApplicationCartItem[];
  onRemove: (cartKey: string) => void;
  onUpdateNote: (cartKey: string, note: string) => void;
  onAddItem: (item: ApplicationCartItem) => boolean;
  onNavigateToDirectory: () => void;
  onSubmit: (payload: {
    requesterName: string;
    requesterOrg?: string;
    contactEmail?: string;
    purpose: string;
    usageScope?: string;
  }) => Promise<void>;
  submitting?: boolean;
}

/** Convert ImportSelectionItem (from ImportDialog) to ApplicationCartItem (cart state) */
function toCartItem(item: ImportSelectionItem, index: number): ApplicationCartItem {
  return {
    cartKey: `import-${item.sourceSystem}-${item.sourceId}-${Date.now()}-${index}`,
    sourceSystem: item.sourceSystem,
    sourceId: item.sourceId,
    title: item.title || '',
    resourceType: 'image_2d',
    objectNumber: item.objectNumber || undefined,
    manifestUrl: item.manifestUrl || '',
    note: item.note || undefined,
  };
}

const ApplicationCart: React.FC<ApplicationCartProps> = ({
  items, onRemove, onUpdateNote, onAddItem, onNavigateToDirectory, onSubmit, submitting = false,
}) => {
  const [form] = Form.useForm();
  const [importVisible, setImportVisible] = useState(false);
  const [importing, setImporting] = useState(false);
  const [sortKey, setSortKey] = useState('default');

  // Sort items
  const sortedItems = useMemo(() => {
    const list = [...items];
    switch (sortKey) {
      case 'object_number':
        list.sort((a, b) => (a.objectNumber || '').localeCompare(b.objectNumber || ''));
        break;
      case 'era':
        list.sort((a, b) => (a.era || '').localeCompare(b.era || ''));
        break;
      default:
        break;
    }
    return list;
  }, [items, sortKey]);

  const hint = items.length === 0
    ? '当前还没有待申请资源，先去统一资源目录加入资源，或通过批量导入快速添加。'
    : `当前已选 ${items.length} 项资源，可以统一提交成一张申请单。`;

  // ── Import handler ────────────────────────────────
  const handleImport = useCallback(async (importItems: ImportSelectionItem[]) => {
    if (importItems.length === 0) {
      message.warning('请至少选择一项');
      return;
    }
    setImporting(true);
    let added = 0;
    let skipped = 0;
    try {
      for (let i = 0; i < importItems.length; i++) {
        const cartItem = toCartItem(importItems[i], i);
        const ok = onAddItem(cartItem);
        if (ok) added++;
        else skipped++;
      }
      if (added > 0) {
        message.success(`成功导入 ${added} 项${skipped > 0 ? `，${skipped} 项已在车中` : ''}`);
      } else {
        message.info('所有项已在申请车中');
      }
      setImportVisible(false);
    } catch (err) {
      console.error('import failed', err);
      message.error('导入失败，请重试');
    } finally {
      setImporting(false);
    }
  }, [onAddItem]);

  if (items.length === 0) {
    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Empty description="申请车还是空的，先去统一资源目录加入资源。" />
        </Card>
        <div style={{ textAlign: 'center' }}>
          <Space>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              size="large"
              onClick={onNavigateToDirectory}
            >
              统一资源目录
            </Button>
            <Button
              type="default"
              icon={<ImportOutlined />}
              size="large"
              onClick={() => setImportVisible(true)}
            >
              批量导入
            </Button>
          </Space>
        </div>
        <ImportDialog
          visible={importVisible}
          onClose={() => setImportVisible(false)}
          onImport={handleImport}
        />
      </Space>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Tag color="blue">统一资源利用申请</Tag>
          <Title level={4} style={{ margin: 0 }}>
            申请车
          </Title>
          <Text type="secondary">这里先作为申请草稿区使用，后续提交后会进入正式审批流程。</Text>
        </Space>
      </Card>

      <Alert type="info" showIcon message="当前阶段说明" description={hint} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        <Space>
          <SortAscendingOutlined style={{ color: '#94a3b8' }} />
          <Select
            value={sortKey}
            onChange={setSortKey}
            size="small"
            style={{ width: 130 }}
            options={[
              { value: 'default', label: '默认顺序' },
              { value: 'object_number', label: '按文物号排序' },
              { value: 'era', label: '按年代排序' },
            ]}
          />
        </Space>

        <Space>
          <Button icon={<SearchOutlined />} onClick={onNavigateToDirectory}>
            统一资源目录
          </Button>
          <Button
            type="primary"
            icon={<ImportOutlined />}
            onClick={() => setImportVisible(true)}
          >
            批量导入
          </Button>
        </Space>
      </div>

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
          dataSource={sortedItems}
          renderItem={(item) => (
            <List.Item>
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Space wrap>
                    <Tag color="geekblue">{item.resourceType || '统一资源'}</Tag>
                    <Tag color="purple">
                      {item.sourceSystem && item.sourceId ? `${item.sourceSystem}/${item.sourceId}` : item.cartKey}
                    </Tag>
                    {item.objectNumber ? <Tag color="gold">{item.objectNumber}</Tag> : null}
                    {item.resourceType === 'image_2d_cultural_object' && item.era ? <Tag color="cyan">{item.era}</Tag> : null}
                    {item.resourceType === 'image_2d_cultural_object' && item.objectLevel ? <Tag color="orange">{item.objectLevel}</Tag> : null}
                    {item.sourceLabel ? <Tag>{item.sourceLabel}</Tag> : null}
                  </Space>

                  <div>
                    <Text strong>{item.title}</Text>
                    <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                      访问地址: {item.manifestUrl}
                    </Paragraph>
                  </div>

                  <Input.TextArea
                    rows={3}
                    placeholder="填写该资源的申请备注，例如用途、分辨率、交付说明。"
                    value={item.note || ''}
                    onChange={(event) => onUpdateNote(item.cartKey, event.target.value)}
                  />

                  <Space wrap>
                    <Button danger icon={<DeleteOutlined />} onClick={() => onRemove(item.cartKey)}>
                      移出申请车
                    </Button>
                  </Space>
                </Space>
              </Card>
            </List.Item>
          )}
        />
      </Card>

      <ImportDialog
        visible={importVisible}
        onClose={() => setImportVisible(false)}
        onImport={handleImport}
      />
    </Space>
  );
};

export default ApplicationCart;
