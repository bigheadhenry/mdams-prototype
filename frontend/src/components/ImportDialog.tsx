import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Checkbox,
  DatePicker,
  Image,
  Input,
  Modal,
  Pagination,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd';
import {
  CheckCircleFilled,
  CloudUploadOutlined,
  DatabaseOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  ImportOutlined,
  InboxOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import type {
  ImportSelectionItem,
  LookupImageItem,
  LookupResponse,
  ParsedImportRow,
} from '../types/assets';

const { Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

// ── Constants ─────────────────────────────────────────────────────────

const SOURCE_SYSTEM = 'wenwu';

// ── Helpers ───────────────────────────────────────────────────────────

/** Truncate a string to maxLen chars, adding ellipsis if needed. */
const truncate = (s: string, maxLen: number): string =>
  s.length > maxLen ? s.slice(0, maxLen) + '…' : s;

/** Build a thumbnail placeholder URL for thumbnails that fail to load. */
const FALLBACK_THUMBNAIL =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'><rect width='120' height='120' fill='%231e293b'/><text x='60' y='64' text-anchor='middle' font-size='12' fill='%2364748b'>无预览</text></svg>";

/** Parse CSV text into ParsedImportRow array. */
const parseCSVText = (text: string): { rows: ParsedImportRow[]; errors: string[] } => {
  // Strip UTF-8 BOM and trim
  const cleanText = text.replace(/^\uFEFF/, '').trim();
  // Check for empty after cleaning
  if (!cleanText) {
    return { rows: [], errors: ['输入内容为空'] };
  }
  const result = Papa.parse<string[]>(cleanText, {
    skipEmptyLines: true,
    header: false,
  });

  const rows: ParsedImportRow[] = [];
  const errors: string[] = [];

  for (let i = 0; i < result.data.length; i++) {
    const line = result.data[i];
    if (!line || line.length === 0) continue;

    const row: string[] = [];
    // Normalise — ensure at least 5 columns
    for (let j = 0; j < 5; j++) {
      row.push((line[j] || '').trim());
    }

    const [objectNumber, imageId, content, captureDate, photographer] = row;

    if (!objectNumber) {
      errors.push(`第 ${i + 1} 行: 缺少文物号`);
      continue;
    }

    rows.push({
      objectNumber,
      imageId: imageId || null,
      content: content || null,
      captureDate: captureDate || null,
      photographer: photographer || null,
      matchType: imageId ? 'exact' : 'expand',
      lineNo: i + 1,
      raw: line.join(','),
    });
  }

  return { rows, errors };
};

/** Parse Excel workbook into ParsedImportRow array. */
const parseExcelSheet = (workbook: XLSX.WorkBook): { rows: ParsedImportRow[]; errors: string[] } => {
  const rows: ParsedImportRow[] = [];
  const errors: string[] = [];

  // Use the first sheet
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) {
    errors.push('工作簿中没有工作表');
    return { rows, errors };
  }

  const sheet = workbook.Sheets[sheetName];
  const jsonData = XLSX.utils.sheet_to_json<unknown[]>(sheet, { header: 1 });

  // Find header row — look for 文物号 column
  let headerRowIdx = -1;
  const colMapping: Record<string, number> = {};

  for (let i = 0; i < Math.min(jsonData.length, 10); i++) {
    const row = jsonData[i];
    if (!row) continue;
    const headerStr = row.map((c: unknown) => String(c || '').trim().toLowerCase()).join('|');
    if (headerStr.includes('文物号')) {
      headerRowIdx = i;
      // Map columns by header name
      const headers = row.map((c: unknown) => String(c || '').trim());
      const imageIdHeaders = ['图片id', '图片编号', '图片标识', 'image_id', 'img_id'];
      const contentHeaders = ['拍摄内容', '内容', '描述'];
      const dateHeaders = ['拍摄时间', '拍摄日期', '日期', '时间'];
      const photographerHeaders = ['摄影者', '摄影师', '拍摄者', '作者', 'photographer'];

      headers.forEach((h, idx) => {
        const hl = h.toLowerCase();
        if (hl.includes('文物号') || hl.includes('编号') || hl.includes('object')) {
          if (!colMapping.objectNumber) colMapping.objectNumber = idx;
        }
        if (imageIdHeaders.includes(hl)) colMapping.imageId = idx;
        if (contentHeaders.some((k) => hl.includes(k))) colMapping.content = idx;
        if (dateHeaders.some((k) => hl.includes(k))) colMapping.captureDate = idx;
        if (photographerHeaders.some((k) => hl.includes(k))) colMapping.photographer = idx;
      });
      break;
    }
  }

  // Fallback: no header found, assume first row is header and map by position
  if (headerRowIdx === -1) {
    Object.assign(colMapping, { objectNumber: 0, imageId: 1, content: 2, captureDate: 3, photographer: 4 });
    headerRowIdx = 0;
  }

  // Parse data rows
  for (let i = headerRowIdx + 1; i < jsonData.length; i++) {
    const row = jsonData[i];
    if (!row || row.every((c: unknown) => !String(c || '').trim())) continue;

    const objectNumber = String(row[colMapping.objectNumber] || '').trim();
    if (!objectNumber) {
      errors.push(`第 ${i + 1} 行: 缺少文物号`);
      continue;
    }

    const imageId = colMapping.imageId !== undefined ? String(row[colMapping.imageId] || '').trim() : '';
    const content = colMapping.content !== undefined ? String(row[colMapping.content] || '').trim() : '';
    const captureDate = colMapping.captureDate !== undefined ? String(row[colMapping.captureDate] || '').trim() : '';
    const photographer =
      colMapping.photographer !== undefined ? String(row[colMapping.photographer] || '').trim() : '';

    rows.push({
      objectNumber,
      imageId: imageId || null,
      content: content || null,
      captureDate: captureDate || null,
      photographer: photographer || null,
      matchType: imageId ? 'exact' : 'expand',
      lineNo: i + 1,
      raw: row.join(','),
    });
  }

  return { rows, errors };
};

// ── Sub-component: ObjectNumberLookup ─────────────────────────────────

interface ObjectNumberLookupProps {
  onSelectItems: (items: LookupImageItem[]) => void;
  selectedItems: LookupImageItem[];
  onImport: () => void;
  importing: boolean;
}

const ObjectNumberLookup: React.FC<ObjectNumberLookupProps> = ({
  onSelectItems,
  selectedItems,
  onImport,
  importing,
}) => {
  const [objectNumber, setObjectNumber] = useState('');
  const [lookupResult, setLookupResult] = useState<LookupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [imageItems, setImageItems] = useState<LookupImageItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<LookupImageItem[]>([]);

  // Filter state
  const [contentFilter, setContentFilter] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[string | undefined, string | undefined]>([undefined, undefined]);
  const [photographerFilter, setPhotographerFilter] = useState<string | undefined>();

  // Unique filter options derived from data
  const contentOptions = useMemo(() => {
    const set = new Set(imageItems.map((i) => i.content).filter(Boolean) as string[]);
    return Array.from(set).sort();
  }, [imageItems]);

  const photographerOptions = useMemo(() => {
    const set = new Set(imageItems.map((i) => i.photographer).filter(Boolean) as string[]);
    return Array.from(set).sort();
  }, [imageItems]);

  const selectedKeys = useMemo(() => {
    const set = new Set(selectedItems.map((i) => `${i.sourceSystem}:${i.sourceId}`));
    return set;
  }, [selectedItems]);

  // Apply filters
  const applyFilters = useCallback(
    (items: LookupImageItem[]) => {
      let result = [...items];
      if (contentFilter) {
        result = result.filter((i) => i.content?.includes(contentFilter));
      }
      if (photographerFilter) {
        result = result.filter((i) => i.photographer?.includes(photographerFilter));
      }
      if (dateRange[0]) {
        const from = dateRange[0];
        result = result.filter((i) => i.captureDate && i.captureDate >= from);
      }
      if (dateRange[1]) {
        const to = dateRange[1];
        result = result.filter((i) => i.captureDate && i.captureDate <= to);
      }
      return result;
    },
    [contentFilter, dateRange, photographerFilter],
  );

  // Trigger lookup
  const handleSearch = useCallback(async () => {
    if (!objectNumber.trim()) {
      message.warning('请输入文物号');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get<LookupResponse>('/api/cart/lookup', {
        params: { object_number: objectNumber.trim() },
      });
      const data = response.data;
      setLookupResult(data);
      setImageItems(data.items || []);
      setFilteredItems(applyFilters(data.items || []));
    } catch (err: unknown) {
      console.error('lookup failed', err);
      message.error('文物号查询失败，请检查文物号是否正确');
      setLookupResult(null);
      setImageItems([]);
      setFilteredItems([]);
    } finally {
      setLoading(false);
    }
  }, [objectNumber, applyFilters]);

  // Re-apply filters when filter values change
  const handleFilterChange = useCallback(() => {
    setFilteredItems(applyFilters(imageItems));
  }, [imageItems, applyFilters]);

  // Toggle a single item
  const toggleItem = useCallback(
    (item: LookupImageItem) => {
      const key = `${item.sourceSystem}:${item.sourceId}`;
      const isSelected = selectedKeys.has(key);
      if (isSelected) {
        onSelectItems(selectedItems.filter((i) => `${i.sourceSystem}:${i.sourceId}` !== key));
      } else {
        onSelectItems([...selectedItems, item]);
      }
    },
    [selectedItems, selectedKeys, onSelectItems],
  );

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  // Paginated items
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, currentPage, pageSize]);

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [contentFilter, dateRange, photographerFilter]);
  const toggleSelectAll = useCallback(() => {
    const allSelected = filteredItems.every((item) =>
      selectedKeys.has(`${item.sourceSystem}:${item.sourceId}`),
    );
    if (allSelected) {
      const filteredKeys = new Set(filteredItems.map((i) => `${i.sourceSystem}:${i.sourceId}`));
      onSelectItems(selectedItems.filter((i) => !filteredKeys.has(`${i.sourceSystem}:${i.sourceId}`)));
    } else {
      const existingKeys = new Set(selectedItems.map((i) => `${i.sourceSystem}:${i.sourceId}`));
      const merged = [...selectedItems];
      for (const item of filteredItems) {
        if (!existingKeys.has(`${item.sourceSystem}:${item.sourceId}`)) {
          merged.push(item);
        }
      }
      onSelectItems(merged);
    }
  }, [filteredItems, selectedItems, selectedKeys, onSelectItems]);

  const allFilteredSelected =
    filteredItems.length > 0 &&
    filteredItems.every((item) => selectedKeys.has(`${item.sourceSystem}:${item.sourceId}`));

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {/* Search bar */}
      <Space.Compact style={{ width: '100%' }}>
        <Input
          placeholder="输入文物号，例如 故00123456"
          value={objectNumber}
          onChange={(e) => setObjectNumber(e.target.value)}
          onPressEnter={handleSearch}
          style={{ fontSize: 14 }}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
          查询
        </Button>
      </Space.Compact>

      {/* Result area */}
      {lookupResult && (
        <>
          <Space wrap style={{ width: '100%' }}>
            <Text strong>
              文物号: <Tag color="gold">{lookupResult.objectNumber}</Tag>
            </Text>
            {lookupResult.objectName && <Text type="secondary">({lookupResult.objectName})</Text>}
            <Text type="secondary">
              共 {lookupResult.total} 张影像，已选 {selectedItems.length} 张
            </Text>
          </Space>

          {/* Filter bar */}
          <Card size="small" title="筛选条件" style={{ width: '100%' }}>
            <Space wrap>
              <Select
                allowClear
                placeholder="拍摄内容"
                value={contentFilter}
                onChange={(v) => {
                  setContentFilter(v);
                  setTimeout(handleFilterChange, 0);
                }}
                style={{ width: 140 }}
                options={contentOptions.map((c) => ({ value: c, label: c }))}
              />
              <RangePicker
                format="YYYY-MM-DD"
                onChange={(dates) => {
                  setDateRange([
                    dates?.[0]?.format('YYYY-MM-DD') || undefined,
                    dates?.[1]?.format('YYYY-MM-DD') || undefined,
                  ]);
                  setTimeout(handleFilterChange, 0);
                }}
              />
              <Select
                allowClear
                placeholder="摄影者"
                value={photographerFilter}
                onChange={(v) => {
                  setPhotographerFilter(v);
                  setTimeout(handleFilterChange, 0);
                }}
                style={{ width: 140 }}
                options={photographerOptions.map((p) => ({ value: p, label: p }))}
              />
            </Space>
          </Card>

          {/* Thumbnail grid */}
          <div style={{ width: '100%' }}>
            <Space style={{ marginBottom: 12 }}>
              <Checkbox checked={allFilteredSelected} onChange={toggleSelectAll}>
                {allFilteredSelected ? '取消全选' : '全选当前筛选结果'}
              </Checkbox>
              <Text type="secondary">({filteredItems.length} 张)</Text>
            </Space>

            {filteredItems.length === 0 ? (
              <Text type="secondary">无匹配的影像</Text>
            ) : (
              <>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                  gap: 12,
                }}
              >
                {paginatedItems.map((item) => {
                  const key = `${item.sourceSystem}:${item.sourceId}`;
                  const isSelected = selectedKeys.has(key);
                  return (
                    <Card
                      key={key}
                      size="small"
                      hoverable
                      onClick={() => toggleItem(item)}
                      style={{
                        borderColor: isSelected ? '#1677ff' : undefined,
                        background: isSelected ? 'rgba(22,119,255,0.04)' : undefined,
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ position: 'relative' }}>
                        <Image
                          src={item.thumbnailUrl || undefined}
                          alt={item.title}
                          preview={false}
                          fallback={FALLBACK_THUMBNAIL}
                          style={{
                            width: '100%',
                            height: 120,
                            objectFit: 'cover',
                            borderRadius: 6,
                          }}
                        />
                        {isSelected && (
                          <CheckCircleFilled
                            style={{
                              position: 'absolute',
                              top: 4,
                              right: 4,
                              fontSize: 20,
                              color: '#1677ff',
                              background: '#fff',
                              borderRadius: '50%',
                            }}
                          />
                        )}
                      </div>
                      <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.6 }}>
                        <Text strong style={{ fontSize: 12 }} ellipsis={{ tooltip: item.title }}>
                          {truncate(item.title, 28)}
                        </Text>
                        <br />
                        {item.resolution && (
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {item.resolution}
                          </Text>
                        )}
                        {item.captureDate && (
                          <>
                            <br />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              📅 {item.captureDate}
                            </Text>
                          </>
                        )}
                        {item.photographer && (
                          <>
                            <br />
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              👤 {item.photographer}
                            </Text>
                          </>
                        )}
                      </div>
                    </Card>
                  );
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 16 }}>
                <Pagination
                  current={currentPage}
                  pageSize={pageSize}
                  total={filteredItems.length}
                  onChange={(page) => setCurrentPage(page)}
                  showSizeChanger={false}
                  showTotal={(total) => `共 ${total} 张`}
                />
              </div>
              </>
            )}
          </div>

          {/* Import button */}
          <div style={{ textAlign: 'right', width: '100%' }}>
            <Button
              type="primary"
              icon={<ImportOutlined />}
              size="large"
              onClick={onImport}
              loading={importing}
              disabled={selectedItems.length === 0}
            >
              导入 {selectedItems.length > 0 ? `(${selectedItems.length} 项)` : ''}
            </Button>
          </div>
        </>
      )}
    </Space>
  );
};



// ── Sub-component: ImportPreviewTable ─────────────────────────────────

interface ImportPreviewTableProps {
  rows: ParsedImportRow[];
  onConfirm: (items: ImportSelectionItem[]) => void;
  onBack: () => void;
  importing: boolean;
  onLookup: (objectNumber: string) => Promise<LookupImageItem[]>;
}

const ImportPreviewTable: React.FC<ImportPreviewTableProps> = ({
  rows,
  onConfirm,
  onBack,
  importing,
  onLookup,
}) => {
  const exactCount = rows.filter((r) => r.matchType === 'exact').length;
  const expandCount = rows.filter((r) => r.matchType === 'expand').length;

  // Inline expand state: per lineNo => fetched images
  const [expandData, setExpandData] = useState<
    Record<number, { loading: boolean; items: LookupImageItem[]; error?: string }>
  >({});

  // Selected items per objectNumber (key = objectNumber)
  const [selectedExpandItems, setSelectedExpandItems] = useState<Record<string, LookupImageItem[]>>(
    {},
  );

  // Expanded row keys
  const [expandedRowKeys, setExpandedRowKeys] = useState<React.Key[]>([]);

  // Compute total selected expand image count
  const totalExpandSelected = useMemo(
    () => Object.values(selectedExpandItems).reduce((sum, arr) => sum + arr.length, 0),
    [selectedExpandItems],
  );

  const totalItems = exactCount + totalExpandSelected;

  // Handle expand / collapse
  const handleExpand = useCallback(
    async (expanded: boolean, record: ParsedImportRow) => {
      if (record.matchType !== 'expand') return;

      if (!expanded) {
        setExpandedRowKeys((prev) => prev.filter((k) => k !== record.lineNo));
        return;
      }

      setExpandedRowKeys((prev) => [...prev, record.lineNo]);

      // Already fetched
      if (expandData[record.lineNo]?.items?.length > 0) return;

      // Fetch
      setExpandData((prev) => ({
        ...prev,
        [record.lineNo]: { loading: true, items: [] },
      }));

      try {
        const items = await onLookup(record.objectNumber);
        setExpandData((prev) => ({
          ...prev,
          [record.lineNo]: { loading: false, items },
        }));

        // If this objectNumber hasn't been initialised yet, initialise with empty selection
        setSelectedExpandItems((prev) => {
          if (prev[record.objectNumber] === undefined) {
            return { ...prev, [record.objectNumber]: [] };
          }
          return prev;
        });
      } catch (err) {
        console.error('expand lookup failed', err);
        setExpandData((prev) => ({
          ...prev,
          [record.lineNo]: { loading: false, items: [], error: '影像查询失败' },
        }));
      }
    },
    [onLookup, expandData],
  );

  // Toggle selection of an image item within an expanded row
  const toggleExpandItem = useCallback(
    (objectNumber: string, item: LookupImageItem) => {
      setSelectedExpandItems((prev) => {
        const current = prev[objectNumber] || [];
        const key = `${item.sourceSystem}:${item.sourceId}`;
        const exists = current.some(
          (i) => `${i.sourceSystem}:${i.sourceId}` === key,
        );
        return {
          ...prev,
          [objectNumber]: exists
            ? current.filter((i) => `${i.sourceSystem}:${i.sourceId}` !== key)
            : [...current, item],
        };
      });
    },
    [],
  );

  // Select all / deselect all for a given object number
  const toggleSelectAllForObject = useCallback(
    (objectNumber: string, items: LookupImageItem[]) => {
      setSelectedExpandItems((prev) => {
        const current = prev[objectNumber] || [];
        const currentKeys = new Set(
          current.map((i) => `${i.sourceSystem}:${i.sourceId}`),
        );
        const allSelected = items.every((item) =>
          currentKeys.has(`${item.sourceSystem}:${item.sourceId}`),
        );

        if (allSelected) {
          // Deselect all for this object number
          const deselectedKeys = new Set(
            items.map((i) => `${i.sourceSystem}:${i.sourceId}`),
          );
          return {
            ...prev,
            [objectNumber]: current.filter(
              (i) => !deselectedKeys.has(`${i.sourceSystem}:${i.sourceId}`),
            ),
          };
        } else {
          // Select all for this object number
          const existingKeys = new Set(
            current.map((i) => `${i.sourceSystem}:${i.sourceId}`),
          );
          const merged = [...current];
          for (const item of items) {
            if (!existingKeys.has(`${item.sourceSystem}:${item.sourceId}`)) {
              merged.push(item);
            }
          }
          return { ...prev, [objectNumber]: merged };
        }
      });
    },
    [],
  );

  // Handle final confirm: build ImportSelectionItem[]
  const handleConfirm = useCallback(() => {
    // Exact rows → items
    const exactItems: ImportSelectionItem[] = rows
      .filter((r) => r.matchType === 'exact')
      .map((row) => ({
        sourceSystem: SOURCE_SYSTEM,
        sourceId: row.imageId!,
        title: `${row.objectNumber}${row.content ? ` - ${row.content}` : ''}`,
        objectNumber: row.objectNumber,
        thumbnailUrl: null,
        manifestUrl: null,
        note: `导入: 精确匹配 | ${row.content ? `拍摄内容: ${row.content}` : ''}${row.photographer ? ` | 摄影者: ${row.photographer}` : ''}`,
      }));

    // Expand selections → items
    const expandItems: ImportSelectionItem[] = [];
    for (const [, items] of Object.entries(selectedExpandItems)) {
      for (const item of items) {
        expandItems.push({
          sourceSystem: item.sourceSystem,
          sourceId: item.sourceId,
          title: item.title,
          objectNumber: item.objectNumber || null,
          thumbnailUrl: item.thumbnailUrl || null,
          manifestUrl: item.manifestUrl || null,
        });
      }
    }

    const allItems = [...exactItems, ...expandItems];
    // Convert camelCase to snake_case for backend API
    onConfirm(allItems.map((item) => {
      const snake: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(item)) {
        snake[k.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`)] = v;
      }
      return snake as unknown as ImportSelectionItem;
    }));
  }, [rows, selectedExpandItems, onConfirm]);

  // Expanded row renderer — thumbnail grid with checkboxes
  const expandedRowRender = useCallback(
    (record: ParsedImportRow) => {
      if (record.matchType !== 'expand') return null;
      const data = expandData[record.lineNo];

      if (!data || data.loading) {
        return (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <Text type="secondary">正在查询关联影像...</Text>
          </div>
        );
      }

      if (data.error) {
        return (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <Text type="danger">{data.error}</Text>
          </div>
        );
      }

      const items = data.items;
      const objSelections = selectedExpandItems[record.objectNumber] || [];
      const selectedKeys = new Set(
        objSelections.map((i) => `${i.sourceSystem}:${i.sourceId}`),
      );

      const allSelected =
        items.length > 0 &&
        items.every((item) =>
          selectedKeys.has(`${item.sourceSystem}:${item.sourceId}`),
        );

      if (items.length === 0) {
        return (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <Text type="secondary">未找到关联影像</Text>
          </div>
        );
      }

      return (
        <div style={{ padding: '8px 0' }}>
          <Space style={{ marginBottom: 8 }}>
            <Checkbox
              checked={allSelected}
              onChange={() => toggleSelectAllForObject(record.objectNumber, items)}
            >
              {allSelected ? '取消全选' : '全选'}
            </Checkbox>
            <Text type="secondary">
              文物 {record.objectNumber} — 共 {items.length} 张，已选{' '}
              {objSelections.length} 张
            </Text>
          </Space>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
              gap: 10,
            }}
          >
            {items.map((item) => {
              const key = `${item.sourceSystem}:${item.sourceId}`;
              const isSelected = selectedKeys.has(key);
              return (
                <Card
                  key={key}
                  size="small"
                  hoverable
                  onClick={() => toggleExpandItem(record.objectNumber, item)}
                  style={{
                    borderColor: isSelected ? '#1677ff' : undefined,
                    background: isSelected ? 'rgba(22,119,255,0.04)' : undefined,
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ position: 'relative' }}>
                    <Image
                      src={item.thumbnailUrl || undefined}
                      alt={item.title}
                      preview={false}
                      fallback={FALLBACK_THUMBNAIL}
                      style={{
                        width: '100%',
                        height: 110,
                        objectFit: 'cover',
                        borderRadius: 6,
                      }}
                    />
                    {isSelected && (
                      <CheckCircleFilled
                        style={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          fontSize: 18,
                          color: '#1677ff',
                          background: '#fff',
                          borderRadius: '50%',
                        }}
                      />
                    )}
                  </div>
                  <div style={{ marginTop: 4, fontSize: 11, lineHeight: 1.5 }}>
                    <Text strong style={{ fontSize: 11 }} ellipsis={{ tooltip: item.title }}>
                      {truncate(item.title, 24)}
                    </Text>
                    {item.resolution && (
                      <>
                        <br />
                        <Text type="secondary" style={{ fontSize: 10 }}>
                          {item.resolution}
                        </Text>
                      </>
                    )}
                    {item.captureDate && (
                      <>
                        <br />
                        <Text type="secondary" style={{ fontSize: 10 }}>
                          📅 {item.captureDate}
                        </Text>
                      </>
                    )}
                    {item.photographer && (
                      <>
                        <br />
                        <Text type="secondary" style={{ fontSize: 10 }}>
                          👤 {item.photographer}
                        </Text>
                      </>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      );
    },
    [
      expandData,
      selectedExpandItems,
      toggleExpandItem,
      toggleSelectAllForObject,
    ],
  );

  const columns = [
    {
      title: '行号',
      dataIndex: 'lineNo',
      key: 'lineNo',
      width: 60,
    },
    {
      title: '文物号',
      dataIndex: 'objectNumber',
      key: 'objectNumber',
      render: (_: unknown, record: ParsedImportRow) => (
        <Tag color={record.matchType === 'exact' ? 'blue' : 'green'}>
          {record.matchType === 'exact' ? '🔵' : '🟢'} {record.objectNumber}
        </Tag>
      ),
    },
    {
      title: '图片ID',
      dataIndex: 'imageId',
      key: 'imageId',
      render: (value: string | null | undefined) =>
        value ? <Tag color="blue">{value}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '拍摄内容',
      dataIndex: 'content',
      key: 'content',
      render: (value: string | null | undefined) => value || <Text type="secondary">—</Text>,
    },
    {
      title: '拍摄时间',
      dataIndex: 'captureDate',
      key: 'captureDate',
      render: (value: string | null | undefined) => value || <Text type="secondary">—</Text>,
    },
    {
      title: '摄影者',
      dataIndex: 'photographer',
      key: 'photographer',
      render: (value: string | null | undefined) => value || <Text type="secondary">—</Text>,
    },
    {
      title: '匹配方式',
      dataIndex: 'matchType',
      key: 'matchType',
      width: 100,
      render: (value: string) => (
        <Tag color={value === 'exact' ? 'blue' : 'green'}>
          {value === 'exact' ? '精确匹配' : '展开多图'}
        </Tag>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Space wrap>
        <Text strong>预览解析结果</Text>
        <Tag color="blue">精确匹配: {exactCount} 项</Tag>
        <Tag color="green">展开多图: {expandCount} 项</Tag>
        <Tag>总计: {rows.length} 项</Tag>
      </Space>

      <Table<ParsedImportRow>
        dataSource={rows}
        columns={columns}
        rowKey="lineNo"
        size="small"
        pagination={false}
        scroll={{ y: 320 }}
        expandable={{
          expandedRowRender,
          expandedRowKeys,
          onExpand: handleExpand,
          rowExpandable: (record) => record.matchType === 'expand',
        }}
      />

      <Paragraph type="secondary" style={{ fontSize: 12 }}>
        🔵 <Tag color="blue">精确匹配</Tag> — 有图片ID，直接定位到具体影像
        <br />
        🟢 <Tag color="green">展开多图</Tag> — 点击行首▶展开，勾选需要导入的影像
      </Paragraph>

      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button onClick={onBack}>返回修改</Button>
          <Button
            type="primary"
            icon={<ImportOutlined />}
            onClick={handleConfirm}
            loading={importing}
            disabled={totalItems === 0}
          >
            确认导入 ({totalItems} 项)
          </Button>
        </Space>
      </div>
    </Space>
  );
};

// ── Main ImportDialog Component ───────────────────────────────────────

interface ImportDialogProps {
  visible: boolean;
  onClose: () => void;
  onImport: (items: ImportSelectionItem[]) => Promise<void>;
}

const ImportDialog: React.FC<ImportDialogProps> = ({ visible, onClose, onImport }) => {
  const [activeTab, setActiveTab] = useState<string>('lookup');
  const [importing, setImporting] = useState(false);

  // Tab 1: Lookup state
  const [lookupSelections, setLookupSelections] = useState<LookupImageItem[]>([]);

  // Tab 2: Paste state
  const [pasteText, setPasteText] = useState('');
  const [parsedRows, setParsedRows] = useState<ParsedImportRow[]>([]);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [showPastePreview, setShowPastePreview] = useState(false);

  // Tab 3: File upload state
  const [fileRows, setFileRows] = useState<ParsedImportRow[]>([]);
  const [fileErrors, setFileErrors] = useState<string[]>([]);
  const [showFilePreview, setShowFilePreview] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  // Reset all state when dialog opens
  const resetState = useCallback(() => {
    setLookupSelections([]);
    setPasteText('');
    setParsedRows([]);
    setParseErrors([]);
    setShowPastePreview(false);
    setFileRows([]);
    setFileErrors([]);
    setShowFilePreview(false);
    setFileName(null);
    setActiveTab('lookup');
  }, []);

  // ── Import handler ────────────────────────────────────────────────

  const handleImport = useCallback(
    async (items: ImportSelectionItem[]) => {
      if (items.length === 0) {
        message.warning('请至少选择一项');
        return;
      }
      setImporting(true);
      try {
        await onImport(items);
        message.success(`成功导入 ${items.length} 项`);
        resetState();
        onClose();
      } catch (err: unknown) {
        console.error('import failed', err);
        message.error('导入失败，请重试');
      } finally {
        setImporting(false);
      }
    },
    [onImport, onClose, resetState],
  );

  // ── Handle lookup tab import ─────────────────────────────────────

  const handleLookupImport = useCallback(async () => {
    const items: ImportSelectionItem[] = lookupSelections.map((item) => ({
      sourceSystem: item.sourceSystem,
      sourceId: item.sourceId,
      title: item.title,
      objectNumber: item.objectNumber || null,
      thumbnailUrl: item.thumbnailUrl || null,
      manifestUrl: item.manifestUrl || null,
    }));
    await handleImport(items);
  }, [lookupSelections, handleImport]);

  // ── Handle paste parsing ─────────────────────────────────────────

  const handleParsePaste = useCallback(() => {
    if (!pasteText.trim()) {
      message.warning('请粘贴文本');
      return;
    }

    const { rows, errors } = parseCSVText(pasteText);
    setParsedRows(rows);
    setParseErrors(errors);
    setShowPastePreview(true);
  }, [pasteText]);

  // ── Handle paste confirm ─────────────────────────────────────────

  const handlePasteConfirm = useCallback(
    async (items: ImportSelectionItem[]) => {
      await handleImport(items);
    },
    [handleImport],
  );

  // ── Handle file upload parsing ───────────────────────────────────

  const handleFileParse = useCallback(
    (file: File) => {
      setFileName(file.name);

      // Check file size (max 50MB)
      const MAX_FILE_SIZE = 50 * 1024 * 1024;
      if (file.size > MAX_FILE_SIZE) {
        message.error('文件大小超过 50MB 限制，请拆分后重试');
        return false;
      }

      const ext = file.name.split('.').pop()?.toLowerCase() || '';

      if (ext !== 'csv' && ext !== 'xlsx' && ext !== 'xls') {
        message.error('请上传 CSV 或 Excel 文件');
        return false;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const data = e.target?.result;
        if (!data) {
          message.error('文件读取失败');
          return;
        }

        try {
          if (ext === 'csv') {
            // Auto-detect encoding: try UTF-8 first, fall back to GBK
            const raw = data as string;
            // Check for GBK by looking for common Chinese bytes in Latin-1
            const text = raw.charCodeAt(0) > 255
              ? new TextDecoder('gbk').decode(new TextEncoder().encode(raw))
              : raw;
            const { rows, errors } = parseCSVText(text);
            setFileRows(rows);
            setFileErrors(errors);
          } else {
            const workbook = XLSX.read(data, { type: 'array' });
            const { rows, errors } = parseExcelSheet(workbook);
            setFileRows(rows);
            setFileErrors(errors);
          }
          setShowFilePreview(true);
        } catch (err) {
          console.error('parse error', err);
          message.error('文件解析失败，请检查文件格式');
        }
      };

      if (ext === 'csv') {
        reader.readAsText(file, 'UTF-8');
      } else {
        reader.readAsArrayBuffer(file);
      }

      // Prevent upload — we handle parsing ourselves
      return false;
    },
    [],
  );

  const handleFileConfirm = useCallback(
    async (items: ImportSelectionItem[]) => {
      await handleImport(items);
    },
    [handleImport],
  );

  // ── Lookup function for inline expand ────────────────────────────

  const lookupFn = useCallback(async (objectNumber: string): Promise<LookupImageItem[]> => {
    try {
      const response = await axios.get('/api/cart/lookup', {
        params: { object_number: objectNumber },
      });
      // Convert backend snake_case response → frontend camelCase
      return (response.data?.items || []).map((item: Record<string, unknown>) => ({
        sourceSystem: item.source_system as string,
        sourceId: item.source_id as string,
        title: item.title as string,
        thumbnailUrl: (item.thumbnail_url as string) || null,
        resolution: (item.resolution as string) || null,
        photographer: (item.photographer as string) || null,
        captureDate: (item.shoot_date || item.capture_date) as string | null,
        content: (item.content as string) || null,
        fileSize: (item.file_size as number) || null,
        mimeType: (item.mime_type as string) || null,
        manifestUrl: (item.manifest_url as string) || null,
        objectNumber: item.object_number as string,
      }));
    } catch (err) {
      console.error('lookup failed for', objectNumber, err);
      message.error(`查询 ${objectNumber} 的影像失败，请检查文物号或网络`);
      return [];
    }
  }, []);

  // ── Dialog footer ─────────────────────────────────────────────────

  const footer = (
    <Space>
      <Button onClick={onClose}>取消</Button>
    </Space>
  );

  // ── Tab items ─────────────────────────────────────────────────────

  const tabItems = useMemo(
    () => [
      {
        key: 'lookup',
        label: (
          <span>
            <SearchOutlined /> 查文物号
          </span>
        ),
        children: (
          <ObjectNumberLookup
            onSelectItems={setLookupSelections}
            selectedItems={lookupSelections}
            onImport={handleLookupImport}
            importing={importing}
          />
        ),
      },
      {
        key: 'paste',
        label: (
          <span>
            <FileTextOutlined /> 粘贴文本
          </span>
        ),
        children: (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {!showPastePreview ? (
              <>
                <Paragraph type="secondary">
                  粘贴 CSV 格式文本，每行格式：<Text code>文物号, 图片ID, 拍摄内容, 拍摄时间, 摄影者</Text>
                </Paragraph>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    示例：
                  </Text>
                  <pre
                    style={{
                      background: '#f5f5f5',
                      padding: 8,
                      borderRadius: 4,
                      fontSize: 12,
                      marginTop: 4,
                    }}
                  >
                    故00123456, IMG-101, 正面全图, 2024-03-15, 张莹{'\n'}
                    故00123456, IMG-102, 款识局部, 2024-03-15, 张莹{'\n'}
                    故00234567, , , , {'\n'}
                    故00345678, , , ,
                  </pre>
                </div>
                <TextArea
                  rows={8}
                  placeholder="在此粘贴 CSV 数据..."
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                />
                <Button type="primary" icon={<FileTextOutlined />} onClick={handleParsePaste}>
                  解析文本
                </Button>
              </>
            ) : (
              <>
                {parseErrors.length > 0 && (
                  <Card size="small" title="解析警告" style={{ borderColor: '#faad14' }}>
                    {parseErrors.map((err, idx) => (
                      <Text key={idx} type="warning" style={{ display: 'block', fontSize: 12 }}>
                        {err}
                      </Text>
                    ))}
                  </Card>
                )}
                {parsedRows.length === 0 ? (
                  <Text type="secondary">未能解析出有效数据，请检查文本格式</Text>
                ) : (
                  <ImportPreviewTable
                    rows={parsedRows}
                    onConfirm={handlePasteConfirm}
                    onBack={() => setShowPastePreview(false)}
                    importing={importing}
                    onLookup={lookupFn}
                  />
                )}
              </>
            )}
          </Space>
        ),
      },
      {
        key: 'file',
        label: (
          <span>
            <CloudUploadOutlined /> 上传文件
          </span>
        ),
        children: (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {!showFilePreview ? (
              <>
                <Paragraph type="secondary">
                  支持 CSV 或 Excel 格式，至少包含<Text strong>文物号</Text>列。
                  可选列：<Text code>图片ID</Text>、<Text code>拍摄内容</Text>、<Text code>拍摄时间</Text>、<Text code>摄影者</Text>
                </Paragraph>

                <Dragger
                  accept=".csv,.xlsx,.xls"
                  showUploadList={false}
                  beforeUpload={(file) => handleFileParse(file)}
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                  <p className="ant-upload-hint">支持 CSV、Excel (.xlsx / .xls) 格式</p>
                </Dragger>
              </>
            ) : (
              <>
                <Space>
                  <FileExcelOutlined style={{ fontSize: 20, color: '#52c41a' }} />
                  <Text strong>{fileName}</Text>
                  {fileErrors.length > 0 && (
                    <Tag color="warning">解析警告: {fileErrors.length} 条</Tag>
                  )}
                </Space>

                {fileErrors.length > 0 && (
                  <Card size="small" title="解析警告" style={{ borderColor: '#faad14' }}>
                    {fileErrors.slice(0, 10).map((err, idx) => (
                      <Text key={idx} type="warning" style={{ display: 'block', fontSize: 12 }}>
                        {err}
                      </Text>
                    ))}
                    {fileErrors.length > 10 && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        ...还有 {fileErrors.length - 10} 条警告
                      </Text>
                    )}
                  </Card>
                )}

                {fileRows.length === 0 ? (
                  <Text type="secondary">未能解析出有效数据，请检查文件格式</Text>
                ) : (
                  <ImportPreviewTable
                    rows={fileRows}
                    onConfirm={handleFileConfirm}
                    onBack={() => setShowFilePreview(false)}
                    importing={importing}
                    onLookup={lookupFn}
                  />
                )}
              </>
            )}
          </Space>
        ),
      },
    ],
    [
      lookupSelections,
      importing,
      handleLookupImport,
      showPastePreview,
      pasteText,
      parseErrors,
      parsedRows,
      handleParsePaste,
      handlePasteConfirm,
      showFilePreview,
      fileName,
      fileErrors,
      fileRows,
      handleFileParse,
      handleFileConfirm,
      lookupFn,
    ],
  );

  return (
    <Modal
      title={
        <Space>
          <DatabaseOutlined />
          <span>批量导入资源</span>
        </Space>
      }
      open={visible}
      onCancel={() => {
        resetState();
        onClose();
      }}
      footer={footer}
      width={900}
      destroyOnClose
      style={{ top: 40 }}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </Modal>
  );
};

export default ImportDialog;
