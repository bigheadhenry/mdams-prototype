import React, { useState } from 'react';
import { Button, Col, Collapse, Input, Row, Segmented, Select, Space, Typography } from 'antd';
import { ClearOutlined, FilterOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import type { AdvancedSearchParams } from '../types/assets';

const { Search } = Input;
const { Text } = Typography;

const PROFILE_OPTIONS = [
  { value: 'other', label: '其他' },
  { value: 'movable_artifact', label: '文物影像' },
  { value: 'immovable_artifact', label: '文物建筑影像' },
  { value: 'art_photography', label: '艺术摄影影像' },
  { value: 'business_activity', label: '业务活动影像' },
  { value: 'panorama', label: '全景影像' },
  { value: 'ancient_tree', label: '古树影像' },
  { value: 'archaeology', label: '考古影像' },
  { value: 'model', label: '三维模型' },
  { value: 'point_cloud', label: '点云' },
  { value: 'oblique_photo', label: '倾斜摄影' },
  { value: 'package', label: '三维包' },
  { value: 'mission_documentary', label: '航天任务纪实' },
  { value: 'science_education', label: '科普教育' },
  { value: 'human_spaceflight', label: '载人航天' },
];

export type ViewMode = 'card' | 'table';

interface AdvancedSearchPanelProps {
  viewMode: ViewMode;
  sourceSystem: string;
  onViewModeChange: (mode: ViewMode) => void;
  onSearch: (params: AdvancedSearchParams) => void;
  onRefresh: () => void;
  loading?: boolean;
}

const AdvancedSearchPanel: React.FC<AdvancedSearchPanelProps> = ({
  viewMode,
  sourceSystem,
  onViewModeChange,
  onSearch,
  onRefresh,
  loading = false,
}) => {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<string | undefined>();
  const [previewState, setPreviewState] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [profileKey, setProfileKey] = useState<string | undefined>();

  const resourceTypeOptions = sourceSystem === ''
    ? [
        { value: 'image_2d_cultural_object', label: '二维影像' },
        { value: 'three_d_digital_object', label: '三维数字对象' },
        { value: 'video_cultural_object', label: '文博视频' },
      ]
    : sourceSystem === 'three_d'
    ? [{ value: 'three_d_digital_object', label: '三维数字对象' }]
    : sourceSystem === 'video'
      ? [{ value: 'video_cultural_object', label: '文博视频' }]
      : [{ value: 'image_2d_cultural_object', label: '二维影像' }];

  const profileOptions = PROFILE_OPTIONS.filter((option) => {
    if (sourceSystem === '') return true;
    if (sourceSystem === 'three_d') return ['model', 'point_cloud', 'oblique_photo', 'package'].includes(option.value);
    if (sourceSystem === 'video') return ['mission_documentary', 'science_education', 'human_spaceflight', 'other'].includes(option.value);
    return !['model', 'point_cloud', 'oblique_photo', 'package', 'mission_documentary', 'science_education', 'human_spaceflight'].includes(option.value);
  });

  const handleSearch = () => {
    const params: AdvancedSearchParams = {};
    if (query.trim()) params.q = query.trim();
    if (status) params.status = status;
    if (previewState) params.preview_enabled = previewState;
    if (resourceType) params.resource_type = resourceType;
    if (profileKey) params.profile_key = profileKey;
    onSearch(params);
  };

  const handleClear = () => {
    setQuery('');
    setStatus(undefined);
    setPreviewState(undefined);
    setResourceType(undefined);
    setProfileKey(undefined);
    onSearch({});
  };

  const hasFilters =
    query || status || previewState || resourceType || profileKey;

  return (
    <Collapse
      size="small"
      items={[
        {
          key: 'advanced-search',
          label: (
            <Space>
              <FilterOutlined />
              <span>高级检索</span>
              {hasFilters && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  (已激活)
                </Text>
              )}
            </Space>
          ),
          children: (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Row gutter={[12, 8]} align="middle">
                <Col xs={24} sm={12} md={9}>
                  <Search
                    data-testid="platform-search"
                    allowClear
                    placeholder="搜索标题、文件名、MIME 或资源标识"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onSearch={handleSearch}
                    enterButton={<SearchOutlined />}
                  />
                </Col>
                <Col xs={12} sm={6} md={4}>
                  <Select
                    allowClear
                    placeholder="状态"
                    value={status}
                    onChange={setStatus}
                    style={{ width: '100%' }}
                    options={[
                      { value: 'ready', label: '就绪' },
                      { value: 'processing', label: '处理中' },
                      { value: 'error', label: '异常' },
                    ]}
                  />
                </Col>
                <Col xs={12} sm={6} md={4}>
                  <Select
                    allowClear
                    placeholder="预览"
                    value={previewState}
                    onChange={setPreviewState}
                    style={{ width: '100%' }}
                    options={[
                      { value: 'true', label: '可预览' },
                      { value: 'false', label: '仅下载' },
                    ]}
                  />
                </Col>
                <Col xs={12} sm={6} md={5}>
                  <Select
                    allowClear
                    placeholder="资源类型"
                    value={resourceType}
                    onChange={setResourceType}
                    style={{ width: '100%' }}
                    options={resourceTypeOptions}
                  />
                </Col>
                <Col xs={12} sm={6} md={4}>
                  <Select
                    allowClear
                    placeholder="模板"
                    value={profileKey}
                    onChange={setProfileKey}
                    style={{ width: '100%' }}
                    options={profileOptions}
                  />
                </Col>
                <Col style={{ marginLeft: 'auto' }}>
                  <Space>
                    <Button
                      icon={<ClearOutlined />}
                      onClick={handleClear}
                      disabled={!hasFilters && !loading}
                    >
                      清除
                    </Button>
                    <Button
                      type="primary"
                      icon={<SearchOutlined />}
                      onClick={handleSearch}
                      loading={loading}
                    >
                      检索
                    </Button>
                    <Button icon={<ReloadOutlined />} onClick={onRefresh} />
                    <Segmented
                      size="small"
                      value={viewMode}
                      onChange={(value) => onViewModeChange(value as ViewMode)}
                      options={[
                        { value: 'card', label: '卡片' },
                        { value: 'table', label: '表格' },
                      ]}
                    />
                  </Space>
                </Col>
              </Row>
            </Space>
          ),
        },
      ]}
    />
  );
};

export default AdvancedSearchPanel;
