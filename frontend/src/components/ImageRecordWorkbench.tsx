import React, { useCallback, useEffect, useState } from 'react';
import { Modal, message } from 'antd';
import axios from 'axios';
import type { AuthContext, AuthUserSummary } from '../auth/permissions';
import type { ImageRecordDetailResponse, ImageRecordSavePayload, ImageRecordSummary } from '../types/assets';
import ImageRecordDetail from './ImageRecordDetail';
import ImageRecordForm from './ImageRecordForm';
import ImageRecordList from './ImageRecordList';

type ViewMode = 'list' | 'detail' | 'form';

interface ImageRecordWorkbenchProps {
  authContext: AuthContext;
  availableUsers: AuthUserSummary[];
}

const ImageRecordWorkbench: React.FC<ImageRecordWorkbenchProps> = ({ authContext, availableUsers }) => {
  const [records, setRecords] = useState<ImageRecordSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [mode, setMode] = useState<ViewMode>('list');
  const [searchValue, setSearchValue] = useState('');
  const [statusValue, setStatusValue] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<ImageRecordDetailResponse | null>(null);

  const canCreate = authContext.permissions.includes('image.record.create');
  const canEdit = authContext.permissions.includes('image.record.edit');
  const canSubmit = authContext.permissions.includes('image.record.submit');
  const canReturn = authContext.permissions.includes('image.record.return');
  const canUpload = authContext.permissions.includes('image.file.upload');
  const canMatch = authContext.permissions.includes('image.file.match');
  const readyPoolOnly =
    !authContext.permissions.includes('image.record.list')
    && authContext.permissions.includes('image.record.view_ready_for_upload');

  const loadRecords = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get<ImageRecordSummary[]>('/api/image-records', {
        params: {
          q: searchValue || undefined,
          status: readyPoolOnly ? undefined : statusValue || undefined,
        },
      });
      setRecords(response.data);
    } catch (error) {
      console.error(error);
      message.error('Failed to load image records.');
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [readyPoolOnly, searchValue, statusValue]);

  const openDetail = async (record: ImageRecordSummary) => {
    setActionLoading(true);
    try {
      const response = await axios.get<ImageRecordDetailResponse>(`/api/image-records/${record.id}`);
      setSelectedRecord(response.data);
      setMode('detail');
    } catch (error) {
      console.error(error);
      message.error('Failed to load the selected image record.');
    } finally {
      setActionLoading(false);
    }
  };

  const saveRecord = async (payload: ImageRecordSavePayload) => {
    setSaving(true);
    try {
      if (selectedRecord) {
        const response = await axios.patch<ImageRecordDetailResponse>(`/api/image-records/${selectedRecord.id}`, payload);
        setSelectedRecord(response.data);
      } else {
        const response = await axios.post<ImageRecordDetailResponse>('/api/image-records', payload);
        setSelectedRecord(response.data);
      }
      setMode('detail');
      await loadRecords();
      message.success('Image record draft saved.');
    } catch (error) {
      console.error(error);
      message.error('Failed to save the image record.');
    } finally {
      setSaving(false);
    }
  };

  const submitRecord = async () => {
    if (!selectedRecord) return;
    setActionLoading(true);
    try {
      const response = await axios.post<ImageRecordDetailResponse>(`/api/image-records/${selectedRecord.id}/submit`);
      setSelectedRecord(response.data);
      await loadRecords();
      message.success('Record moved to ready-for-upload.');
    } catch (error) {
      console.error(error);
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      if (detail?.missing_labels) {
        message.error(`Missing required fields: ${detail.missing_labels.join(', ')}`);
      } else {
        message.error('Failed to submit the image record.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const returnRecord = () => {
    if (!selectedRecord) return;
    let note = '';
    Modal.confirm({
      title: 'Return image record',
      content: (
        <textarea
          rows={4}
          style={{ width: '100%', marginTop: 12, resize: 'vertical' }}
          placeholder="Optional return note"
          onChange={(event) => {
            note = event.target.value;
          }}
        />
      ),
      okText: 'Return',
      cancelText: 'Cancel',
      onOk: async () => {
        setActionLoading(true);
        try {
          const response = await axios.post<ImageRecordDetailResponse>(`/api/image-records/${selectedRecord.id}/return`, {
            note: note || null,
          });
          setSelectedRecord(response.data);
          await loadRecords();
          message.success('Image record returned.');
        } catch (error) {
          console.error(error);
          message.error('Failed to return the image record.');
        } finally {
          setActionLoading(false);
        }
      },
    });
  };

  const uploadTempFile = async (file: File) => {
    if (!selectedRecord) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    try {
      const response = await axios.post<ImageRecordDetailResponse>(
        `/api/image-records/${selectedRecord.id}/upload-temp`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        },
      );
      setSelectedRecord(response.data);
      message.success('Temporary upload analysis is ready.');
    } catch (error) {
      console.error(error);
      message.error('Failed to upload the candidate file.');
    } finally {
      setUploading(false);
    }
  };

  const confirmMatch = async (modeValue: 'bind' | 'replace') => {
    if (!selectedRecord?.pending_upload) return;
    setActionLoading(true);
    try {
      const response = await axios.post<ImageRecordDetailResponse>(
        `/api/image-records/${selectedRecord.id}/${modeValue === 'bind' ? 'confirm-bind' : 'confirm-replace'}`,
        {
          temp_upload_token: selectedRecord.pending_upload.token,
        },
      );
      setSelectedRecord(response.data);
      await loadRecords();
      message.success(modeValue === 'bind' ? 'Asset binding confirmed.' : 'Asset replacement confirmed.');
    } catch (error) {
      console.error(error);
      message.error(modeValue === 'bind' ? 'Failed to confirm the binding.' : 'Failed to confirm the replacement.');
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    void loadRecords();
  }, [loadRecords]);

  if (mode === 'form') {
    return (
      <ImageRecordForm
        record={selectedRecord}
        availableUsers={availableUsers}
        saving={saving}
        onCancel={() => setMode(selectedRecord ? 'detail' : 'list')}
        onSave={saveRecord}
      />
    );
  }

  if (mode === 'detail' && selectedRecord) {
    return (
      <ImageRecordDetail
        record={selectedRecord}
        canEdit={canEdit}
        canSubmit={canSubmit}
        canReturn={canReturn}
        canUpload={canUpload}
        canMatch={canMatch}
        actionLoading={actionLoading}
        uploading={uploading}
        onBack={() => setMode('list')}
        onEdit={() => setMode('form')}
        onSubmit={() => void submitRecord()}
        onReturn={returnRecord}
        onUploadTempFile={(file) => void uploadTempFile(file)}
        onConfirmBind={() => void confirmMatch('bind')}
        onConfirmReplace={() => void confirmMatch('replace')}
      />
    );
  }

  return (
    <ImageRecordList
      records={records}
      loading={loading}
      searchValue={searchValue}
      statusValue={readyPoolOnly ? 'ready_for_upload' : statusValue}
      canCreate={canCreate}
      readyPoolOnly={readyPoolOnly}
      onSearchChange={setSearchValue}
      onStatusChange={setStatusValue}
      onCreate={() => {
        setSelectedRecord(null);
        setMode('form');
      }}
      onRefresh={() => void loadRecords()}
      onOpen={(record) => void openDetail(record)}
    />
  );
};

export default ImageRecordWorkbench;
