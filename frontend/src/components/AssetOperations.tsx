import React, { useCallback, useEffect, useState } from 'react';
import { Button, Card, Col, Modal, Row, Space, Statistic, message } from 'antd';
import { ReloadOutlined, SafetyCertificateOutlined, SyncOutlined } from '@ant-design/icons';
import axios from 'axios';

interface Summary {
  total: number;
  processing: number;
  failed: number;
  iiif_not_ready: number;
  fixity_attention: number;
  ready_for_upload: number;
  pending_validation: number;
  duplicate_files: number;
}

interface AssetOperationsProps {
  assetIds: number[];
  canEdit: boolean;
  onRefresh: () => void;
}

const AssetOperations: React.FC<AssetOperationsProps> = ({ assetIds, canEdit, onRefresh }) => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [running, setRunning] = useState(false);
  const load = useCallback(async () => {
    const response = await axios.get<Summary>('/api/assets/operations/summary');
    setSummary(response.data);
  }, []);
  useEffect(() => { void load(); }, [load]);

  const runBatch = (kind: 'verify-fixity' | 'regenerate-derivatives') => {
    Modal.confirm({
      title: kind === 'verify-fixity' ? '校验当前列表中的全部二维资源？' : '重新生成当前列表中的访问副本？',
      content: `本次将处理 ${assetIds.length} 个资源。`,
      onOk: async () => {
        setRunning(true);
        try {
          await axios.post(`/api/assets/operations/${kind}`, { asset_ids: assetIds });
          message.success(kind === 'verify-fixity' ? '批量校验完成' : '衍生任务已加入队列');
          await load();
          onRefresh();
        } catch {
          message.error('批量操作失败');
        } finally {
          setRunning(false);
        }
      },
    });
  };

  if (!summary) return null;
  return (
    <Card title="二维运维概览" size="small" style={{ marginBottom: 16 }} extra={<Button icon={<ReloadOutlined />} onClick={() => void load()}>刷新</Button>}>
      <Row gutter={[12, 12]}>
        <Col xs={12} md={6}><Statistic title="资源总数" value={summary.total} /></Col>
        <Col xs={12} md={6}><Statistic title="处理失败" value={summary.failed} valueStyle={summary.failed ? { color: '#cf1322' } : undefined} /></Col>
        <Col xs={12} md={6}><Statistic title="IIIF 未就绪" value={summary.iiif_not_ready} /></Col>
        <Col xs={12} md={6}><Statistic title="完整性待处理" value={summary.fixity_attention} /></Col>
        <Col xs={12} md={6}><Statistic title="记录待上传" value={summary.ready_for_upload} /></Col>
        <Col xs={12} md={6}><Statistic title="记录待校验" value={summary.pending_validation} /></Col>
        <Col xs={12} md={6}><Statistic title="重复文件" value={summary.duplicate_files} /></Col>
      </Row>
      {canEdit && <Space wrap style={{ marginTop: 16 }}>
        <Button icon={<SafetyCertificateOutlined />} loading={running} onClick={() => runBatch('verify-fixity')}>批量校验完整性</Button>
        <Button icon={<SyncOutlined />} loading={running} onClick={() => runBatch('regenerate-derivatives')}>批量重生成访问副本</Button>
      </Space>}
    </Card>
  );
};

export default AssetOperations;
