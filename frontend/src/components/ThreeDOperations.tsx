import React, { useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  message,
  Row,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import { ExclamationCircleOutlined, ReloadOutlined, SyncOutlined, ToolOutlined } from '@ant-design/icons';
import axios from 'axios';
import type { ThreeDAssetSummary, ThreeDObjectGroup } from '../types/assets';

const { Text, Title } = Typography;

interface ThreeDOperationsProps {
  groupedItems: ThreeDObjectGroup[];
  onRefresh: () => void;
}

const ThreeDOperations: React.FC<ThreeDOperationsProps> = ({ groupedItems, onRefresh }) => {
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());

  const handleRegenPreview = async (id: number) => {
    setProcessingIds((prev) => new Set(prev).add(id));
    try {
      await axios.post(`/api/three-d/resources/${id}/regenerate-preview`);
      message.success(`资源 #${id} 预览再生已触发`);
      onRefresh();
    } catch {
      message.error(`资源 #${id} 预览再生失败`);
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleBatchRegen = async () => {
    const ids = errorItems.map((i) => i.id);
    for (const id of ids) {
      await handleRegenPreview(id);
    }
  };

  const handleResetStatus = async (id: number) => {
    try {
      await axios.patch(`/api/three-d/resources/${id}`, { status: 'ready' });
      message.success(`资源 #${id} 状态已复位`);
      onRefresh();
    } catch {
      message.error('操作失败');
    }
  };

  // 收集所有版本层面的异常项
  const errorItems: ThreeDAssetSummary[] = [];
  const missingPreviewItems: ThreeDAssetSummary[] = [];
  const processingItems: ThreeDAssetSummary[] = [];

  groupedItems.forEach((group) => {
    group.versions.forEach((v) => {
      if (v.status === 'error') errorItems.push(v);
      else if (v.status === 'processing') processingItems.push(v);
      if (v.is_web_preview && !v.preview_data?.frames?.length) {
        missingPreviewItems.push(v);
      }
    });
  });

  const combinedIssues = [
    ...errorItems.map((v) => ({ ...v, issue: 'error' as const })),
    ...missingPreviewItems
      .filter((v) => !errorItems.some((e) => e.id === v.id))
      .map((v) => ({ ...v, issue: 'missing_preview' as const })),
    ...processingItems
      .filter((v) => !errorItems.some((e) => e.id === v.id))
      .map((v) => ({ ...v, issue: 'processing' as const })),
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card bordered={false}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>
            <ToolOutlined /> 运维与处置
          </Title>
          <Text type="secondary">
            管理预览再生、异常修复、保存层迁移等运维操作。
          </Text>
        </Space>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Text type="secondary">异常表现</Text>
            <Title level={3} style={{ margin: 0, color: errorItems.length > 0 ? '#ff4d4f' : '#52c41a' }}>
              {errorItems.length}
            </Title>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Text type="secondary">处理中</Text>
            <Title level={3} style={{ margin: 0, color: processingItems.length > 0 ? '#faad14' : '#52c41a' }}>
              {processingItems.length}
            </Title>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Text type="secondary">缺预览帧</Text>
            <Title level={3} style={{ margin: 0, color: missingPreviewItems.length > 0 ? '#faad14' : '#52c41a' }}>
              {missingPreviewItems.length}
            </Title>
          </Card>
        </Col>
      </Row>

      {/* 预览再生 */}
      <Card
        title="预览动画再生"
        size="small"
        extra={
          missingPreviewItems.length > 0 && (
            <Button size="small" type="primary" icon={<SyncOutlined />} onClick={handleBatchRegen}>
              批量再生 ({missingPreviewItems.length})
            </Button>
          )
        }
      >
        {missingPreviewItems.length === 0 ? (
          <Alert type="success" showIcon message="所有已标记 Web 展示的表现均有预览帧。" />
        ) : (
          <Table
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10 }}
            dataSource={missingPreviewItems}
            columns={[
              { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
              {
                title: '标题',
                key: 'title',
                render: (_, r) => <Text>{r.title || r.filename}</Text>,
              },
              {
                title: '版本',
                dataIndex: 'version_label',
                key: 'vl',
                width: 120,
                render: (v: string) => <Tag>{v || 'v1'}</Tag>,
              },
              {
                title: '操作',
                key: 'action',
                width: 160,
                render: (_, r) => (
                  <Button
                    size="small"
                    icon={<ReloadOutlined />}
                    loading={processingIds.has(r.id)}
                    onClick={() => handleRegenPreview(r.id)}
                  >
                    再生预览
                  </Button>
                ),
              },
            ]}
          />
        )}
      </Card>

      {/* 异常处理 */}
      <Card
        title="异常与处理中"
        size="small"
        extra={
          errorItems.length > 0 && (
            <Button
              size="small"
              danger
              icon={<ExclamationCircleOutlined />}
              onClick={() => {
                errorItems.forEach((item) => handleResetStatus(item.id));
              }}
            >
              全部复位
            </Button>
          )
        }
      >
        {combinedIssues.length === 0 ? (
          <Alert type="success" showIcon message="所有表现状态正常。" />
        ) : (
          <Table
            rowKey={(r) => `${r.issue}-${r.id}`}
            size="small"
            pagination={{ pageSize: 10 }}
            dataSource={combinedIssues}
            columns={[
              { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
              {
                title: '标题',
                key: 'title',
                render: (_, r) => <Text>{r.title || r.filename}</Text>,
              },
              {
                title: '问题',
                key: 'issue',
                width: 120,
                render: (_, r) => {
                  if (r.issue === 'error') return <Tag color="red">异常</Tag>;
                  if (r.issue === 'processing') return <Tag color="blue">处理中</Tag>;
                  return <Tag color="orange">缺预览</Tag>;
                },
              },
              {
                title: '状态',
                dataIndex: 'status',
                key: 'st',
                width: 100,
                render: (v: string) => (
                  <Tag color={v === 'ready' ? 'green' : v === 'error' ? 'red' : 'blue'}>
                    {v}
                  </Tag>
                ),
              },
              {
                title: '操作',
                key: 'action',
                width: 180,
                render: (_, r) => (
                  <Space size={0}>
                    {r.issue === 'error' && (
                      <Button size="small" onClick={() => handleResetStatus(r.id)}>复位</Button>
                    )}
                    {r.issue === 'missing_preview' && (
                      <Button size="small" icon={<ReloadOutlined />} loading={processingIds.has(r.id)}
                        onClick={() => handleRegenPreview(r.id)}>再生</Button>
                    )}
                    {r.issue === 'processing' && (
                      <Button size="small" onClick={() => handleResetStatus(r.id)}>强制完成</Button>
                    )}
                  </Space>
                ),
              },
            ]}
          />
        )}
      </Card>
    </Space>
  );
};

export default ThreeDOperations;
