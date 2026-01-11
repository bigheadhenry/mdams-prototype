import React, { useState, useEffect } from 'react';
import { Layout, Menu, Upload, Button, Table, message, Card, Statistic, Row, Col, Tag, Modal } from 'antd';
import { UploadOutlined, DatabaseOutlined, DashboardOutlined, ShoppingCartOutlined, EyeOutlined, ExperimentOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import MiradorViewer from './MiradorViewer';
import IngestDemo from './components/IngestDemo';

const { Header, Content, Footer, Sider } = Layout;

interface Asset {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  created_at: string;
}

const App: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [currentManifest, setCurrentManifest] = useState('');
  const [selectedKey, setSelectedKey] = useState('1');

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/assets');
      setAssets(res.data);
    } catch (err) {
      // Quiet fail if backend is down for UI demo
      console.warn('加载资产失败', err);
    } finally {
      setLoading(false);
    }
  };

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

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post('/api/upload', formData);
      message.success(`${file.name} 上传成功`);
      onSuccess("Ok");
      fetchAssets();
    } catch (err) {
      message.error(`${file.name} 上传失败`);
      onError({ err });
    }
  };

  const beforeUpload = (file: any) => {
    // Allow common image formats supported by Cantaloupe/Java 2D
    // JPG, PNG, GIF, BMP, TIFF
    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff'];
    const fileName = file.name.toLowerCase();
    const isImage = file.type.startsWith('image/') && 
                    allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isImage) {
      message.error('您只能上传支持的图像文件 (JPG, PNG, GIF, BMP, TIFF)!');
      return Upload.LIST_IGNORE;
    }
    
    const isLt100M = file.size / 1024 / 1024 < 1000;
    if (!isLt100M) {
      message.error('图像大小必须小于 1000MB!');
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '文件名', dataIndex: 'filename', key: 'filename' },
    { 
      title: '大小', 
      dataIndex: 'file_size', 
      key: 'file_size',
      render: (val: number) => (val / 1024 / 1024).toFixed(2) + ' MB'
    },
    { title: '类型', dataIndex: 'mime_type', key: 'mime_type' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ready' ? 'green' : 'blue'}>{status.toUpperCase()}</Tag>
      )
    },
    { title: '上传时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Asset) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button 
            icon={<EyeOutlined />} 
            onClick={() => {
              // Use relative path via Nginx proxy to avoid hardcoding IP
              // 使用经由 Nginx 代理的相对路径，避免硬编码 IP
              setCurrentManifest(`/api/iiif/${record.id}/manifest`);
              setPreviewVisible(true);
            }}
          >
            查看
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
          onClick={(e) => setSelectedKey(e.key)}
          items={[
            { key: '1', icon: <DashboardOutlined />, label: '仪表盘' },
            { key: '2', icon: <DatabaseOutlined />, label: '数字资产' },
            { key: '3', icon: <ShoppingCartOutlined />, label: '订单管理' },
            { key: '4', icon: <ExperimentOutlined />, label: '入库 PoC' },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff' }} />
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
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
                </Row>

                <Table 
                  dataSource={assets} 
                  columns={columns} 
                  rowKey="id" 
                  loading={loading}
                />
              </>
            )}
            
            {selectedKey === '4' && (
              <IngestDemo 
                onViewManifest={(assetId) => {
                  setCurrentManifest(`/api/iiif/${assetId}/manifest`);
                  setPreviewVisible(true);
                }}
              />
            )}
            
            {(selectedKey === '2' || selectedKey === '3') && (
               <div style={{ textAlign: 'center', padding: 50 }}>
                 <Tag color="orange">建设中</Tag>
                 <p>该模块尚未实现。</p>
               </div>
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
