import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { Tabs } from 'antd';
import {
  AppstoreOutlined,
  CloudUploadOutlined,
  DashboardOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import type { ThreeDAssetSummary, ThreeDCollectionObjectSummary, ThreeDObjectGroup } from '../types/assets';
import ThreeDDashboard from './ThreeDDashboard';
import ThreeDCatalog from './ThreeDCatalog';
import ThreeDIngestWizard from './ThreeDIngestWizard';
import ThreeDOperations from './ThreeDOperations';

/* ─── 数据聚合 ─── */
const getVersionOrder = (item: ThreeDAssetSummary) => item.version_order ?? 0;
const getGroupKey = (item: ThreeDAssetSummary) =>
  `object-${item.three_d_object_id}`;
const getGroupLabel = (item: ThreeDAssetSummary) =>
  item.resource_group?.trim() || item.title?.trim() || item.filename;

/* ─── 主容器 ─── */
interface ThreeDManagementProps {
  permissions?: string[];
}

const ThreeDManagement: React.FC<ThreeDManagementProps> = ({ permissions = [] }) => {
  const [items, setItems] = useState<ThreeDAssetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [collectionObjects, setCollectionObjects] = useState<ThreeDCollectionObjectSummary[]>([]);
  const [collectionObjectLoading, setCollectionObjectLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get<ThreeDAssetSummary[]>('/api/three-d/resources');
      setItems(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchCollectionObjects = useCallback(async (query?: string) => {
    setCollectionObjectLoading(true);
    try {
      const res = await axios.get<ThreeDCollectionObjectSummary[]>('/api/three-d/collection-objects', {
        params: query ? { q: query, limit: 50 } : { limit: 50 },
      });
      setCollectionObjects(res.data);
    } finally {
      setCollectionObjectLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchItems();
    void fetchCollectionObjects();
  }, [fetchItems, fetchCollectionObjects]);

  const refresh = useCallback(() => {
    void fetchItems();
  }, [fetchItems]);

  /* ─── 按资源组聚合 ─── */
  const groupedItems = useMemo<ThreeDObjectGroup[]>(() => {
    const groups = new Map<string, ThreeDObjectGroup>();

    items.forEach((item) => {
      const key = getGroupKey(item);
      const label = getGroupLabel(item);
      const nextGroup =
        groups.get(key) ??
        ({
          key,
          label,
          versions: [],
          resourceType: item.resource_type,
          profileLabel: item.profile_label ?? null,
          objectNumber: item.object_number ?? null,
          objectName: item.object_name ?? null,
          currentVersion: null,
          webPreviewVersion: null,
          latestVersion: null,
          storageTier: item.storage_tier ?? null,
          preservationStatus: item.preservation_status ?? null,
          updatedAt: null,
          readyCount: 0,
          totalFileCount: 0,
        } as ThreeDObjectGroup);

      nextGroup.versions.push(item);
      nextGroup.resourceType = nextGroup.resourceType || item.resource_type;
      nextGroup.profileLabel = nextGroup.profileLabel || item.profile_label || null;
      nextGroup.objectNumber = nextGroup.objectNumber || item.object_number || null;
      nextGroup.objectName = nextGroup.objectName || item.object_name || null;
      nextGroup.storageTier = nextGroup.storageTier || item.storage_tier || null;
      nextGroup.preservationStatus = nextGroup.preservationStatus || item.preservation_status || null;
      if (!nextGroup.updatedAt || item.created_at > nextGroup.updatedAt) {
        nextGroup.updatedAt = item.created_at;
      }
      groups.set(key, nextGroup);
    });

    return Array.from(groups.values())
      .map((group) => {
        const versions = [...group.versions].sort((a, b) => {
          const orderDiff = getVersionOrder(a) - getVersionOrder(b);
          if (orderDiff !== 0) return orderDiff;
          return a.created_at.localeCompare(b.created_at);
        });
        const currentVersion = versions.find((v) => v.is_current) ?? versions[versions.length - 1] ?? null;
        const webPreviewVersion =
          versions.find((v) => v.is_web_preview && v.web_preview_status === 'ready') ?? null;
        const latestVersion = versions[versions.length - 1] ?? null;
        return {
          ...group,
          versions,
          currentVersion,
          webPreviewVersion,
          latestVersion,
          readyCount: versions.filter((v) => v.is_web_preview && v.web_preview_status === 'ready').length,
          totalFileCount: versions.reduce((sum, v) => sum + (v.file_count ?? 0), 0),
        };
      })
      .sort((a, b) => {
        if (a.updatedAt && b.updatedAt && a.updatedAt !== b.updatedAt) {
          return b.updatedAt.localeCompare(a.updatedAt);
        }
        return a.label.localeCompare(b.label);
      });
  }, [items]);

  /* ─── 统计 ─── */
  const overview = useMemo(() => {
    const webPreviewGroups = groupedItems.filter((g) => g.webPreviewVersion);
    const totalFileCount = groupedItems.reduce((sum, g) => sum + g.totalFileCount, 0);
    return {
      objectCount: groupedItems.length,
      representationCount: items.length,
      webPreviewGroupCount: webPreviewGroups.length,
      totalFileCount,
    };
  }, [groupedItems, items.length]);

  /* ─── Tab 定义 ─── */
  const tabItems = [
    {
      key: 'dashboard',
      label: (
        <span>
          <DashboardOutlined />
          总览看板
        </span>
      ),
      children: (
        <ThreeDDashboard
          overview={overview}
          groupedItems={groupedItems}
        />
      ),
    },
    {
      key: 'catalog',
      label: (
        <span>
          <AppstoreOutlined />
          数字对象目录
        </span>
      ),
      children: (
        <ThreeDCatalog
          groupedItems={groupedItems}
          loading={loading}
          onRefresh={refresh}
          onIngest={() => setActiveTab('ingest')}
          canReview={permissions.includes('three_d.review') || permissions.includes('system.manage')}
        />
      ),
    },
    {
      key: 'ingest',
      label: (
        <span>
          <CloudUploadOutlined />
          资源入库
        </span>
      ),
      children: (
        <ThreeDIngestWizard
          collectionObjects={collectionObjects}
          collectionObjectLoading={collectionObjectLoading}
          onFetchCollectionObjects={fetchCollectionObjects}
          onSuccess={() => {
            refresh();
            setActiveTab('catalog');
          }}
          onCancel={() => setActiveTab('catalog')}
        />
      ),
    },
    {
      key: 'operations',
      label: (
        <span>
          <ToolOutlined />
          运维与处置
        </span>
      ),
      children: (
        <ThreeDOperations
          groupedItems={groupedItems}
          onRefresh={refresh}
        />
      ),
    },
  ];

  return (
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      size="large"
      style={{ padding: '0 8px' }}
      items={tabItems}
    />
  );
};

export default ThreeDManagement;
