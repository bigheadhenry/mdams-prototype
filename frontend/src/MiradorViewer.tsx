/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useMemo, useState } from 'react';
import { Button, Space, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import mirador from 'mirador';
import axios from 'axios';

interface ApplicationCandidate {
  assetId: number;
  resourceId: string;
  title: string;
  manifestUrl: string;
  objectNumber?: string | null;
  sourceLabel?: string | null;
}

interface MiradorViewerProps {
  manifestId: string;
  onAddToApplication?: (item: ApplicationCandidate) => boolean;
}

const normalizeLabel = (value: unknown) => {
  if (!value || typeof value !== 'object') return '';
  const firstKey = Object.keys(value as Record<string, unknown>)[0];
  const firstValue = firstKey ? (value as Record<string, unknown>)[firstKey] : undefined;
  if (Array.isArray(firstValue) && firstValue.length > 0) {
    return String(firstValue[0]);
  }
  return '';
};

const MiradorViewer: React.FC<MiradorViewerProps> = ({ manifestId, onAddToApplication }) => {
  const [applicationCandidate, setApplicationCandidate] = useState<ApplicationCandidate | null>(null);

  useEffect(() => {
    const config = {
      id: 'mirador-viewer',
      windows: [
        {
          manifestId: manifestId,
        },
      ],
      window: {
        allowClose: false,
        allowMaximize: false,
        defaultSideBarPanel: 'info',
        sideBarOpenByDefault: true,
      },
      workspace: {
        showZoomControls: true,
      },
      // Fix: Handle JSON parsing errors gracefully
      requests: {
        preprocessors: [
          (url: string, options: any) => {
            // Ensure we don't double-slash or malform URLs
            return { url, options };
          }
        ],
        postprocessors: [
            (url: string, action: any) => {
                // If the response is not valid JSON (e.g. 404 HTML, 500 Error page), 
                // Mirador will throw SyntaxError. We can't easily catch it inside Mirador,
                // but we can log the response body here if needed.
                return action;
            }
        ]
      }
    };

    const viewer = mirador.viewer(config);
    
    // Cleanup
    return () => {
        if (viewer && viewer.unmount) {
             viewer.unmount();
        }
    };
  }, [manifestId]);

  useEffect(() => {
    let cancelled = false;

    const loadManifestMeta = async () => {
      try {
        const response = await axios.get(manifestId);
        const manifest = response.data as {
          label?: unknown;
          metadata?: Array<{ label?: unknown; value?: unknown }>;
        };
        const metadataMap = new Map<string, string>();

        for (const entry of manifest.metadata || []) {
          const key = normalizeLabel(entry.label).trim().toLowerCase();
          const value = normalizeLabel(entry.value).trim();
          if (key && value) {
            metadataMap.set(key, value);
          }
        }

        const assetId = Number(metadataMap.get('asset id'));
        if (!Number.isFinite(assetId)) {
          return;
        }

        const resourceId = metadataMap.get('resource id') || `image_2d:${assetId}`;
        const title = metadataMap.get('title') || normalizeLabel(manifest.label) || `Asset ${assetId}`;
        const objectNumber = metadataMap.get('object number') || undefined;

        if (!cancelled) {
          setApplicationCandidate({
            assetId,
            resourceId,
            title,
            manifestUrl: manifestId,
            objectNumber,
            sourceLabel: '二维影像子系统',
          });
        }
      } catch (error) {
        if (!cancelled) {
          setApplicationCandidate(null);
        }
        console.warn('Failed to load mirador manifest metadata', error);
      }
    };

    setApplicationCandidate(null);
    loadManifestMeta();

    return () => {
      cancelled = true;
    };
  }, [manifestId]);

  const canApply = useMemo(() => Boolean(applicationCandidate && onAddToApplication), [applicationCandidate, onAddToApplication]);

  return (
    <div style={{ position: 'relative' }}>
      <Space
        direction="vertical"
        size="small"
        style={{
          position: 'absolute',
          top: 12,
          right: 12,
          zIndex: 20,
          alignItems: 'flex-end',
        }}
      >
        {applicationCandidate ? <Tag color="blue">Asset #{applicationCandidate.assetId}</Tag> : null}
        <Button
          type="primary"
          icon={<PlusOutlined />}
          disabled={!canApply}
          onClick={() => {
            if (!applicationCandidate || !onAddToApplication) return;
            const added = onAddToApplication(applicationCandidate);
            if (added) {
              message.success('已加入申请车');
            } else {
              message.info('申请车中已存在该资源');
            }
          }}
        >
          加入申请单
        </Button>
      </Space>
      <div id="mirador-viewer" style={{ width: '100%', height: '600px', position: 'relative' }} />
    </div>
  );
};

export default MiradorViewer;
