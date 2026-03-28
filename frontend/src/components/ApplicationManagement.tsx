import React, { useMemo, useState } from 'react';
import { Button, Card, Empty, Input, Modal, Space, Table, Tag, Typography, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Key } from 'react';
import type { ApplicationSummary } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

interface ApplicationManagementProps {
  applications: ApplicationSummary[];
  onApprove: (applicationId: number, reviewNote?: string) => Promise<void>;
  onReject: (applicationId: number, reviewNote?: string) => Promise<void>;
  onExport: (applicationId: number) => Promise<void>;
  onRefresh?: () => Promise<void>;
}

type ReviewMode = 'approve' | 'reject';

const statusColorMap: Record<string, string> = {
  submitted: 'blue',
  approved: 'green',
  rejected: 'red',
  fulfilled: 'purple',
};

const ApplicationManagement: React.FC<ApplicationManagementProps> = ({
  applications,
  onApprove,
  onReject,
  onExport,
  onRefresh,
}) => {
  const [reviewModal, setReviewModal] = useState<{
    mode: ReviewMode;
    applicationId: number;
    batchIds?: number[];
  } | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([]);

  const filteredApplications = useMemo(() => {
    if (statusFilter === 'all') {
      return applications;
    }
    return applications.filter((item) => item.status === statusFilter);
  }, [applications, statusFilter]);

  const selectedApplications = useMemo(
    () => filteredApplications.filter((item) => selectedRowKeys.includes(item.id)),
    [filteredApplications, selectedRowKeys],
  );

  const statusCounts = useMemo(
    () =>
      ['all', 'submitted', 'approved', 'rejected', 'fulfilled'].reduce<Record<string, number>>((acc, status) => {
        acc[status] = status === 'all' ? applications.length : applications.filter((item) => item.status === status).length;
        return acc;
      }, {}),
    [applications],
  );

  const openReviewModal = (mode: ReviewMode, applicationId: number, batchIds?: number[]) => {
    setReviewNote('');
    setReviewModal({ mode, applicationId, batchIds });
  };

  const handleReviewSubmit = async () => {
    if (!reviewModal) return;
    const ids = reviewModal.batchIds && reviewModal.batchIds.length > 0 ? reviewModal.batchIds : [reviewModal.applicationId];
    if (reviewModal.mode === 'approve') {
      for (const id of ids) {
        await onApprove(id, reviewNote);
      }
    } else {
      for (const id of ids) {
        await onReject(id, reviewNote);
      }
    }
    message.success(reviewModal.batchIds ? '批量处理完成' : '处理完成');
    setReviewModal(null);
    setReviewNote('');
    setSelectedRowKeys([]);
    await onRefresh?.();
  };

  const handleBatchExport = async () => {
    if (selectedApplications.length === 0) {
      message.warning('请先选择至少一个申请单');
      return;
    }
    for (const item of selectedApplications) {
      if (item.status === 'approved' || item.status === 'fulfilled') {
        await onExport(item.id);
      }
    }
    message.success('批量导出已完成');
    setSelectedRowKeys([]);
    await onRefresh?.();
  };

  const columns: ColumnsType<ApplicationSummary> = [
    {
      title: '申请编号',
      dataIndex: 'application_no',
      key: 'application_no',
    },
    {
      title: '申请人',
      dataIndex: 'requester_name',
      key: 'requester_name',
      render: (_value, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.requester_name}</Text>
          {record.requester_org ? <Text type="secondary">{record.requester_org}</Text> : null}
        </Space>
      ),
    },
    {
      title: '用途',
      dataIndex: 'purpose',
      key: 'purpose',
      render: (value: string) => <Paragraph style={{ marginBottom: 0, maxWidth: 280 }}>{value}</Paragraph>,
    },
    {
      title: '状态',
      dataIndex: 'status_label',
      key: 'status_label',
      render: (_value, record) => <Tag color={statusColorMap[record.status] || 'default'}>{record.status_label}</Tag>,
    },
    {
      title: '审批备注',
      dataIndex: 'review_note',
      key: 'review_note',
      render: (value?: string | null) => (
        <Paragraph style={{ marginBottom: 0, maxWidth: 240 }} type={value ? 'secondary' : 'secondary'}>
          {value || '无'}
        </Paragraph>
      ),
    },
    {
      title: '条目',
      dataIndex: 'item_count',
      key: 'item_count',
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_value, record) => (
        <Space wrap>
          {record.status === 'submitted' ? (
            <>
              <Button size="small" type="primary" icon={<CheckCircleOutlined />} onClick={() => openReviewModal('approve', record.id)}>
                通过
              </Button>
              <Button size="small" danger icon={<CloseCircleOutlined />} onClick={() => openReviewModal('reject', record.id)}>
                拒绝
              </Button>
            </>
          ) : null}
          {(record.status === 'approved' || record.status === 'fulfilled') ? (
            <Button size="small" icon={<DownloadOutlined />} onClick={() => onExport(record.id)}>
              {record.status === 'fulfilled' ? '重新导出' : '导出交付包'}
            </Button>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Tag color="blue">二维影像申请管理</Tag>
          <Title level={4} style={{ margin: 0 }}>
            申请管理
          </Title>
          <Text type="secondary">这里集中处理申请单审批、拒绝和交付导出。申请车页面只保留草稿提交能力。</Text>
        </Space>
      </Card>

      <Card
        title="管理视图"
        extra={
          <Space wrap>
            <Button icon={<ReloadOutlined />} onClick={() => onRefresh?.()}>
              刷新
            </Button>
            <Input
              allowClear
              style={{ width: 220 }}
              placeholder="按状态过滤"
              value={statusFilter === 'all' ? '' : statusFilter}
              onChange={(event) => setStatusFilter(event.target.value || 'all')}
            />
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          {['all', 'submitted', 'approved', 'rejected', 'fulfilled'].map((status) => (
            <Tag
              key={status}
              color={statusFilter === status ? 'processing' : 'default'}
              style={{ cursor: 'pointer' }}
              onClick={() => setStatusFilter(status)}
            >
              {status === 'all' ? `全部 (${statusCounts.all})` : `${status} (${statusCounts[status]})`}
            </Tag>
          ))}
        </Space>

        <Space style={{ marginBottom: 16 }} wrap>
          <Tag color="blue">已选 {selectedApplications.length} 项</Tag>
          <Button
            icon={<CheckCircleOutlined />}
            disabled={selectedApplications.filter((item) => item.status === 'submitted').length === 0}
            onClick={() => {
              const batchIds = selectedApplications.filter((item) => item.status === 'submitted').map((item) => item.id);
              if (batchIds.length === 0) {
                message.warning('请选择待审批的申请单');
                return;
              }
              openReviewModal('approve', batchIds[0], batchIds);
            }}
          >
            批量通过
          </Button>
          <Button
            danger
            icon={<CloseCircleOutlined />}
            disabled={selectedApplications.filter((item) => item.status === 'submitted').length === 0}
            onClick={() => {
              const batchIds = selectedApplications.filter((item) => item.status === 'submitted').map((item) => item.id);
              if (batchIds.length === 0) {
                message.warning('请选择待审批的申请单');
                return;
              }
              openReviewModal('reject', batchIds[0], batchIds);
            }}
          >
            批量拒绝
          </Button>
          <Button
            icon={<DownloadOutlined />}
            disabled={selectedApplications.filter((item) => item.status === 'approved' || item.status === 'fulfilled').length === 0}
            onClick={handleBatchExport}
          >
            批量导出
          </Button>
        </Space>

        {filteredApplications.length === 0 ? (
          <Empty description="当前没有符合条件的申请单。" />
        ) : (
          <Table
            rowKey="id"
            columns={columns}
            dataSource={filteredApplications}
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
            }}
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>

      <Modal
        title={reviewModal?.mode === 'approve' ? '通过申请单' : '拒绝申请单'}
        open={Boolean(reviewModal)}
        onOk={handleReviewSubmit}
        onCancel={() => {
          setReviewModal(null);
          setReviewNote('');
        }}
        okText={reviewModal?.batchIds && reviewModal.batchIds.length > 1 ? '确认批量处理' : reviewModal?.mode === 'approve' ? '确认通过' : '确认拒绝'}
        okButtonProps={{ danger: reviewModal?.mode === 'reject' }}
      >
        <Input.TextArea rows={4} placeholder="填写审批说明，可选。" value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} />
      </Modal>
    </Space>
  );
};

export default ApplicationManagement;
