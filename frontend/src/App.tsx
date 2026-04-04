import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Badge,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Image,
  Layout,
  Menu,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EyeOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  LoadingOutlined,
  LoginOutlined,
  LogoutOutlined,
  ReloadOutlined,
  ShoppingCartOutlined,
  UserOutlined,
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
import {
  can,
  getRoleLabels,
  getVisibleMenuKeys,
  type AuthContext,
  type AuthLoginResponse,
  type AuthUserSummary,
  type MenuKey,
} from './auth/permissions';
import type { ApplicationCartItem, ApplicationSummary, AssetSummary } from './types/assets';

const { Header, Content, Footer, Sider } = Layout;
const { Paragraph, Text, Title } = Typography;

const AUTH_TOKEN_KEY = 'mdams.auth.token';

const buildPreviewUrl = (record: AssetSummary) => {
  const version = encodeURIComponent(`${record.created_at}-${record.file_size}`);
  return `/api/assets/${record.id}/preview?v=${version}`;
};

const MENU_LABELS: Record<MenuKey, string> = {
  '1': '总览',
  '2': '二维资源',
  '3': '申请车',
  '4': '入库与处理',
  '5': '统一资源目录',
  '6': '统一资源详情',
  '7': '三维管理',
  '8': '申请管理',
};

const App: React.FC = () => {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [currentManifest, setCurrentManifest] = useState('');
  const [selectedKey, setSelectedKey] = useState<MenuKey>('1');
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
  const [selectedUnifiedResourceId, setSelectedUnifiedResourceId] = useState<string | null>(null);
  const [applicationCart, setApplicationCart] = useState<ApplicationCartItem[]>([]);
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [applicationsSubmitting, setApplicationsSubmitting] = useState(false);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [availableUsers, setAvailableUsers] = useState<AuthUserSummary[]>([]);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginSubmitting, setLoginSubmitting] = useState(false);

  const visibleMenuKeys = useMemo(
    () => (authContext ? getVisibleMenuKeys(authContext) : []),
    [authContext],
  );
  const currentRoleLabels = useMemo(
    () => (authContext ? getRoleLabels(authContext) : []),
    [authContext],
  );

  const canViewImages = authContext ? can(authContext, 'image.view') : false;
  const canUploadImages = authContext
    ? can(authContext, 'image.upload') || can(authContext, 'image.ingest_review') || can(authContext, 'image.edit')
    : false;
  const canDeleteImages = authContext ? can(authContext, 'image.delete') : false;
  const canCreateApplications = authContext ? can(authContext, 'application.create') : false;
  const canManageApplications = authContext
    ? can(authContext, 'application.review') || can(authContext, 'application.export') || can(authContext, 'application.view_all')
    : false;
  const canView3D = authContext ? can(authContext, 'three_d.view') : false;
  const canViewPlatform = authContext ? can(authContext, 'platform.view') : false;

  const applyToken = useCallback((token: string | null) => {
    if (token) {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
      window.localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      delete axios.defaults.headers.common.Authorization;
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  }, []);

  const fetchAuthUsers = useCallback(async () => {
    try {
      const response = await axios.get<AuthUserSummary[]>('/api/auth/users');
      setAvailableUsers(response.data);
    } catch (error) {
      console.error(error);
      setAvailableUsers([]);
    }
  }, []);

  const fetchAuthContext = useCallback(async () => {
    const response = await axios.get<AuthContext>('/api/auth/context');
    setAuthContext(response.data);
    return response.data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.warn('logout failed', error);
    } finally {
      applyToken(null);
      setAuthContext(null);
      setApplications([]);
      setAssets([]);
    }
  }, [applyToken]);

  useEffect(() => {
    const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
      applyToken(token);
    }

    const initialize = async () => {
      setAuthLoading(true);
      await fetchAuthUsers();
      if (token) {
        try {
          await fetchAuthContext();
        } catch (error) {
          console.warn('stored auth token invalid', error);
          applyToken(null);
          setAuthContext(null);
        }
      }
      setAuthLoading(false);
    };

    void initialize();
  }, [applyToken, fetchAuthContext, fetchAuthUsers]);

  useEffect(() => {
    if (!visibleMenuKeys.includes(selectedKey) && visibleMenuKeys.length > 0) {
      setSelectedKey(visibleMenuKeys[0]);
    }
  }, [selectedKey, visibleMenuKeys]);

  const fetchAssets = useCallback(
    async (silent = false) => {
      if (!authContext || !canViewImages) {
        setAssets([]);
        return;
      }
      if (!silent) setLoading(true);
      try {
        const res = await axios.get<AssetSummary[]>('/api/assets');
        setAssets(res.data);
      } catch (err) {
        console.warn('Failed to load assets', err);
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [authContext, canViewImages],
  );

  const fetchApplications = useCallback(async () => {
    if (!authContext || (!canCreateApplications && !canManageApplications)) {
      setApplications([]);
      return;
    }
    try {
      const res = await axios.get<ApplicationSummary[]>('/api/applications');
      setApplications(res.data);
    } catch (err) {
      console.warn('Failed to load applications', err);
      setApplications([]);
    }
  }, [authContext, canCreateApplications, canManageApplications]);

  useEffect(() => {
    if (!authContext) return;
    void fetchAssets();
    void fetchApplications();
  }, [authContext, fetchAssets, fetchApplications]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    const hasProcessing = assets.some((asset) => asset.status === 'processing');
    if (hasProcessing) {
      interval = setInterval(() => {
        void fetchAssets(true);
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [assets, fetchAssets]);

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/assets/${id}`);
      message.success('资源已删除');
      void fetchAssets();
    } catch (err) {
      console.error(err);
      message.error('删除失败');
    }
  };

  const addToApplicationCart = useCallback(
    (item: ApplicationCartItem) => {
      if (!canCreateApplications) {
        message.warning('当前用户没有提交申请的权限');
        return false;
      }
      let added = false;
      setApplicationCart((current) => {
        if (current.some((entry) => entry.assetId === item.assetId)) {
          return current;
        }
        added = true;
        return [...current, item];
      });
      if (added) {
        message.success('已加入申请车');
      }
      return added;
    },
    [canCreateApplications],
  );

  const updateApplicationNote = useCallback((assetId: number, note: string) => {
    setApplicationCart((current) => current.map((item) => (item.assetId === assetId ? { ...item, note } : item)));
  }, []);

  const removeFromApplicationCart = useCallback((assetId: number) => {
    setApplicationCart((current) => current.filter((item) => item.assetId !== assetId));
    message.success('已从申请车移除');
  }, []);

  const submitApplication = useCallback(
    async (payload: {
      requesterName: string;
      requesterOrg?: string;
      contactEmail?: string;
      purpose: string;
      usageScope?: string;
    }) => {
      if (!canCreateApplications) {
        message.warning('当前用户没有提交申请的权限');
        return;
      }
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
        void fetchApplications();
      } catch (err) {
        console.error(err);
        message.error('申请提交失败');
      } finally {
        setApplicationsSubmitting(false);
      }
    },
    [applicationCart, canCreateApplications, fetchApplications],
  );

  const approveApplication = useCallback(
    async (applicationId: number, reviewNote?: string) => {
      try {
        await axios.post(`/api/applications/${applicationId}/approve`, {
          review_note: reviewNote || null,
        });
        message.success('申请单已通过');
        await fetchApplications();
      } catch (err) {
        console.error(err);
        message.error('审批失败');
      }
    },
    [fetchApplications],
  );

  const rejectApplication = useCallback(
    async (applicationId: number, reviewNote?: string) => {
      try {
        await axios.post(`/api/applications/${applicationId}/reject`, {
          review_note: reviewNote || null,
        });
        message.success('申请单已拒绝');
        await fetchApplications();
      } catch (err) {
        console.error(err);
        message.error('拒绝失败');
      }
    },
    [fetchApplications],
  );

  const exportApplication = useCallback(
    async (applicationId: number) => {
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
        await fetchApplications();
      } catch (err) {
        console.error(err);
        message.error('交付包导出失败');
      }
    },
    [fetchApplications],
  );

  const handleLogin = async (payload: { username: string; password: string }) => {
    setLoginSubmitting(true);
    try {
      const response = await axios.post<AuthLoginResponse>('/api/auth/login', payload);
      applyToken(response.data.token);
      setAuthContext(response.data.user);
      message.success(`已登录：${response.data.user.display_name}`);
    } catch (error) {
      console.error(error);
      message.error('登录失败，请检查用户名和密码');
    } finally {
      setLoginSubmitting(false);
    }
  };

  const columns = [
    {
      title: '缩略图',
      key: 'thumbnail',
      width: 96,
      render: (_value: unknown, record: AssetSummary) => (
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: 10,
            overflow: 'hidden',
            border: '1px solid #e5e7eb',
            background: 'linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Image
            src={buildPreviewUrl(record)}
            alt={record.filename}
            preview={false}
            loading="lazy"
            fallback="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='72' height='72' viewBox='0 0 72 72'><rect width='72' height='72' fill='%23eef2f7'/><text x='36' y='40' text-anchor='middle' font-size='12' fill='%2394a3b8'>No Preview</text></svg>"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>
      ),
    },
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '文件名', dataIndex: 'filename', key: 'filename' },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (val: number) => `${(val / 1024 / 1024).toFixed(2)} MB`,
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
            data-testid={`asset-preview-button-${record.id}`}
            icon={<EyeOutlined />}
            disabled={record.status === 'processing'}
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
          {canDeleteImages ? (
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
          ) : null}
        </div>
      ),
    },
  ];

  const menuItems = useMemo(
    () =>
      ([
        { key: '1', icon: <DashboardOutlined />, label: <span data-testid="menu-1">{MENU_LABELS['1']}</span> },
        { key: '2', icon: <DatabaseOutlined />, label: <span data-testid="menu-2">{MENU_LABELS['2']}</span> },
        {
          key: '3',
          icon: <ShoppingCartOutlined />,
          label: (
            <Badge count={applicationCart.length} size="small">
              <span data-testid="menu-3">{MENU_LABELS['3']}</span>
            </Badge>
          ),
        },
        { key: '4', icon: <ExperimentOutlined />, label: <span data-testid="menu-4">{MENU_LABELS['4']}</span> },
        { key: '5', icon: <DatabaseOutlined />, label: <span data-testid="menu-5">{MENU_LABELS['5']}</span> },
        { key: '6', icon: <FileTextOutlined />, label: <span data-testid="menu-6">{MENU_LABELS['6']}</span> },
        { key: '7', icon: <DatabaseOutlined />, label: <span data-testid="menu-7">{MENU_LABELS['7']}</span> },
        { key: '8', icon: <FileTextOutlined />, label: <span data-testid="menu-8">{MENU_LABELS['8']}</span> },
      ] as Array<{ key: MenuKey; icon: React.ReactNode; label: React.ReactNode }>).filter((item) =>
        visibleMenuKeys.includes(item.key),
      ),
    [applicationCart.length, visibleMenuKeys],
  );

  const renderDashboard = () => (
    <>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="二维资源数" value={assets.length} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="申请草稿数" value={applicationCart.length} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="申请单数" value={applications.length} />
          </Card>
        </Col>
      </Row>

      <Card title="当前登录上下文" extra={<Button icon={<ReloadOutlined />} onClick={() => void fetchAssets()}>刷新资源</Button>}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Text strong>{authContext?.display_name}</Text>
          <Space wrap>
            {currentRoleLabels.map((label) => (
              <Tag key={label} color="blue">
                {label}
              </Tag>
            ))}
          </Space>
          <Paragraph style={{ marginBottom: 0 }}>
            当前可见菜单：{visibleMenuKeys.map((key) => MENU_LABELS[key]).join(' / ')}
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            认证模式：{authContext?.auth_mode}，责任范围：{authContext?.collection_scope.length ? authContext.collection_scope.join(', ') : '无'}
          </Paragraph>
        </Space>
      </Card>

      {canViewImages ? (
        <div data-testid="assets-table" style={{ marginTop: 24 }}>
          <Table dataSource={assets} columns={columns} rowKey="id" loading={loading} />
        </div>
      ) : null}
    </>
  );

  if (authLoading) {
    return (
      <Layout style={{ minHeight: '100vh', placeItems: 'center' }}>
        <Content style={{ display: 'grid', placeItems: 'center' }}>
          <Card>
            <Space direction="vertical" align="center">
              <LoadingOutlined />
              <Text>正在初始化登录上下文…</Text>
            </Space>
          </Card>
        </Content>
      </Layout>
    );
  }

  if (!authContext) {
    return (
      <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f5f1e8 0%, #dbe7e4 100%)' }}>
        <Content style={{ display: 'grid', placeItems: 'center', padding: 24 }}>
          <Card style={{ width: 520, maxWidth: '100%' }}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Space direction="vertical" size={4}>
                <Title level={3} style={{ margin: 0 }}>
                  MDAMS 登录
                </Title>
                <Text type="secondary">
                  当前已接入真实用户、角色关系和登录上下文。默认测试密码为 `mdams123`。
                </Text>
              </Space>

              <Form layout="vertical" onFinish={(values) => void handleLogin(values)}>
                <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请选择或填写用户名' }]}>
                  <Select
                    showSearch
                    placeholder="选择测试用户"
                    suffixIcon={<UserOutlined />}
                    options={availableUsers.map((user) => ({
                      label: `${user.display_name} (${user.username})`,
                      value: user.username,
                    }))}
                  />
                </Form.Item>
                <Form.Item name="password" label="密码" initialValue="mdams123" rules={[{ required: true, message: '请输入密码' }]}>
                  <Input.Password placeholder="输入密码" />
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<LoginOutlined />} loading={loginSubmitting} block>
                  登录进入系统
                </Button>
              </Form>

              <Divider style={{ margin: 0 }} />

              <Card size="small" title="可用测试账号" bordered={false}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {availableUsers.map((user) => (
                    <Space key={user.username} align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space direction="vertical" size={0}>
                        <Text strong>{user.display_name}</Text>
                        <Text type="secondary">{user.username}</Text>
                      </Space>
                      <Space wrap>
                        {user.roles.map((role) => (
                          <Tag key={`${user.username}-${role.key}`}>{role.label}</Tag>
                        ))}
                      </Space>
                    </Space>
                  ))}
                </Space>
              </Card>
            </Space>
          </Card>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ padding: 16, color: '#fff' }}>
          <Space direction="vertical" size={4} style={{ width: '100%' }}>
            <Text style={{ color: '#fff', fontWeight: 700 }}>MDAMS Prototype</Text>
            <Text style={{ color: 'rgba(255,255,255,0.75)' }}>真实用户与角色上下文</Text>
          </Space>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={(e) => {
            setSelectedKey(e.key as MenuKey);
            if (e.key !== '2') {
              setSelectedAssetId(null);
            }
            if (e.key !== '6') {
              setSelectedUnifiedResourceId(null);
            }
          }}
          items={menuItems}
        />
      </Sider>

      <Layout>
        <Header style={{ padding: '0 24px', background: '#fff' }}>
          <Row align="middle" justify="space-between" style={{ height: '100%' }}>
            <Col>
              <Space>
                <UserOutlined />
                <Text strong>{authContext.display_name}</Text>
                <Tag color="processing">{currentRoleLabels.join(' / ')}</Tag>
              </Space>
            </Col>
            <Col>
              <Space>
                <Text type="secondary">默认测试密码：mdams123</Text>
                <Button icon={<LogoutOutlined />} onClick={() => void logout()}>
                  退出登录
                </Button>
              </Space>
            </Col>
          </Row>
        </Header>

        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
            {selectedAssetId !== null ? (
              <AssetDetail
                assetId={selectedAssetId}
                onBack={() => {
                  setSelectedAssetId(null);
                  setSelectedKey('1');
                  void fetchAssets(true);
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
                  <Tag color="blue">统一资源详情</Tag>
                  <Paragraph>请先从统一资源目录中选择一个资源。</Paragraph>
                  <Button type="primary" onClick={() => setSelectedKey('5')}>
                    返回统一资源目录
                  </Button>
                </Card>
              )
            ) : (
              <>
                {selectedKey === '1' && renderDashboard()}

                {selectedKey === '4' && canUploadImages ? (
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
                ) : null}

                {selectedKey === '5' && canViewPlatform ? (
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
                ) : null}

                {selectedKey === '7' && canView3D ? <ThreeDManagement /> : null}

                {selectedKey === '8' && canManageApplications ? (
                  <ApplicationManagement
                    applications={applications}
                    onApprove={approveApplication}
                    onReject={rejectApplication}
                    onExport={exportApplication}
                    onRefresh={fetchApplications}
                  />
                ) : null}

                {selectedKey === '3' && canCreateApplications ? (
                  <ApplicationCart
                    items={applicationCart}
                    onRemove={removeFromApplicationCart}
                    onUpdateNote={updateApplicationNote}
                    onSubmit={submitApplication}
                    submitting={applicationsSubmitting}
                  />
                ) : null}

                {selectedKey === '2' && canViewImages ? (
                  <div data-testid="assets-table">
                    <Table dataSource={assets} columns={columns} rowKey="id" loading={loading} />
                  </div>
                ) : null}
              </>
            )}
          </div>
        </Content>

        <Footer style={{ textAlign: 'center' }}>
          MDAMS Prototype · Auth context
          <Divider type="vertical" />
          {authContext.display_name}
        </Footer>

        {previewVisible ? (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 5000,
              background: 'rgba(10, 12, 18, 0.92)',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                color: '#fff',
                borderBottom: '1px solid rgba(255,255,255,0.12)',
                flex: '0 0 auto',
              }}
            >
              <div>
                <Text strong style={{ color: '#fff' }}>Mirador Viewer</Text>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.72)' }}>
                  {currentManifest}
                </div>
              </div>
              <Button onClick={() => setPreviewVisible(false)}>关闭预览</Button>
            </div>
            <div style={{ flex: 1, minHeight: 0 }}>
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
            </div>
          </div>
        ) : null}
      </Layout>
    </Layout>
  );
};

export default App;
