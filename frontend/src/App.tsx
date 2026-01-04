import React, { useState, useEffect } from 'react';
import { Layout, Menu, Upload, Button, Table, message, Card, Statistic, Row, Col, Tag, Modal } from 'antd';
import { UploadOutlined, DatabaseOutlined, DashboardOutlined, ShoppingCartOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';
import MiradorViewer from './MiradorViewer';

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

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/assets');
      setAssets(res.data);
    } catch (err) {
      message.error('Failed to load assets');
    } finally {
      setLoading(false);
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
      message.success(`${file.name} uploaded successfully`);
      onSuccess("Ok");
      fetchAssets();
    } catch (err) {
      message.error(`${file.name} upload failed.`);
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
      message.error('You can only upload supported image files (JPG, PNG, GIF, BMP, TIFF)!');
      return Upload.LIST_IGNORE;
    }
    
    const isLt100M = file.size / 1024 / 1024 < 100;
    if (!isLt100M) {
      message.error('Image must be smaller than 100MB!');
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Filename', dataIndex: 'filename', key: 'filename' },
    { 
      title: 'Size', 
      dataIndex: 'file_size', 
      key: 'file_size',
      render: (val: number) => (val / 1024 / 1024).toFixed(2) + ' MB'
    },
    { title: 'Type', dataIndex: 'mime_type', key: 'mime_type' },
    { 
      title: 'Status', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ready' ? 'green' : 'blue'}>{status.toUpperCase()}</Tag>
      )
    },
    { title: 'Uploaded At', dataIndex: 'created_at', key: 'created_at' },
    {
      title: 'Action',
      key: 'action',
      render: (_, record: Asset) => (
        <Button 
          icon={<EyeOutlined />} 
          onClick={() => {
            // Use relative path via Nginx proxy to avoid hardcoding IP
            // 使用经由 Nginx 代理的相对路径，避免硬编码 IP
            setCurrentManifest(`/api/iiif/${record.id}/manifest`);
            setPreviewVisible(true);
          }}
        >
          View in Mirador
        </Button>
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
          defaultSelectedKeys={['1']}
          items={[
            { key: '1', icon: <DashboardOutlined />, label: 'Dashboard' },
            { key: '2', icon: <DatabaseOutlined />, label: 'Assets' },
            { key: '3', icon: <ShoppingCartOutlined />, label: 'Orders' },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff' }} />
        <Content style={{ margin: '24px 16px 0' }}>
          <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card>
                  <Statistic title="Total Assets" value={assets.length} />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic title="Storage Used" value="1.2 GB" precision={2} />
                </Card>
              </Col>
            </Row>

            <div style={{ marginBottom: 16 }}>
              <Upload 
                customRequest={handleUpload} 
                showUploadList={false}
                accept=".jpg,.jpeg,.png,.gif,.bmp,.tif,.tiff"
                beforeUpload={beforeUpload}
              >
                <Button icon={<UploadOutlined />}>Upload New Asset</Button>
              </Upload>
            </div>

            <Table 
              dataSource={assets} 
              columns={columns} 
              rowKey="id" 
              loading={loading}
            />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>MEAM Prototype ©2026 Created for SunJing Lab</Footer>

        <Modal
          title="Mirador Viewer"
          open={previewVisible}
          onCancel={() => setPreviewVisible(false)}
          width={1000}
          footer={null}
          destroyOnClose
        >
           {previewVisible && <MiradorViewer manifestId={currentManifest} />}
        </Modal>
      </Layout>
    </Layout>
  );
};

export default App;
