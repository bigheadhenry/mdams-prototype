import React from 'react';
import { Card, Col, Row, Space, Statistic, Tag, Typography } from 'antd';
import type { ThreeDObjectGroup } from '../types/assets';

const { Text, Title } = Typography;

const STORAGE_TIER_LABELS: Record<string, string> = {
  working: '工作区',
  delivery: '交付区',
  archive: '归档区',
};

const RECORD_STATUS_LABELS: Record<string, string> = {
  ready: '就绪',
  error: '异常',
  processing: '处理中',
};

interface DashboardOverview {
  objectCount: number;
  representationCount: number;
  webPreviewGroupCount: number;
  totalFileCount: number;
}

interface ThreeDDashboardProps {
  overview: DashboardOverview;
  groupedItems: ThreeDObjectGroup[];
  onOpenDetail?: (id: number) => void;
}

const ThreeDDashboard: React.FC<ThreeDDashboardProps> = ({ overview, groupedItems, onOpenDetail }) => {
  const readyCount = groupedItems.reduce((sum, g) => sum + g.readyCount, 0);
  const errorCount = groupedItems.reduce(
    (sum, g) =>
      sum + g.versions.filter((v) => v.status === 'error' || v.status !== 'ready').length,
    0,
  );

  const storageTierCounts = groupedItems.reduce(
    (acc, g) => {
      const tier = g.storageTier || 'archive';
      acc[tier] = (acc[tier] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card bordered={false}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>
            三维数据管理看板
          </Title>
          <Text type="secondary">
            从管理角度，一个藏品三维数字对象下可以包含原始保存级、Web 展示级、移动轻量级、高精度研究级等模型表现，每个表现再组织自己的模型、点云、贴图和说明文件。
          </Text>
        </Space>
      </Card>

      <Card title="数字对象概览" bordered={false}>
        <Row gutter={16}>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="数字对象" value={overview.objectCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="模型表现总数" value={overview.representationCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="可展示对象" value={overview.webPreviewGroupCount} />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Statistic title="文件总数" value={overview.totalFileCount} />
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col xs={24} lg={8}>
          <Card size="small" title="状态分布" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row justify="space-between">
                <Text>就绪表现</Text>
                <Tag color="green">{readyCount}</Tag>
              </Row>
              <Row justify="space-between">
                <Text>异常 / 非就绪</Text>
                <Tag color="red">{errorCount}</Tag>
              </Row>
              <Row justify="space-between">
                <Text>数字对象总数</Text>
                <Tag color="blue">{overview.objectCount}</Tag>
              </Row>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card size="small" title="保存层分布" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {Object.entries(storageTierCounts).map(([tier, count]) => (
                <Row key={tier} justify="space-between">
                  <Text>{STORAGE_TIER_LABELS[tier] || tier}</Text>
                  <Tag>{count}</Tag>
                </Row>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card size="small" title="Web 展示就绪率" bordered={false}>
            <Statistic
              title="可展示 / 总数"
              value={overview.objectCount > 0
                ? `${((overview.webPreviewGroupCount / overview.objectCount) * 100).toFixed(0)}%`
                : '0%'}
              suffix={
                <Text type="secondary">
                  ({overview.webPreviewGroupCount}/{overview.objectCount})
                </Text>
              }
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card size="small" title="最近对象" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {groupedItems.slice(0, 8).map((group) => (
                <Row key={group.key} align="middle" justify="space-between" style={{ width: '100%' }}>
                  <Space direction="vertical" size={0}>
                    <Text strong style={{ cursor: 'pointer' }} onClick={() => {
                      const preferred = group.webPreviewVersion ?? group.currentVersion ?? group.latestVersion;
                      if (preferred && onOpenDetail) onOpenDetail(preferred.id);
                    }}>
                      {group.label}
                    </Text>
                    <Text type="secondary">
                      {group.versions.length} 个表现 · {group.totalFileCount} 个文件
                    </Text>
                  </Space>
                  <Space wrap>
                    <Tag color={group.webPreviewVersion ? 'green' : 'default'}>
                      {group.webPreviewVersion ? '可展示' : '未展示'}
                    </Tag>
                    <Tag>{RECORD_STATUS_LABELS[group.versions[0]?.status] || group.versions[0]?.status || '-'}</Tag>
                  </Space>
                </Row>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card size="small" title="对象级状态" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {groupedItems.slice(0, 8).map((group) => (
                <Row key={`${group.key}-state`} align="middle" justify="space-between" style={{ width: '100%' }}>
                  <Text>{group.label}</Text>
                  <Space wrap>
                    <Tag color={group.currentVersion ? 'blue' : 'default'}>
                      当前：{group.currentVersion?.version_label || '未设'}
                    </Tag>
                    <Tag color={group.webPreviewVersion ? 'green' : 'default'}>
                      Web：{group.webPreviewVersion?.version_label || '未设'}
                    </Tag>
                  </Space>
                </Row>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default ThreeDDashboard;
