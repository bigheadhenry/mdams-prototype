import React, { useMemo } from 'react';
import { Button, Card, Divider, Progress, Space, Tag, Tooltip, Typography } from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  DoubleLeftOutlined,
  DoubleRightOutlined,
  EyeOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { UnifiedResourceSourceSummary } from '../types/assets';

const { Text } = Typography;

interface PlatformStatsBarProps {
  sources: UnifiedResourceSourceSummary[];
  totalResources: number;
  activeSourceSystem: string;
  previewResourceCount: number;
  onSwitchSource?: (sourceSystem: string) => void;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
}

const SOURCE_COLORS: Record<string, string> = {
  image_2d: '#1677ff',
  three_d: '#52c41a',
  video: '#fa8c16',
};

const SOURCE_LABELS: Record<string, string> = {
  image_2d: '二维',
  three_d: '三维',
  video: '视频',
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  image_2d: <PictureOutlined />,
  three_d: <ThunderboltOutlined />,
  video: <PlayCircleOutlined />,
};

const formatRelativeTime = (iso?: string | null): string => {
  if (!iso) return '未同步';
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diff = Date.now() - t;
  if (diff < 0) return new Date(iso).toLocaleString();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} 天前`;
  return new Date(iso).toLocaleDateString();
};

const PlatformStatsBar: React.FC<PlatformStatsBarProps> = ({
  sources,
  totalResources,
  activeSourceSystem,
  previewResourceCount,
  onSwitchSource,
  collapsed = false,
  onToggleCollapsed,
}) => {
  const activeSource = sources.find((source) => source.source_system === activeSourceSystem);
  const stats = useMemo(() => {
    const totalSources = sources.length;
    const healthySources = sources.filter((s) => s.healthy).length;
    const healthyRate = totalSources > 0 ? Math.round((healthySources / totalSources) * 100) : 0;
    const previewRate = totalResources > 0
      ? Math.round((previewResourceCount / totalResources) * 100)
      : 0;
    return { totalSources, healthySources, healthyRate, previewRate };
  }, [sources, totalResources, previewResourceCount]);

  const activeLabel = activeSource
    ? SOURCE_LABELS[activeSource.source_system] || activeSource.source_label
    : '当前资源';

  // 折叠态：竖排迷你条
  if (collapsed) {
    return (
      <Card
        size="small"
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: 8 }}
      >
        <Space direction="vertical" align="center" size={10} style={{ width: '100%' }}>
          <Tooltip title="展开检索概览" placement="right">
            <Button
              type="text"
              size="small"
              icon={<DoubleRightOutlined />}
              onClick={onToggleCollapsed}
            />
          </Tooltip>
          <Tooltip title={`${activeLabel} 资源数`} placement="right">
            <Text strong style={{ fontSize: 18, color: '#1677ff', lineHeight: 1 }}>
              {totalResources}
            </Text>
          </Tooltip>
          <Divider style={{ margin: '4px 0' }} />
          {sources.map((source) => {
            const isActive = source.source_system === activeSourceSystem;
            return (
              <Tooltip
                key={source.source_system}
                title={`${SOURCE_LABELS[source.source_system] || source.source_label}：${source.resource_count}`}
                placement="right"
              >
                <Tag
                  color={isActive ? SOURCE_COLORS[source.source_system] || 'blue' : undefined}
                  style={{
                    margin: 0,
                    cursor: onSwitchSource ? 'pointer' : 'default',
                    fontSize: 11,
                    padding: '2px 6px',
                  }}
                  onClick={() => onSwitchSource?.(source.source_system)}
                >
                  {SOURCE_ICONS[source.source_system]}
                  <span style={{ marginLeft: 2 }}>{source.resource_count}</span>
                </Tag>
              </Tooltip>
            );
          })}
          <Divider style={{ margin: '4px 0' }} />
          <Tooltip title={`可预览：${previewResourceCount}（${stats.previewRate}%）`} placement="right">
            <Tag icon={<EyeOutlined />} color="green" style={{ margin: 0, fontSize: 11 }}>
              {previewResourceCount}
            </Tag>
          </Tooltip>
          <Tooltip
            title={`来源健康度：${stats.healthyRate}%（${stats.healthySources}/${stats.totalSources}）`}
            placement="right"
          >
            <Tag
              icon={<CheckCircleOutlined />}
              color={stats.healthyRate === 100 ? 'success' : stats.healthyRate < 60 ? 'error' : 'orange'}
              style={{ margin: 0, fontSize: 11 }}
            >
              {stats.healthyRate}%
            </Tag>
          </Tooltip>
        </Space>
      </Card>
    );
  }

  return (
    <Card
      size="small"
      title="检索概览"
      style={{ marginBottom: 16 }}
      bodyStyle={{ padding: 16 }}
      extra={
        onToggleCollapsed ? (
          <Tooltip title="折叠为边栏">
            <Button
              type="text"
              size="small"
              icon={<DoubleLeftOutlined />}
              onClick={onToggleCollapsed}
            />
          </Tooltip>
        ) : null
      }
    >
      {/* Group 1: 当前 Tab 概览 */}
      <Space direction="vertical" size={6} style={{ width: '100%' }}>
        <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {activeLabel} 资源数
          </Text>
          <Tooltip title={`最近同步：${formatRelativeTime(activeSource?.last_synced_at)}`}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              <ClockCircleOutlined style={{ marginRight: 4 }} />
              {formatRelativeTime(activeSource?.last_synced_at)}
            </Text>
          </Tooltip>
        </Space>
        <Space align="baseline" size={8}>
          <Text strong style={{ fontSize: 26, color: '#1677ff', lineHeight: 1 }}>
            {totalResources}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            可预览 {previewResourceCount} ({stats.previewRate}%)
          </Text>
        </Space>
        <Progress
          percent={stats.previewRate}
          size="small"
          showInfo={false}
          strokeColor="#52c41a"
        />
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* Group 2: 全平台维度分布（可点击切换 Tab） */}
      <Space direction="vertical" size={6} style={{ width: '100%' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          全平台维度分布
        </Text>
        <Space wrap size={[6, 6]}>
          {sources.map((source) => {
            const isActive = source.source_system === activeSourceSystem;
            return (
              <Tag
                key={source.source_system}
                color={isActive ? SOURCE_COLORS[source.source_system] || 'blue' : undefined}
                style={{
                  margin: 0,
                  cursor: onSwitchSource ? 'pointer' : 'default',
                  borderStyle: isActive ? 'solid' : 'dashed',
                  fontWeight: isActive ? 600 : 400,
                }}
                onClick={() => onSwitchSource?.(source.source_system)}
              >
                <span style={{ marginRight: 4 }}>{SOURCE_ICONS[source.source_system]}</span>
                {SOURCE_LABELS[source.source_system] || source.source_label}
                <span style={{ marginLeft: 4, opacity: 0.85 }}>{source.resource_count}</span>
              </Tag>
            );
          })}
        </Space>
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* Group 3: 来源健康度（100% 折叠为徽标） */}
      <Space direction="vertical" size={6} style={{ width: '100%' }}>
        <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            <Tooltip title="健康 = 来源系统过去 24h 同步成功，未上报错误">
              <span style={{ borderBottom: '1px dashed #bfbfbf', cursor: 'help' }}>
                来源健康度
              </span>
            </Tooltip>
          </Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {stats.healthySources}/{stats.totalSources}
          </Text>
        </Space>
        {stats.healthyRate === 100 ? (
          <Tag icon={<CheckCircleOutlined />} color="success" style={{ margin: 0 }}>
            全部健康
          </Tag>
        ) : (
          <Progress
            percent={stats.healthyRate}
            size="small"
            status={stats.healthyRate < 60 ? 'exception' : 'normal'}
            format={() => `${stats.healthyRate}%`}
          />
        )}
        <Text type="secondary" style={{ fontSize: 11 }}>
          <EyeOutlined style={{ marginRight: 4 }} />
          当前 Tab 可预览 {previewResourceCount} 条
        </Text>
      </Space>
    </Card>
  );
};

export default PlatformStatsBar;
