/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Button, Progress, Spin, Space, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import mirador from 'mirador';
import axios from 'axios';
import MiradorAiPanel from './MiradorAiPanel';

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

const AUTH_TOKEN_KEY = 'mdams.auth.token';
const AUTH_HEADER_HOST_PATHS = ['/api', '/auth'];

type PreviewLoadStage = 'loading_manifest' | 'initializing_viewer' | 'loading_tiles' | 'ready' | 'error';

const normalizeLabel = (value: unknown) => {
  if (!value || typeof value !== 'object') return '';
  const firstKey = Object.keys(value as Record<string, unknown>)[0];
  const firstValue = firstKey ? (value as Record<string, unknown>)[firstKey] : undefined;
  if (Array.isArray(firstValue) && firstValue.length > 0) {
    return String(firstValue[0]);
  }
  return '';
};

const getStageLabel = (stage: PreviewLoadStage) => {
  switch (stage) {
    case 'loading_manifest':
      return '正在加载预览信息';
    case 'initializing_viewer':
      return '正在初始化 Mirador';
    case 'loading_tiles':
      return '正在生成 IIIF 切片';
    case 'ready':
      return '预览已完成';
    case 'error':
      return '预览加载失败';
    default:
      return '正在加载预览';
  }
};

const shouldAttachAuthHeader = (url: string) => {
  try {
    const parsed = new URL(url, window.location.origin);
    return AUTH_HEADER_HOST_PATHS.some((path) => parsed.pathname.startsWith(path));
  } catch {
    return false;
  }
};

const MiradorViewer: React.FC<MiradorViewerProps> = ({ manifestId, onAddToApplication }) => {
  const [applicationCandidate, setApplicationCandidate] = useState<ApplicationCandidate | null>(null);
  const [manifest, setManifest] = useState<Record<string, unknown> | null>(null);
  const [previewStage, setPreviewStage] = useState<PreviewLoadStage>('loading_manifest');
  const [previewProgress, setPreviewProgress] = useState(8);
  const [previewElapsedSeconds, setPreviewElapsedSeconds] = useState(0);
  const [previewStats, setPreviewStats] = useState<{
    manifestLoadedMs?: number;
    firstTileRenderedMs?: number;
  }>({});

  const previewStartAtRef = useRef<number>(performance.now());
  const firstTileReportedRef = useRef(false);
  const viewerApiRef = useRef<any>(null);

  const stageLabel = useMemo(() => getStageLabel(previewStage), [previewStage]);
  const statusLabel = useMemo(() => stageLabel, [stageLabel]);

  const isRendered = () => {
    const root = document.getElementById('mirador-viewer');
    if (!root) return false;

    const visibleCanvas = Array.from(root.querySelectorAll('canvas')).some((canvas) => {
      const rect = canvas.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    });
    if (visibleCanvas) return true;

    return Array.from(root.querySelectorAll('img')).some((img) => {
      const image = img as HTMLImageElement;
      return image.complete && image.naturalWidth > 0 && image.naturalHeight > 0;
    });
  };

  useEffect(() => {
    previewStartAtRef.current = performance.now();
    firstTileReportedRef.current = false;
    setPreviewStats({});
  }, [manifestId]);

  useEffect(() => {
    if (!manifest) return;

    setPreviewStage('initializing_viewer');
    setPreviewProgress((current) => Math.max(current, 35));

    const config = {
      id: 'mirador-viewer',
      windows: [
        {
          manifestId,
          manifest,
        },
      ],
      window: {
        allowClose: false,
        allowFullscreen: false,
        allowMaximize: false,
        allowTopMenuButton: false,
        allowWindowSideBar: false,
        defaultView: 'single',
        hideWindowTitle: true,
        sideBarOpen: false,
        sideBarPanel: 'info',
      },
      workspace: {
        showZoomControls: true,
      },
      requests: {
        preprocessors: [
          (url: string, options: any) => {
            const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
            if (!token || !shouldAttachAuthHeader(url)) {
              return options;
            }
            return {
              ...options,
              headers: {
                ...(options?.headers || {}),
                Authorization: `Bearer ${token}`,
              },
            };
          },
        ],
        postprocessors: [(url: string, action: any) => action],
      },
    };

    const viewer = mirador.viewer(config);
    viewerApiRef.current = viewer;
    let readyDetected = false;

    const elapsedTimer = window.setInterval(() => {
      setPreviewElapsedSeconds((current) => current + 1);
    }, 1000);

    const progressTimer = window.setInterval(() => {
      if (readyDetected) return;
      setPreviewProgress((current) => Math.min(94, current + 3));
    }, 700);

    const renderTimer = window.setInterval(() => {
      if (isRendered()) {
        if (!firstTileReportedRef.current) {
          firstTileReportedRef.current = true;
          setPreviewStats((current) => ({
            ...current,
            firstTileRenderedMs: Math.max(0, Math.round(performance.now() - previewStartAtRef.current)),
          }));
        }
        readyDetected = true;
        setPreviewStage('ready');
        setPreviewProgress(100);
        setPreviewElapsedSeconds((current) => Math.max(current, 1));
        window.clearInterval(renderTimer);
        window.clearInterval(progressTimer);
        window.clearInterval(elapsedTimer);
        return;
      }
      setPreviewStage((current) => (current === 'initializing_viewer' ? 'loading_tiles' : current));
    }, 300);

    return () => {
      window.clearInterval(progressTimer);
      window.clearInterval(renderTimer);
      window.clearInterval(elapsedTimer);
      if (viewer && viewer.unmount) {
        viewer.unmount();
      }
      if (viewerApiRef.current === viewer) {
        viewerApiRef.current = null;
      }
    };
  }, [manifest, manifestId]);

  useEffect(() => {
    let cancelled = false;

    const loadManifestMeta = async () => {
      try {
        setPreviewStage('loading_manifest');
        setPreviewProgress(10);
        setPreviewElapsedSeconds(0);

        const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
        const response = await axios.get(manifestId, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });

        const manifestData = response.data as {
          label?: unknown;
          metadata?: Array<{ label?: unknown; value?: unknown }>;
        };
        const metadataMap = new Map<string, string>();

        for (const entry of manifestData.metadata || []) {
          const key = normalizeLabel(entry.label).trim().toLowerCase();
          const value = normalizeLabel(entry.value).trim();
          if (key && value) {
            metadataMap.set(key, value);
          }
        }

        const assetId = Number(metadataMap.get('asset id'));
        if (!Number.isFinite(assetId)) {
          throw new Error('Manifest 元数据中缺少资源 ID');
        }

        const resourceId = metadataMap.get('resource id') || `image_2d:${assetId}`;
        const title = metadataMap.get('title') || normalizeLabel(manifestData.label) || `Asset ${assetId}`;
        const objectNumber = metadataMap.get('object number') || undefined;

        if (!cancelled) {
          setPreviewStats((current) => ({
            ...current,
            manifestLoadedMs: Math.max(0, Math.round(performance.now() - previewStartAtRef.current)),
          }));
          setPreviewStage('loading_tiles');
          setPreviewProgress(45);
          setManifest(response.data as Record<string, unknown>);
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
          setManifest(null);
          setPreviewStage('error');
          setPreviewProgress(100);
        }
        console.warn('Failed to load mirador manifest metadata', error);
      }
    };

    setManifest(null);
    setApplicationCandidate(null);
    loadManifestMeta();

    return () => {
      cancelled = true;
    };
  }, [manifestId]);

  const canApply = useMemo(() => Boolean(applicationCandidate && onAddToApplication), [applicationCandidate, onAddToApplication]);

  return (
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          minHeight: 0,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'row',
        }}
        aria-busy={previewStage !== 'ready'}
      >
        <div
          style={{
            position: 'relative',
            flex: 1,
            minWidth: 0,
            height: '100%',
            overflow: 'hidden',
          }}
        >
      <Space
        direction="vertical"
        size="small"
        style={{
          position: 'absolute',
          top: 12,
          right: 12,
          zIndex: 120,
          alignItems: 'flex-end',
        }}
      >
        {applicationCandidate ? <Tag color="blue">资源 #{applicationCandidate.assetId}</Tag> : null}
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
          加入申请车
        </Button>
      </Space>

      <div
        id="mirador-viewer"
        style={{
          width: '100%',
          height: '100%',
          minHeight: 0,
          position: 'relative',
          flex: 1,
          zIndex: 1,
        }}
      />

      {previewStage !== 'ready' ? (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 50,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(180deg, rgba(10,12,18,0.68), rgba(10,12,18,0.42))',
            backdropFilter: 'blur(3px)',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              width: 'min(460px, calc(100% - 40px))',
              padding: '18px 20px',
              borderRadius: 14,
              background: 'rgba(15, 18, 28, 0.84)',
              color: '#fff',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.35)',
            }}
          >
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Space align="center" size={12}>
                <Spin />
                <div style={{ fontWeight: 600 }}>
                  {statusLabel}
                </div>
              </Space>
              <Progress percent={previewProgress} status={previewStage === 'error' ? 'exception' : 'active'} showInfo />
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.72)', lineHeight: 1.6 }}>
                首次打开会先请求低清预览，再生成 IIIF info.json 和高清切片。大图和 TIFF 会更慢，等待几秒是正常的。
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>
                已等待 {previewElapsedSeconds} 秒
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.58)', lineHeight: 1.6 }}>
                {previewStats.manifestLoadedMs ? `manifest ${previewStats.manifestLoadedMs} ms` : 'manifest 等待中'}
                {' · '}
                {previewStats.firstTileRenderedMs ? `首个切片 ${previewStats.firstTileRenderedMs} ms` : '切片等待中'}
              </div>
            </Space>
          </div>
        </div>
      ) : null}
        </div>
        <MiradorAiPanel
          manifestId={manifestId}
          currentCandidate={applicationCandidate}
          viewerApiRef={viewerApiRef}
          viewerReady={previewStage === 'ready'}
        />
      </div>
  );
};

export default MiradorViewer;

