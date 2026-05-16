import React, { useMemo } from 'react';
import { Card, Col, Progress, Row, Space, Statistic, Tag, Typography } from 'antd';
import {
  CheckCircleOutlined,
  DatabaseOutlined,
  EyeOutlined,
  FileImageOutlined,
} from '@ant-design/icons';
import type { UnifiedResourceSourceSummary } from '../types/assets';

const { Text } = Typography;

interface PlatformStatsBarProps {
  sources: UnifiedResourceSourceSummary[];
  totalResources: number;
  activeSourceSystem: string;
  previewResourceCount: number;
}

const SOURCE_COLORS: Record<string, string> = {
  image_2d: '#1677ff',
  three_d: '#52c41a',
  video: '#fa8c16',
};

const SOURCE_LABELS: Record<string, string> = {
  image_2d: '二维影像',
  three_d: '三维资产',
  video: '视频资产',
};

const PlatformStatsBar: React.FC<PlatformStatsBarProps> = ({
  sources,
  totalResources,
  activeSourceSystem,
  previewResourceCount,
}) => {
  const activeSource = sources.find((source) => source.source_system === activeSourceSystem);
  const stats = useMemo(() => {
    const totalSources = sources.length;
    const healthySources = sources.filter((s) => s.healthy).length;
    const healthyRate = totalSources > 0 ? Math.round((healthySources / totalSources) * 100) : 0;

    return { totalSources, healthySources, healthyRate };
  }, [sources]);

  return (
    <Card size="small" title="检索概览" style={{ marginBottom: 16 }}>
      <Row gutter={[16, 12]}>
        <Col span={12}>
          <Statistic
            title={activeSource ? SOURCE_LABELS[activeSource.source_system] || activeSource.source_label : '当前资源'}
            value={totalResources}
            prefix={<DatabaseOutlined />}
            valueStyle={{ color: '#1677ff', fontSize: 24 }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="来源系统"
            value={stats.totalSources}
            suffix={`/ ${stats.healthySources} 健康`}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ fontSize: 24 }}
          />
        </Col>
        <Col span={24}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              来源健康度
            </Text>
            <Progress
              percent={stats.healthyRate}
              size="small"
              status={stats.healthyRate === 100 ? 'success' : 'normal'}
              format={() => `${stats.healthyRate}%`}
            />
          </Space>
        </Col>
        <Col span={24}>
          <Space wrap size={[4, 4]}>
            <Text type="secondary" style={{ fontSize: 12, marginRight: 4 }}>
              全平台分布：
            </Text>
            {sources.map((source) => (
              <Tag
                key={source.source_system}
                color={SOURCE_COLORS[source.source_system] || 'default'}
                style={{ margin: 0 }}
              >
                <FileImageOutlined style={{ marginRight: 4 }} />
                {SOURCE_LABELS[source.source_system] || source.source_label}: {source.resource_count}
              </Tag>
            ))}
          </Space>
        </Col>
        <Col span={24}>
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              当前可预览：
            </Text>
            <Tag icon={<EyeOutlined />} color="green">
              {previewResourceCount} 资源
            </Tag>
          </Space>
        </Col>
      </Row>
    </Card>
  );
};

export default PlatformStatsBar;
