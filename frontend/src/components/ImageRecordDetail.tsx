import React, { useRef } from 'react';
import { Alert, Button, Card, Descriptions, Divider, List, Space, Tag, Typography } from 'antd';
import type { ImageRecordDetailResponse } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

const STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  ready_for_upload: 'processing',
  returned: 'warning',
  uploaded_pending_validation: 'purple',
};

interface ImageRecordDetailProps {
  record: ImageRecordDetailResponse;
  canEdit: boolean;
  canSubmit: boolean;
  canReturn: boolean;
  canUpload: boolean;
  canMatch: boolean;
  actionLoading: boolean;
  uploading: boolean;
  onBack: () => void;
  onEdit: () => void;
  onSubmit: () => void;
  onReturn: () => void;
  onUploadTempFile: (file: File) => void;
  onConfirmBind: () => void;
  onConfirmReplace: () => void;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return '-';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

const ImageRecordDetail: React.FC<ImageRecordDetailProps> = ({
  record,
  canEdit,
  canSubmit,
  canReturn,
  canUpload,
  canMatch,
  actionLoading,
  uploading,
  onBack,
  onEdit,
  onSubmit,
  onReturn,
  onUploadTempFile,
  onConfirmBind,
  onConfirmReplace,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const management = (record.metadata_info.management as Record<string, unknown> | undefined) || {};
  const profile = record.metadata_info.profile;
  const profileFields = (profile?.fields as Record<string, unknown> | undefined) || {};
  const pendingUpload = record.pending_upload || null;

  return (
    <Card
      data-testid="image-record-detail"
      title={
        <Space direction="vertical" size={2}>
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              {record.title}
            </Title>
            <Tag color={STATUS_COLORS[record.status] || 'default'}>{record.status}</Tag>
          </Space>
          <Text type="secondary">{record.record_no}</Text>
        </Space>
      }
      extra={
        <Space>
          <Button onClick={onBack}>Back</Button>
          {canEdit ? <Button onClick={onEdit}>Edit</Button> : null}
          {canSubmit && (record.status === 'draft' || record.status === 'returned') ? (
            <Button type="primary" loading={actionLoading} onClick={onSubmit}>
              Submit to ready-for-upload
            </Button>
          ) : null}
          {canReturn && record.status === 'ready_for_upload' ? (
            <Button loading={actionLoading} onClick={onReturn}>
              Return for revision
            </Button>
          ) : null}
        </Space>
      }
    >
      {!record.validation.ready_for_submit ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="Required fields are still missing before submit."
          description={`Missing fields: ${record.validation.missing_labels.join(', ')}`}
        />
      ) : null}

      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Record No">{record.record_no}</Descriptions.Item>
        <Descriptions.Item label="Profile">{record.profile_label || record.profile_key}</Descriptions.Item>
        <Descriptions.Item label="Visibility">{record.visibility_scope}</Descriptions.Item>
        <Descriptions.Item label="Collection Object ID">{record.collection_object_id ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Project">{record.project_name || '-'}</Descriptions.Item>
        <Descriptions.Item label="Image Category">{record.image_category || '-'}</Descriptions.Item>
        <Descriptions.Item label="Created By">{record.created_by_display_name || '-'}</Descriptions.Item>
        <Descriptions.Item label="Assigned Photographer">{record.assigned_photographer_display_name || '-'}</Descriptions.Item>
        <Descriptions.Item label="Submitted By">{record.submitted_by_display_name || '-'}</Descriptions.Item>
        <Descriptions.Item label="Submitted At">{record.submitted_at || '-'}</Descriptions.Item>
        <Descriptions.Item label="Current Asset" span={2}>
          {record.asset ? `${record.asset.filename || `Asset #${record.asset.asset_id}`} (${record.asset.status || 'unknown'})` : 'No active binding'}
        </Descriptions.Item>
      </Descriptions>

      {(canUpload || canMatch)
      && (record.status === 'ready_for_upload' || record.status === 'uploaded_pending_validation' || pendingUpload) ? (
        <>
          <Divider />
          <Title level={5}>Upload and Matching</Title>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
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
                      onUploadTempFile(nextFile);
                    }
                    event.target.value = '';
                  }}
                />
                <Space>
                  <Button loading={uploading} onClick={() => fileInputRef.current?.click()}>
                    Upload candidate file
                  </Button>
                  <Text type="secondary">Binding only becomes effective after explicit confirmation.</Text>
                </Space>
              </>
            ) : null}

            {pendingUpload ? (
              <Card size="small" title="Pending Upload Analysis">
                <Descriptions bordered size="small" column={2}>
                  <Descriptions.Item label="Filename">{pendingUpload.filename}</Descriptions.Item>
                  <Descriptions.Item label="SHA256">{pendingUpload.sha256}</Descriptions.Item>
                  <Descriptions.Item label="Size">{pendingUpload.file_size} bytes</Descriptions.Item>
                  <Descriptions.Item label="Format">{pendingUpload.format_name || pendingUpload.mime_type || '-'}</Descriptions.Item>
                  <Descriptions.Item label="Dimensions">
                    {pendingUpload.width && pendingUpload.height ? `${pendingUpload.width} x ${pendingUpload.height}` : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Filename Matches">
                    {pendingUpload.filename_matches.length ? pendingUpload.filename_matches.join(', ') : 'None'}
                  </Descriptions.Item>
                </Descriptions>

                {pendingUpload.warnings.length ? (
                  <Alert
                    type="warning"
                    showIcon
                    style={{ marginTop: 16 }}
                    message="Review these risk hints before confirming."
                    description={
                      <List
                        size="small"
                        dataSource={pendingUpload.warnings}
                        renderItem={(item) => <List.Item>{item}</List.Item>}
                      />
                    }
                  />
                ) : null}

                {pendingUpload.duplicate_assets.length ? (
                  <Alert
                    type="info"
                    showIcon
                    style={{ marginTop: 16 }}
                    message="Duplicate file hash detected."
                    description={
                      <List
                        size="small"
                        dataSource={pendingUpload.duplicate_assets}
                        renderItem={(item) => (
                          <List.Item>
                            Asset #{item.asset_id} {item.filename ? `(${item.filename})` : ''} {item.image_record_id ? `linked to record ${item.image_record_id}` : ''}
                          </List.Item>
                        )}
                      />
                    }
                  />
                ) : null}

                {canMatch ? (
                  <Space style={{ marginTop: 16 }}>
                    {pendingUpload.can_confirm_bind ? (
                      <Button type="primary" loading={actionLoading} onClick={onConfirmBind}>
                        Confirm bind
                      </Button>
                    ) : null}
                    {pendingUpload.can_confirm_replace ? (
                      <Button type="primary" danger loading={actionLoading} onClick={onConfirmReplace}>
                        Confirm replace
                      </Button>
                    ) : null}
                  </Space>
                ) : null}
              </Card>
            ) : (
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                No temporary upload is waiting for confirmation.
              </Paragraph>
            )}
          </Space>
        </>
      ) : null}

      <Divider />

      <Title level={5}>Management Metadata</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        {Object.keys(management).length === 0 ? (
          <Paragraph type="secondary">No management metadata yet.</Paragraph>
        ) : (
          Object.entries(management).map(([key, value]) => (
            <Paragraph key={key} style={{ marginBottom: 8 }}>
              <Text strong>{key}</Text>: {renderValue(value)}
            </Paragraph>
          ))
        )}
      </Space>

      <Divider />

      <Title level={5}>Profile Metadata</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        {Object.keys(profileFields).length === 0 ? (
          <Paragraph type="secondary">No profile-specific fields yet.</Paragraph>
        ) : (
          Object.entries(profileFields).map(([key, value]) => (
            <Paragraph key={key} style={{ marginBottom: 8 }}>
              <Text strong>{key}</Text>: {renderValue(value)}
            </Paragraph>
          ))
        )}
      </Space>
    </Card>
  );
};

export default ImageRecordDetail;
