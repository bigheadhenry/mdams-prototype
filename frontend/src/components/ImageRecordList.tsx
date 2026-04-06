import React from 'react';
import { Button, Card, Input, Select, Space, Table, Tag, Typography } from 'antd';
import { EyeOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { ImageRecordSummary } from '../types/assets';

const { Text } = Typography;

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  ready_for_upload: 'processing',
  returned: 'warning',
  uploaded_pending_validation: 'purple',
};

interface ImageRecordListProps {
  records: ImageRecordSummary[];
  loading: boolean;
  searchValue: string;
  statusValue: string;
  canCreate: boolean;
  readyPoolOnly?: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onCreate: () => void;
  onRefresh: () => void;
  onOpen: (record: ImageRecordSummary) => void;
}

const statusOptions = [
  { label: 'All statuses', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Ready for upload', value: 'ready_for_upload' },
  { label: 'Returned', value: 'returned' },
  { label: 'Uploaded pending validation', value: 'uploaded_pending_validation' },
];

const columns: ColumnsType<ImageRecordSummary> = [
  {
    title: 'Record No',
    dataIndex: 'record_no',
    key: 'record_no',
    width: 180,
  },
  {
    title: 'Title',
    dataIndex: 'title',
    key: 'title',
  },
  {
    title: 'Profile',
    dataIndex: 'profile_label',
    key: 'profile_label',
    width: 160,
    render: (value: string | null | undefined, record) => value || record.profile_key,
  },
  {
    title: 'Project',
    dataIndex: 'project_name',
    key: 'project_name',
    width: 160,
    render: (value: string | null | undefined) => value || '-',
  },
  {
    title: 'Object Number',
    dataIndex: 'object_number',
    key: 'object_number',
    width: 160,
    render: (value: string | null | undefined) => value || '-',
  },
  {
    title: 'Status',
    dataIndex: 'status',
    key: 'status',
    width: 180,
    render: (value: string) => <Tag color={STATUS_COLORS[value] || 'default'}>{value}</Tag>,
  },
  {
    title: 'Assigned Photographer',
    dataIndex: 'assigned_photographer_display_name',
    key: 'assigned_photographer_display_name',
    width: 180,
    render: (value: string | null | undefined) => value || '-',
  },
  {
    title: 'Current Asset',
    key: 'asset',
    width: 180,
    render: (_value, record) =>
      record.asset ? <Text>{record.asset.filename || `Asset #${record.asset.asset_id}`}</Text> : <Text type="secondary">No active binding</Text>,
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 140,
    render: (_value, record) => (
      <Button icon={<EyeOutlined />} onClick={() => void record && null}>
        Open
      </Button>
    ),
  },
];

const ImageRecordList: React.FC<ImageRecordListProps> = ({
  records,
  loading,
  searchValue,
  statusValue,
  canCreate,
  readyPoolOnly = false,
  onSearchChange,
  onStatusChange,
  onCreate,
  onRefresh,
  onOpen,
}) => {
  const resolvedColumns = columns.map((column) =>
    column.key === 'actions'
      ? {
          ...column,
          render: (_value: unknown, record: ImageRecordSummary) => (
            <Button icon={<EyeOutlined />} onClick={() => onOpen(record)}>
              Open
            </Button>
          ),
        }
      : column,
  ) as ColumnsType<ImageRecordSummary>;

  return (
    <Card
      title={readyPoolOnly ? 'Assigned upload workbench' : 'Image record workbench'}
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>
            Refresh
          </Button>
          {canCreate ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
              New record
            </Button>
          ) : null}
        </Space>
      }
      data-testid="image-record-list"
    >
      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder={readyPoolOnly ? 'Search record no, object number, or title' : 'Search record no or title'}
          allowClear
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          onSearch={onSearchChange}
          style={{ width: 320 }}
        />
        {!readyPoolOnly ? (
          <Select value={statusValue} options={statusOptions} onChange={onStatusChange} style={{ width: 220 }} />
        ) : null}
      </Space>

      <Table
        rowKey="id"
        loading={loading}
        dataSource={records}
        columns={resolvedColumns}
        pagination={{ pageSize: 8 }}
      />
    </Card>
  );
};

export default ImageRecordList;
