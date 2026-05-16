import React, { useState } from 'react';
import { Button, Col, Collapse, DatePicker, Input, Row, Segmented, Select, Space, Typography } from 'antd';
import { ClearOutlined, FilterOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import type { AdvancedSearchParams } from '../types/assets';

const { Search } = Input;
const { RangePicker } = DatePicker;
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
];

const FIELD_OPTIONS = [
  { value: 'title', label: '标题' },
  { value: 'filename', label: '文件名' },
  { value: 'mime', label: 'MIME 类型' },
];

export type ViewMode = 'card' | 'table';

interface AdvancedSearchPanelProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onSearch: (params: AdvancedSearchParams) => void;
  onRefresh: () => void;
  loading?: boolean;
}

const AdvancedSearchPanel: React.FC<AdvancedSearchPanelProps> = ({
  viewMode,
  onViewModeChange,
  onSearch,
  onRefresh,
  loading = false,
}) => {
  const [query, setQuery] = useState('');
  const [field, setField] = useState<string | undefined>();
  const [fieldValue, setFieldValue] = useState('');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [status, setStatus] = useState<string | undefined>();
  const [previewState, setPreviewState] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [profileKey, setProfileKey] = useState<string | undefined>();

  const handleSearch = () => {
    const params: AdvancedSearchParams = {};
    if (query.trim()) params.q = query.trim();
    if (field && fieldValue.trim()) {
      params.field = field as AdvancedSearchParams['field'];
      params.field_value = fieldValue.trim();
    }
    if (dateRange) {
      params.date_from = dateRange[0];
      params.date_to = dateRange[1];
    }
    if (status) params.status = status;
    if (previewState) params.preview_enabled = previewState;
    if (resourceType) params.resource_type = resourceType;
    if (profileKey) params.profile_key = profileKey;
    onSearch(params);
  };

  const handleClear = () => {
    setQuery('');
    setField(undefined);
    setFieldValue('');
    setDateRange(null);
    setStatus(undefined);
    setPreviewState(undefined);
    setResourceType(undefined);
    setProfileKey(undefined);
    onSearch({});
  };

  const hasFilters =
    query || field || fieldValue || dateRange || status || previewState || resourceType || profileKey;

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
              {/* Row 1: Keyword search + quick filters */}
              <Row gutter={[12, 8]} align="middle">
                <Col xs={24} sm={12} md={8}>
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
                <Col xs={12} sm={6} md={3}>
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
                    options={[
                      { value: 'image_2d_cultural_object', label: '二维影像' },
                      { value: 'three_d_model', label: '三维模型' },
                      { value: 'three_d_point_cloud', label: '点云' },
                      { value: 'three_d_oblique_photo', label: '倾斜摄影' },
                      { value: 'three_d_package', label: '三维包' },
                    ]}
                  />
                </Col>
              </Row>

              {/* Row 2: Field search + date range + template + actions */}
              <Row gutter={[12, 8]} align="middle">
                <Col xs={8} sm={6} md={3}>
                  <Select
                    allowClear
                    placeholder="字段"
                    value={field}
                    onChange={setField}
                    style={{ width: '100%' }}
                    options={FIELD_OPTIONS}
                  />
                </Col>
                <Col xs={16} sm={10} md={7}>
                  <Input
                    allowClear
                    placeholder="字段值"
                    value={fieldValue}
                    onChange={(e) => setFieldValue(e.target.value)}
                    onPressEnter={handleSearch}
                    disabled={!field}
                  />
                </Col>
                <Col xs={12} sm={8} md={5}>
                  <RangePicker
                    style={{ width: '100%' }}
                    placeholder={['开始日期', '结束日期']}
                    onChange={(dates) => {
                      if (dates && dates[0] && dates[1]) {
                        setDateRange([dates[0].toISOString(), dates[1].toISOString()]);
                      } else {
                        setDateRange(null);
                      }
                    }}
                  />
                </Col>
                <Col xs={12} sm={6} md={4}>
                  <Select
                    allowClear
                    placeholder="模板"
                    value={profileKey}
                    onChange={setProfileKey}
                    style={{ width: '100%' }}
                    options={PROFILE_OPTIONS}
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
