import React, { useCallback, useEffect, useState } from 'react';
import { Badge, Layout, Menu, Button, Table, message, Card, Statistic, Row, Col, Tag, Modal } from 'antd';
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
import ApplicationCart from './components/ApplicationCart';
import ApplicationManagement from './components/ApplicationManagement';
import type { ApplicationCartItem, ApplicationSummary, AssetSummary } from './types/assets';

const { Header, Content, Footer, Sider } = Layout;

const App: React.FC = () => {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [currentManifest, setCurrentManifest] = useState('');
  const [selectedKey, setSelectedKey] = useState('1');
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [selectedUnifiedResourceId, setSelectedUnifiedResourceId] = useState<string | null>(null);
  const [applicationCart, setApplicationCart] = useState<ApplicationCartItem[]>([]);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [applicationsSubmitting, setApplicationsSubmitting] = useState(false);

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

  const fetchApplications = useCallback(async () => {
    try {
      const res = await axios.get<ApplicationSummary[]>('/api/applications');
      setApplications(res.data);
    } catch (err) {
      console.warn('加载申请单失败', err);
    }
  }, []);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

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

  const addToApplicationCart = useCallback((item: ApplicationCartItem) => {
    let added = false;
    setApplicationCart((current) => {
      if (current.some((entry) => entry.assetId === item.assetId)) {
        return current;
      }
      added = true;
      return [...current, item];
    });
    return added;
  }, []);

  const updateApplicationNote = useCallback((assetId: number, note: string) => {
    setApplicationCart((current) =>
      current.map((item) => (item.assetId === assetId ? { ...item, note } : item)),
    );
  }, []);

  const removeFromApplicationCart = useCallback((assetId: number) => {
    setApplicationCart((current) => current.filter((item) => item.assetId !== assetId));
    message.success('已从申请车移除');
  }, []);

  const submitApplication = useCallback(async (payload: {
    requesterName: string;
    requesterOrg?: string;
    contactEmail?: string;
    purpose: string;
    usageScope?: string;
  }) => {
    setApplicationsSubmitting(true);
    try {
      await axios.post('/api/applications', {
        requester_name: payload.requesterName,
        requester_org: payload.requesterOrg,
        contact_email: payload.contactEmail,
        purpose: payload.purpose,
        usage_scope: payload.usageScope,
        items: applicationCart.map((item) => ({
          asset_id: item.assetId,
          requested_variant: 'current',
          delivery_format: 'image',
          note: item.note || null,
        })),
      });
      message.success('申请单已提交');
      setApplicationCart([]);
      fetchApplications();
    } catch (err) {
      console.error(err);
      message.error('申请单提交失败');
    } finally {
      setApplicationsSubmitting(false);
    }
  }, [applicationCart, fetchApplications]);

  const approveApplication = useCallback(async (applicationId: number, reviewNote?: string) => {
    try {
      await axios.post(`/api/applications/${applicationId}/approve`, {
        review_note: reviewNote || null,
      });
      message.success('申请单已通过');
      fetchApplications();
    } catch (err) {
      console.error(err);
      message.error('申请单通过失败');
    }
  }, [fetchApplications]);

  const rejectApplication = useCallback(async (applicationId: number, reviewNote?: string) => {
    try {
      await axios.post(`/api/applications/${applicationId}/reject`, {
        review_note: reviewNote || null,
      });
      message.success('申请单已拒绝');
      fetchApplications();
    } catch (err) {
      console.error(err);
      message.error('申请单拒绝失败');
    }
  }, [fetchApplications]);

  const exportApplication = useCallback(async (applicationId: number) => {
    try {
      const response = await axios.get(`/api/applications/${applicationId}/export`, {
        responseType: 'blob',
      });
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `application-${applicationId}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('交付包已生成');
      fetchApplications();
    } catch (err) {
      console.error(err);
      message.error('交付包导出失败');
    }
  }, [fetchApplications]);

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
            {
              key: '3',
              icon: <ShoppingCartOutlined />,
              label: <Badge count={applicationCart.length} size="small">申请车</Badge>,
            },
            { key: '4', icon: <ExperimentOutlined />, label: '入库 PoC' },
            { key: '5', icon: <DatabaseOutlined />, label: '统一资源' },
            { key: '6', icon: <FileTextOutlined />, label: '统一详情' },
            { key: '7', icon: <DatabaseOutlined />, label: '3D Data' },
            { key: '8', icon: <FileTextOutlined />, label: '申请管理' },
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

                {selectedKey === '8' && (
                  <ApplicationManagement
                    applications={applications}
                    onApprove={approveApplication}
                    onReject={rejectApplication}
                    onExport={exportApplication}
                    onRefresh={fetchApplications}
                  />
                )}

                {selectedKey === '3' && (
                  <ApplicationCart
                    items={applicationCart}
                    onRemove={removeFromApplicationCart}
                    onUpdateNote={updateApplicationNote}
                    onSubmit={submitApplication}
                    submitting={applicationsSubmitting}
                  />
                )}

                {selectedKey === '2' && (
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
          {previewVisible && (
            <MiradorViewer
              manifestId={currentManifest}
              onAddToApplication={(item) =>
                addToApplicationCart({
                  assetId: item.assetId,
                  resourceId: item.resourceId,
                  title: item.title,
                  manifestUrl: item.manifestUrl,
                  objectNumber: item.objectNumber,
                  sourceLabel: item.sourceLabel,
                })
              }
            />
          )}
        </Modal>
      </Layout>
    </Layout>
  );
};

export default App;
