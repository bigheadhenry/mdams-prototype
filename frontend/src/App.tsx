import React, { useCallback, useEffect, useState } from 'react';
import { Layout, Menu, Button, Table, message, Card, Statistic, Row, Col, Tag, Modal } from 'antd';
import {
  DatabaseOutlined,
  DashboardOutlined,
  ShoppingCartOutlined,
  EyeOutlined,
  ExperimentOutlined,
  DeleteOutlined,
  DownloadOutlined,
  ReloadOutlined,
  LoadingOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import MiradorViewer from './MiradorViewer';
import IngestDemo from './components/IngestDemo';
import AssetDetail from './components/AssetDetail';
import PlatformDirectory from './components/PlatformDirectory';
import UnifiedResourceDetail from './components/UnifiedResourceDetail';
import ThreeDManagement from './components/ThreeDManagement';
import type { AssetSummary } from './types/assets';

const { Header, Content, Footer, Sider } = Layout;

const App: React.FC = () => {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [currentManifest, setCurrentManifest] = useState('');
  const [selectedKey, setSelectedKey] = useState('1');
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [selectedUnifiedResourceId, setSelectedUnifiedResourceId] = useState<string | null>(null);

  const fetchAssets = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await axios.get('/api/assets');
      setAssets(res.data);
    } catch (err) {
      console.warn('加载资产失败', err);
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    const hasProcessing = assets.some((asset) => asset.status === 'processing');
    if (hasProcessing) {
      interval = setInterval(() => {
        fetchAssets(true);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [assets, fetchAssets]);

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/assets/${id}`);
      message.success('资产删除成功');
      fetchAssets();
    } catch (err) {
      message.error('删除失败');
      console.error(err);
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '文件名', dataIndex: 'filename', key: 'filename' },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (val: number) => (val / 1024 / 1024).toFixed(2) + ' MB',
    },
    { title: '类型', dataIndex: 'mime_type', key: 'mime_type' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag icon={status === 'processing' ? <LoadingOutlined /> : undefined} color={status === 'ready' ? 'green' : 'blue'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    { title: '上传时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_value: unknown, record: AssetSummary) => (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Button
            icon={<FileTextOutlined />}
            onClick={() => {
              setSelectedAssetId(record.id);
              setSelectedUnifiedResourceId(null);
              setSelectedKey('2');
            }}
          >
            详情
          </Button>
          <Button
            icon={<EyeOutlined />}
            disabled={record.status === 'processing'}
            title={record.status === 'processing' ? '正在转码中，请稍候…' : '查看图像预览'}
            onClick={() => {
              setCurrentManifest(`/api/iiif/${record.id}/manifest`);
              setPreviewVisible(true);
            }}
          >
            预览
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = `/api/assets/${record.id}/download-bag`;
            }}
          >
            下载
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: `确定要删除文件 ${record.filename} 吗？此操作不可恢复。`,
                okText: '删除',
                okType: 'danger',
                cancelText: '取消',
                onOk: () => handleDelete(record.id),
              });
            }}
          >
            删除
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={(e) => {
            setSelectedKey(e.key);
            if (e.key !== '2') {
              setSelectedAssetId(null);
            }
            if (e.key !== '6') {
              setSelectedUnifiedResourceId(null);
            }
          }}
          items={[
            { key: '1', icon: <DashboardOutlined />, label: '仪表盘' },
            { key: '2', icon: <DatabaseOutlined />, label: '数字资产' },
            { key: '3', icon: <ShoppingCartOutlined />, label: '订单管理' },
            { key: '4', icon: <ExperimentOutlined />, label: '入库 PoC' },
            { key: '5', icon: <DatabaseOutlined />, label: '统一资源' },
            { key: '6', icon: <FileTextOutlined />, label: '统一详情' },
            { key: '7', icon: <DatabaseOutlined />, label: '3D Data' },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff' }} />
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
            {selectedAssetId !== null ? (
              <AssetDetail
                assetId={selectedAssetId}
                onBack={() => {
                  setSelectedAssetId(null);
                  setSelectedKey('1');
                  fetchAssets(true);
                }}
                onPreview={(manifestUrl) => {
                  setCurrentManifest(manifestUrl);
                  setPreviewVisible(true);
                }}
              />
            ) : selectedKey === '6' ? (
              selectedUnifiedResourceId ? (
                <UnifiedResourceDetail
                  resourceId={selectedUnifiedResourceId}
                  onBack={() => {
                    setSelectedUnifiedResourceId(null);
                    setSelectedKey('5');
                  }}
                  onPreview={(manifestUrl) => {
                    setCurrentManifest(manifestUrl);
                    setPreviewVisible(true);
                  }}
                  onOpenSourceDetail={(assetId) => {
                    setSelectedAssetId(assetId);
                    setSelectedUnifiedResourceId(null);
                    setSelectedKey('2');
                  }}
                  onOpenUnifiedResourceDetail={(resourceId) => {
                    setSelectedUnifiedResourceId(resourceId);
                    setSelectedAssetId(null);
                    setSelectedKey('6');
                  }}
                />
              ) : (
                <Card>
                  <Tag color="blue">统一详情</Tag>
                  <p>请先从统一资源目录中选择一个资源。</p>
                  <Button type="primary" onClick={() => setSelectedKey('5')}>
                    返回统一资源目录
                  </Button>
                </Card>
              )
            ) : (
              <>
                {selectedKey === '1' && (
                  <>
                    <Row gutter={16} style={{ marginBottom: 24 }}>
                      <Col span={8}>
                        <Card>
                          <Statistic title="资产总数" value={assets.length} />
                        </Card>
                      </Col>
                      <Col span={8}>
                        <Card>
                          <Statistic title="已用存储" value="1.2 GB" precision={2} />
                        </Card>
                      </Col>
                      <Col span={8} style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                        <Button icon={<ReloadOutlined />} onClick={() => fetchAssets()}>
                          刷新列表
                        </Button>
                      </Col>
                    </Row>

                    <Table dataSource={assets} columns={columns} rowKey="id" loading={loading} />
                  </>
                )}

                {selectedKey === '4' && (
                  <IngestDemo
                    onViewManifest={(assetId) => {
                      setCurrentManifest(`/api/iiif/${assetId}/manifest`);
                      setPreviewVisible(true);
                    }}
                    onOpenAssetDetail={(assetId) => {
                      setSelectedAssetId(assetId);
                      setSelectedUnifiedResourceId(null);
                      setSelectedKey('2');
                    }}
                  />
                )}

                {selectedKey === '5' && (
                  <PlatformDirectory
                    onPreview={(manifestUrl) => {
                      setCurrentManifest(manifestUrl);
                      setPreviewVisible(true);
                    }}
                    onOpenAssetDetail={(assetId) => {
                      setSelectedAssetId(assetId);
                      setSelectedUnifiedResourceId(null);
                      setSelectedKey('2');
                    }}
                    onOpenUnifiedResourceDetail={(resourceId) => {
                      setSelectedUnifiedResourceId(resourceId);
                      setSelectedAssetId(null);
                      setSelectedKey('6');
                    }}
                  />
                )}

                {selectedKey === '7' && <ThreeDManagement />}

                {(selectedKey === '2' || selectedKey === '3') && (
                  <div style={{ textAlign: 'center', padding: 50 }}>
                    <Tag color="orange">建设中</Tag>
                    <p>该模块尚未实现。</p>
                  </div>
                )}
              </>
            )}
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>MEAM 原型系统 ©2026 为孙靖实验室创建</Footer>

        <Modal
          title="Mirador Viewer"
          open={previewVisible}
          onCancel={() => setPreviewVisible(false)}
          width={1000}
          footer={null}
          destroyOnHidden={true}
        >
          {previewVisible && <MiradorViewer manifestId={currentManifest} />}
        </Modal>
      </Layout>
    </Layout>
  );
};

export default App;
