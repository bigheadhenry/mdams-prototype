/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useMemo, useState } from 'react';
import axios from 'axios';
import {
  Alert,
  Button,
  Card,
  Divider,
  Input,
  List,
  message,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd';
import {
  AimOutlined,
  ArrowDownOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  ArrowUpOutlined,
  CheckOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SearchOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
} from '@ant-design/icons';
import { OSDReferences } from 'mirador/dist/cjs/src/plugins/OSDReferences';
import {
  addWindow as addMiradorWindow,
  focusWindow as focusMiradorWindow,
  removeWindow as removeMiradorWindow,
  updateViewport as updateMiradorViewport,
  updateWorkspace as updateMiradorWorkspace,
} from 'mirador/dist/cjs/src/state/actions';
import type { MiradorAIPlan, MiradorSearchResult } from './types/assets';

interface ApplicationCandidate {
  assetId: number;
  sourceSystem?: string | null;
  sourceId?: string | null;
  title: string;
  manifestUrl: string;
  objectNumber?: string | null;
  sourceLabel?: string | null;
}

interface MiradorAiPanelProps {
  manifestId: string;
  currentCandidate: ApplicationCandidate | null;
  viewerApiRef: React.MutableRefObject<any>;
  viewerReady: boolean;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ActionLogEntry {
  id: string;
  level: 'info' | 'success' | 'warning' | 'error';
  title: string;
  detail?: string;
  timestamp: string;
}

type WorkspaceMode = 'mosaic' | 'elastic';

const AUTH_TOKEN_KEY = 'mdams.auth.token';
const VIEWPORT_EPSILON = 0.0001;

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content: '可以直接告诉我放大、缩小、平移、适配窗口，或者让我帮你找图并打开比较模式。',
  },
];

const getStateSlice = (state: any) => state?.mirador || state || {};
const getWorkspaceState = (store: any) => getStateSlice(store?.getState?.())?.workspace || {};

const getWindowIds = (store: any): string[] => {
  const workspace = getWorkspaceState(store);
  return Array.isArray(workspace.windowIds) ? workspace.windowIds : [];
};

const getFocusedWindowId = (store: any): string | null => {
  const workspace = getWorkspaceState(store);
  return typeof workspace.focusedWindowId === 'string' ? workspace.focusedWindowId : null;
};

const getCurrentWindowId = (store: any): string | null =>
  getFocusedWindowId(store) ||
  getWindowIds(store)[0] ||
  Object.keys(getStateSlice(store?.getState?.())?.windows || {})[0] ||
  null;

const getWorkspaceMode = (store: any): WorkspaceMode => {
  const workspace = getWorkspaceState(store);
  return workspace.type === 'mosaic' ? 'mosaic' : 'elastic';
};

const getCurrentViewport = (store: any) => {
  const slice = getStateSlice(store?.getState?.());
  const windowId = getCurrentWindowId(store);
  if (!windowId) return null;
  return slice?.viewers?.[windowId] || null;
};

const wait = (ms: number) =>
  new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });

const nearlyEqual = (a: number, b: number, epsilon = VIEWPORT_EPSILON) => Math.abs(a - b) <= epsilon;

const didViewportChange = (
  before: { x: number; y: number; zoom: number } | null,
  after: { x: number; y: number; zoom: number } | null,
) => {
  if (!before || !after) return false;
  return (
    !nearlyEqual(before.x, after.x) ||
    !nearlyEqual(before.y, after.y) ||
    !nearlyEqual(before.zoom, after.zoom)
  );
};

const getViewerViewportSnapshot = (windowId: string | null) => {
  if (!windowId) return null;
  const viewerRef = OSDReferences.get(windowId)?.current;
  const viewport = viewerRef?.viewport;
  if (!viewport?.getCenter || !viewport?.getZoom) return null;

  const center = viewport.getCenter(true);
  return {
    x: Number(center?.x ?? 0),
    y: Number(center?.y ?? 0),
    zoom: Number(viewport.getZoom(true) ?? 1),
  };
};

const getStoreViewportSnapshot = (store: any) => {
  const viewport = getCurrentViewport(store);
  if (!viewport) return null;
  return {
    x: Number(viewport.x ?? 0),
    y: Number(viewport.y ?? 0),
    zoom: Number(viewport.zoom ?? 1),
  };
};

const getViewportSnapshot = (store: any, windowId: string | null) =>
  getViewerViewportSnapshot(windowId) || getStoreViewportSnapshot(store);

const isViewportBoundaryAction = (action: MiradorAIPlan['action']) =>
  ['zoom_out', 'reset_view', 'fit_to_window', 'pan_left', 'pan_right', 'pan_up', 'pan_down'].includes(action);

const nativeViewportControlLabels: Partial<Record<MiradorAIPlan['action'], string[]>> = {
  zoom_in: ['Zoom in', '放大'],
  zoom_out: ['Zoom out', '缩小'],
  reset_view: ['Reset zoom', '重置缩放', '重置'],
  fit_to_window: ['Reset zoom', '重置缩放', '适配'],
};

const clickNativeViewportControl = (action: MiradorAIPlan['action']) => {
  const labels = nativeViewportControlLabels[action];
  const root = document.getElementById('mirador-viewer');
  if (!labels || !root) return false;

  const button = Array.from(root.querySelectorAll<HTMLButtonElement>('button')).find((item) => {
    const label = item.getAttribute('aria-label') || item.textContent || '';
    return labels.some((expected) => label.includes(expected));
  });
  if (!button || button.disabled) return false;

  button.click();
  return true;
};

const withAuthHeaders = () => {
  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : undefined;
};

const getActionLabel = (action: MiradorAIPlan['action']) => {
  switch (action) {
    case 'zoom_in':
      return '放大';
    case 'zoom_out':
      return '缩小';
    case 'pan_left':
      return '左移';
    case 'pan_right':
      return '右移';
    case 'pan_up':
      return '上移';
    case 'pan_down':
      return '下移';
    case 'reset_view':
      return '重置视图';
    case 'fit_to_window':
      return '适配窗口';
    case 'search_assets':
      return '搜索图像';
    case 'open_compare':
      return '打开比较';
    case 'switch_compare_mode':
      return '切换比较模式';
    case 'close_compare':
      return '关闭比较';
    default:
      return '未知动作';
  }
};

const getCompareModeLabel = (mode: WorkspaceMode) => (mode === 'mosaic' ? '比较模式' : '单图模式');
const getRequestedCompareModeLabel = (mode: MiradorAIPlan['compare_mode']) =>
  mode === 'side_by_side' ? '比较模式' : mode === 'single' ? '单图模式' : '未指定';
const getToolCallLabel = (nextPlan: MiradorAIPlan) => nextPlan.tool_call?.name || '兼容动作模式';

const LOG_LEVEL_LABELS: Record<ActionLogEntry['level'], string> = {
  info: '信息',
  success: '成功',
  warning: '警告',
  error: '错误',
};

const getLogLevelLabel = (level: ActionLogEntry['level']) => LOG_LEVEL_LABELS[level];

const nowLabel = () => new Date().toLocaleTimeString();

const MiradorAiPanel: React.FC<MiradorAiPanelProps> = ({ manifestId, currentCandidate, viewerApiRef, viewerReady }) => {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [logEntries, setLogEntries] = useState<ActionLogEntry[]>([]);
  const [plan, setPlan] = useState<MiradorAIPlan | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<MiradorSearchResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const currentInfo = useMemo(
    () => ({
      current_asset_id: currentCandidate?.assetId ?? null,
      current_manifest_url: manifestId,
      current_title: currentCandidate?.title ?? null,
      current_object_number: currentCandidate?.objectNumber ?? null,
      current_source_system: currentCandidate?.sourceSystem ?? null,
      current_source_id: currentCandidate?.sourceId ?? null,
      max_candidates: 5,
    }),
    [currentCandidate, manifestId],
  );

  const appendMessage = (role: ChatMessage['role'], content: string) => {
    setMessages((items) => [
      ...items,
      {
        id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        role,
        content,
      },
    ]);
  };

  const appendLog = (level: ActionLogEntry['level'], title: string, detail?: string) => {
    const entry: ActionLogEntry = {
      id: `${level}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      level,
      title,
      detail,
      timestamp: nowLabel(),
    };
    setLogEntries((items) => [entry, ...items].slice(0, 30));
    const logger = level === 'error' ? console.error : level === 'warning' ? console.warn : console.info;
    logger(`[MiradorAI] ${title}`, detail || '');
  };

  const waitFor = async (predicate: () => boolean, attempts = 10, intervalMs = 40) => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      if (predicate()) return true;
      await wait(intervalMs);
    }
    return predicate();
  };

  const dispatchMirador = (action: any) => {
    const api = viewerApiRef.current;
    if (!api?.store) {
      throw new Error('Mirador 预览器尚未就绪。');
    }
    api.store.dispatch(action);
  };

  const getMiradorAction = <T extends (...args: any[]) => any>(actionFromApi: T | undefined, fallback: T): T =>
    (actionFromApi || fallback) as T;

  const setWorkspaceMode = (mode: WorkspaceMode) => {
    const api = viewerApiRef.current;
    dispatchMirador(getMiradorAction(api?.actions?.updateWorkspace, updateMiradorWorkspace)({ type: mode }));
  };

  const ensureCompareMode = async (mode: WorkspaceMode, reason: string) => {
    setWorkspaceMode(mode);
    const updated = await waitFor(() => getWorkspaceMode(viewerApiRef.current?.store) === mode);
    if (!updated) {
      throw new Error(`切换到${getCompareModeLabel(mode)}失败。`);
    }

    appendLog('success', '比较模式已更新', `${getCompareModeLabel(mode)} - ${reason}`);
    setStatusMessage(`已切换到${getCompareModeLabel(mode)}`);
  };

  const applyViewportAction = async (action: MiradorAIPlan['action'], panPixels = 120, zoomFactor = 1.2) => {
    const api = viewerApiRef.current;
    const store = api?.store;
    const windowId = getCurrentWindowId(store);
    if (!store || !windowId) {
      throw new Error('Mirador 预览器尚未就绪。');
    }

    const viewerRef = OSDReferences.get(windowId)?.current;
    const viewerViewport = viewerRef?.viewport;
    const before = getViewportSnapshot(store, windowId);
    const storeViewport = getCurrentViewport(store);
    const next = {
      flip: storeViewport?.flip ?? false,
      rotation: storeViewport?.rotation ?? 0,
      x: storeViewport?.x ?? 0,
      y: storeViewport?.y ?? 0,
      zoom: storeViewport?.zoom ?? 1,
    };

    const panRatio = Math.max(panPixels / 600, 0.05);
    let handledByViewer = false;
    let handledByNativeControl = false;

    if (viewerViewport) {
      switch (action) {
        case 'zoom_in':
          if (viewerViewport.zoomBy) {
            viewerViewport.zoomBy(zoomFactor, undefined, true);
            viewerViewport.applyConstraints?.();
            handledByViewer = true;
          }
          break;
        case 'zoom_out':
          if (viewerViewport.zoomBy) {
            viewerViewport.zoomBy(1 / zoomFactor, undefined, true);
            viewerViewport.applyConstraints?.();
            handledByViewer = true;
          }
          break;
        case 'pan_left':
        case 'pan_right':
        case 'pan_up':
        case 'pan_down':
          if (viewerViewport.getCenter && viewerViewport.getBounds && viewerViewport.panTo) {
            const center = viewerViewport.getCenter(true);
            const bounds = viewerViewport.getBounds(true);
            const nextCenter = {
              x:
                action === 'pan_left'
                  ? center.x - bounds.width * panRatio
                  : action === 'pan_right'
                    ? center.x + bounds.width * panRatio
                    : center.x,
              y:
                action === 'pan_up'
                  ? center.y - bounds.height * panRatio
                  : action === 'pan_down'
                    ? center.y + bounds.height * panRatio
                    : center.y,
            };
            viewerViewport.panTo(nextCenter, true);
            viewerViewport.applyConstraints?.();
            handledByViewer = true;
          }
          break;
        case 'reset_view':
        case 'fit_to_window':
          if (viewerViewport.goHome) {
            viewerViewport.goHome(true);
            viewerViewport.applyConstraints?.();
            handledByViewer = true;
          }
          break;
        default:
          break;
      }
    }

    if (!handledByViewer) {
      handledByNativeControl = clickNativeViewportControl(action);
    }

    if (!handledByViewer && !handledByNativeControl) {
      switch (action) {
        case 'zoom_in':
          next.zoom = Math.max(0.01, next.zoom * zoomFactor);
          break;
        case 'zoom_out':
          next.zoom = Math.max(0.01, next.zoom / zoomFactor);
          break;
        case 'pan_left':
          next.x -= panPixels;
          break;
        case 'pan_right':
          next.x += panPixels;
          break;
        case 'pan_up':
          next.y -= panPixels;
          break;
        case 'pan_down':
          next.y += panPixels;
          break;
        case 'reset_view':
        case 'fit_to_window':
          next.x = 0;
          next.y = 0;
          next.zoom = 1;
          break;
        default:
          return;
      }

      dispatchMirador(getMiradorAction(api?.actions?.updateViewport, updateMiradorViewport)(windowId, next));
    }

    const updated = await waitFor(() => didViewportChange(before, getViewportSnapshot(store, windowId)));
    if (!updated) {
      if (isViewportBoundaryAction(action)) {
        appendLog('warning', '视图未发生明显变化', `${getActionLabel(action)}可能已到边界或当前已处于目标状态。`);
        setStatusMessage(`${getActionLabel(action)}已执行，当前视图可能已到边界或已适配。`);
        return;
      }
      throw new Error(`${getActionLabel(action)}没有真正生效。`);
    }
  };

  const openCompareTarget = async (target: MiradorSearchResult) => {
    const api = viewerApiRef.current;
    if (!api?.store) {
      throw new Error('Mirador 预览器尚未就绪。');
    }

    const response = await axios.get(target.manifest_url, {
      headers: withAuthHeaders(),
    });

    const beforeCount = getWindowIds(api.store).length;
    const windowId = `compare-${target.asset_id}-${Date.now()}`;
    dispatchMirador(
      getMiradorAction(api.actions?.addWindow, addMiradorWindow)({
        id: windowId,
        manifestId: target.manifest_url,
        manifest: response.data,
      }),
    );
    dispatchMirador(getMiradorAction(api.actions?.focusWindow, focusMiradorWindow)(windowId, true));

    const opened = await waitFor(() => getWindowIds(api.store).length === beforeCount + 1);
    if (!opened) {
      throw new Error('比较窗口没有成功打开。');
    }

    await ensureCompareMode('mosaic', `打开 ${target.title}（#${target.asset_id}）`);
    appendLog('success', '已打开比较目标', `${target.title}（#${target.asset_id}）`);
  };

  const toggleCompareMode = async () => {
    const store = viewerApiRef.current?.store;
    const currentMode = getWorkspaceMode(store);
    const windowCount = getWindowIds(store).length;

    if (currentMode === 'elastic') {
      if (windowCount < 2 && !selectedTarget) {
        appendLog('warning', '无法进入比较模式', '请先打开第二张图像，再进入比较模式。');
        setStatusMessage('请先打开一张比较图，再进入比较模式。');
        return;
      }
      await ensureCompareMode('mosaic', '手动开启');
      return;
    }

    await ensureCompareMode('elastic', '手动关闭');
  };

  const closeCompare = async () => {
    const api = viewerApiRef.current;
    const store = api?.store;
    if (!store) {
      throw new Error('Mirador 预览器尚未就绪。');
    }

    const windowIds = getWindowIds(store);
    if (windowIds.length <= 1) {
      await ensureCompareMode('elastic', '仅剩单窗口');
      appendLog('info', '跳过关闭比较', '当前只打开了一个窗口。');
      return;
    }

    const currentWindowId = getCurrentWindowId(store);
    const removeTarget = windowIds.find((id) => id !== currentWindowId) || windowIds[windowIds.length - 1];
    const beforeCount = windowIds.length;
    if (removeTarget) {
      dispatchMirador(getMiradorAction(api.actions?.removeWindow, removeMiradorWindow)(removeTarget));
      appendLog('success', '已关闭比较目标', removeTarget);
    }

    const closed = await waitFor(() => getWindowIds(store).length === beforeCount - 1);
    if (!closed) {
      throw new Error('比较窗口没有成功关闭。');
    }

    if (getWindowIds(store).length <= 1) {
      await ensureCompareMode('elastic', '关闭后恢复单图');
    }
  };

  const executePlan = async (nextPlan: MiradorAIPlan, target: MiradorSearchResult | null) => {
    try {
      setBusy(true);
      setErrorMessage(null);
      appendLog(
        'info',
        '开始执行',
        `${getActionLabel(nextPlan.action)}${nextPlan.requires_confirmation ? '（待确认）' : ''}`,
      );

      if (nextPlan.action === 'search_assets') {
        setSelectedTarget(target);
        appendLog('info', '等待选择候选图', target ? `${target.title}（#${target.asset_id}）` : '暂无候选目标');
        return;
      }

      if (nextPlan.action === 'open_compare') {
        if (!target) {
          throw new Error('还没有可用于打开比较的候选图。');
        }
        await openCompareTarget(target);
        return;
      }

      if (nextPlan.action === 'switch_compare_mode') {
        const desiredMode = nextPlan.compare_mode === 'single' ? 'elastic' : 'mosaic';
        await ensureCompareMode(
          desiredMode,
          nextPlan.compare_mode ? `显式切换为${getRequestedCompareModeLabel(nextPlan.compare_mode)}` : '切换',
        );
        return;
      }

      if (nextPlan.action === 'close_compare') {
        await closeCompare();
        return;
      }

      if (nextPlan.action === 'noop') {
        appendLog('warning', '忽略空动作', '本次计划没有需要执行的操作。');
        return;
      }

      await applyViewportAction(nextPlan.action, nextPlan.pan_pixels ?? 120, nextPlan.zoom_factor ?? 1.2);
      appendLog('success', '视图已更新', getActionLabel(nextPlan.action));
      setStatusMessage(`已执行${getActionLabel(nextPlan.action)}`);
    } catch (error) {
      const text = error instanceof Error ? error.message : '执行失败';
      setErrorMessage(text);
      appendLog('error', '执行失败', text);
      message.error(text);
    } finally {
      setBusy(false);
    }
  };

  const handleSubmit = async () => {
    const text = prompt.trim();
    if (!text) return;

    setPrompt('');
    appendMessage('user', text);
    appendLog('info', '收到用户指令', text);
    setBusy(true);
    setErrorMessage(null);
    setStatusMessage(null);

    try {
      const response = await axios.post(
        '/api/ai/mirador/interpret',
        {
          prompt: text,
          ...currentInfo,
        },
        {
          headers: withAuthHeaders(),
        },
      );

      const nextPlan = response.data as MiradorAIPlan;
      setPlan(nextPlan);
      appendMessage('assistant', nextPlan.assistant_message);
      appendLog(
        'info',
        'AI 生成计划',
        `${getActionLabel(nextPlan.action)} / ${getToolCallLabel(nextPlan)}${nextPlan.requires_confirmation ? ' / 需要确认' : ''}`,
      );

      const firstTarget = nextPlan.target_asset || nextPlan.search_results?.[0] || null;
      setSelectedTarget(firstTarget);
      if (firstTarget) {
        appendLog('info', '选中候选图', `${firstTarget.title}（#${firstTarget.asset_id}）`);
      }

      if (nextPlan.requires_confirmation) {
        setStatusMessage(`需要确认：${getActionLabel(nextPlan.action)}`);
        appendLog('warning', '等待确认', getActionLabel(nextPlan.action));
        return;
      }

      await executePlan(nextPlan, firstTarget);
    } catch (error) {
      const text = error instanceof Error ? error.message : 'AI 解析失败';
      setErrorMessage(text);
      appendMessage('assistant', `抱歉，这次没有成功：${text}`);
      appendLog('error', 'AI 解析失败', text);
      message.error(text);
    } finally {
      setBusy(false);
    }
  };

  const handleQuickAction = async (action: MiradorAIPlan['action']) => {
    const quickPlan: MiradorAIPlan = {
      action,
      assistant_message: getActionLabel(action),
      requires_confirmation: false,
    };
    setPlan(quickPlan);
    appendLog('info', '快捷操作', getActionLabel(action));
    await executePlan(quickPlan, selectedTarget);
  };

  const confirmPending = async () => {
    if (!plan) return;
    appendLog('success', '用户确认', getActionLabel(plan.action));
    await executePlan(plan, selectedTarget);
  };

  const compareMode = getWorkspaceMode(viewerApiRef.current?.store);
  const windowCount = getWindowIds(viewerApiRef.current?.store).length;
  const candidateList = plan?.search_results || [];

  return (
    <div
      data-testid="mirador-ai-panel"
      style={{
        width: 380,
        minWidth: 320,
        maxWidth: 420,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(180deg, rgba(17, 20, 28, 0.96), rgba(12, 15, 22, 0.98))',
        color: '#f5f7fb',
        borderLeft: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <div style={{ padding: 16, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
          <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
            <Typography.Text style={{ color: '#fff', fontSize: 16, fontWeight: 700 }}>AI 控制台</Typography.Text>
            <Tag color="blue">{currentCandidate ? `资源 #${currentCandidate.assetId}` : '未加载'}</Tag>
          </Space>
          <Space wrap>
            <Tag color={compareMode === 'mosaic' ? 'green' : 'default'}>{getCompareModeLabel(compareMode)}</Tag>
            <Tag color="purple">{windowCount} 个窗口</Tag>
          </Space>
          <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.68)', marginBottom: 0 }}>
            这里既支持自然语言指令，也支持直接点按按钮。视口动作现在会在执行后做一次校验，避免面板显示成功但画面没有变化。
          </Typography.Paragraph>
        </Space>
      </div>

      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto', flex: 1 }}>
        <Card size="small" style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}>
          <Space wrap>
            <Button data-testid="mirador-ai-zoom-in" icon={<ZoomInOutlined />} onClick={() => void handleQuickAction('zoom_in')} disabled={!viewerReady || busy}>
              放大
            </Button>
            <Button data-testid="mirador-ai-zoom-out" icon={<ZoomOutOutlined />} onClick={() => void handleQuickAction('zoom_out')} disabled={!viewerReady || busy}>
              缩小
            </Button>
            <Button data-testid="mirador-ai-pan-left" icon={<ArrowLeftOutlined />} onClick={() => void handleQuickAction('pan_left')} disabled={!viewerReady || busy}>
              左移
            </Button>
            <Button data-testid="mirador-ai-pan-right" icon={<ArrowRightOutlined />} onClick={() => void handleQuickAction('pan_right')} disabled={!viewerReady || busy}>
              右移
            </Button>
            <Button data-testid="mirador-ai-pan-up" icon={<ArrowUpOutlined />} onClick={() => void handleQuickAction('pan_up')} disabled={!viewerReady || busy}>
              上移
            </Button>
            <Button data-testid="mirador-ai-pan-down" icon={<ArrowDownOutlined />} onClick={() => void handleQuickAction('pan_down')} disabled={!viewerReady || busy}>
              下移
            </Button>
            <Button data-testid="mirador-ai-reset" icon={<ReloadOutlined />} onClick={() => void handleQuickAction('reset_view')} disabled={!viewerReady || busy}>
              重置
            </Button>
            <Button data-testid="mirador-ai-fit" icon={<AimOutlined />} onClick={() => void handleQuickAction('fit_to_window')} disabled={!viewerReady || busy}>
              适配
            </Button>
          </Space>
        </Card>

        <Card
          size="small"
          title={<Typography.Text style={{ color: '#fff' }}>比较模式</Typography.Text>}
          style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
          styles={{ body: { paddingTop: 12 } }}
        >
          <Space direction="vertical" size={10} style={{ width: '100%' }}>
            <Space wrap>
              <Button data-testid="mirador-ai-toggle-compare" type="primary" onClick={() => void toggleCompareMode()} icon={<CompareModeIcon />} disabled={!viewerReady || busy}>
                {compareMode === 'mosaic' ? '退出比较模式' : '进入比较模式'}
              </Button>
              <Button data-testid="mirador-ai-close-compare" danger onClick={() => void closeCompare()} icon={<CloseCircleOutlined />} disabled={!viewerReady || busy}>
                关闭比较
              </Button>
            </Space>
            <Typography.Text style={{ color: 'rgba(255,255,255,0.64)' }}>
              当前共有 {windowCount} 个窗口，工作区处于 {getCompareModeLabel(compareMode)}。
            </Typography.Text>
          </Space>
        </Card>

        <Card
          size="small"
          title={<Typography.Text style={{ color: '#fff' }}>自然语言控制</Typography.Text>}
          style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
          styles={{ body: { paddingTop: 12 } }}
        >
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Input.TextArea
              data-testid="mirador-ai-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="例如：放大一点，然后帮我找一张类似的图并打开比较"
              autoSize={{ minRows: 3, maxRows: 6 }}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault();
                  void handleSubmit();
                }
              }}
            />
            <Space>
              <Button data-testid="mirador-ai-send" type="primary" icon={<SearchOutlined />} onClick={() => void handleSubmit()} loading={busy} disabled={!viewerReady}>
                发送
              </Button>
              {plan?.requires_confirmation ? (
                <Button data-testid="mirador-ai-confirm" icon={<CheckOutlined />} onClick={() => void confirmPending()} loading={busy} disabled={!viewerReady}>
                  确认执行
                </Button>
              ) : null}
            </Space>
          </Space>
        </Card>

        {errorMessage ? <Alert data-testid="mirador-ai-error" type="error" showIcon message="执行失败" description={errorMessage} /> : null}
        {statusMessage ? <Alert data-testid="mirador-ai-status" type="info" showIcon message={statusMessage} /> : null}

        {plan ? (
          <Card
            data-testid="mirador-ai-plan"
            size="small"
            title={<Typography.Text style={{ color: '#fff' }}>当前计划</Typography.Text>}
            style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Tag color={plan.requires_confirmation ? 'orange' : 'green'}>{getActionLabel(plan.action)}</Tag>
              <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.8)', marginBottom: 0 }}>
                {plan.assistant_message}
              </Typography.Paragraph>
              {plan.tool_call ? (
                <Typography.Text style={{ color: 'rgba(255,255,255,0.56)' }}>
                  工具调用：{plan.tool_call.name}
                </Typography.Text>
              ) : null}
              {plan.search_query ? (
                <Typography.Text style={{ color: 'rgba(255,255,255,0.56)' }}>搜索关键词：{plan.search_query}</Typography.Text>
              ) : null}
              {plan.compare_mode ? (
                <Typography.Text style={{ color: 'rgba(255,255,255,0.56)' }}>
                  比较目标模式：{plan.compare_mode === 'side_by_side' ? '比较模式' : '单图模式'}
                </Typography.Text>
              ) : null}
            </Space>
          </Card>
        ) : null}

        {candidateList.length > 0 ? (
          <Card
            data-testid="mirador-ai-candidates"
            size="small"
            title={<Typography.Text style={{ color: '#fff' }}>候选图像</Typography.Text>}
            style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <List
              size="small"
              dataSource={candidateList}
              renderItem={(item) => (
                <List.Item
                  data-testid={`mirador-ai-candidate-${item.asset_id}`}
                  style={{
                    cursor: 'pointer',
                    padding: '8px 4px',
                    borderBottom: '1px solid rgba(255,255,255,0.06)',
                  }}
                  onClick={() => {
                    setSelectedTarget(item);
                    appendLog('info', '切换候选图', `${item.title}（#${item.asset_id}）`);
                  }}
                >
                  <Space direction="vertical" size={2} style={{ width: '100%' }}>
                    <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
                      <Typography.Text style={{ color: '#fff' }}>{item.title}</Typography.Text>
                      <Tag color={selectedTarget?.asset_id === item.asset_id ? 'blue' : 'default'}>#{item.asset_id}</Tag>
                    </Space>
                    <Typography.Text style={{ color: 'rgba(255,255,255,0.56)', fontSize: 12 }}>
                      {item.object_number || item.filename || `${item.source_system}/${item.source_id}`}
                    </Typography.Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        ) : null}

        {plan?.requires_confirmation ? (
          <Card
            data-testid="mirador-ai-confirmation"
            size="small"
            title={<Typography.Text style={{ color: '#fff' }}>需要确认</Typography.Text>}
            style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Typography.Text style={{ color: 'rgba(255,255,255,0.82)' }}>
                即将执行：{getActionLabel(plan.action)}
              </Typography.Text>
              {selectedTarget ? (
                <Typography.Text style={{ color: 'rgba(255,255,255,0.62)' }}>
                  比较目标：{selectedTarget.title}
                </Typography.Text>
              ) : null}
              <Space>
                <Button type="primary" onClick={() => void confirmPending()} loading={busy}>
                  确认
                </Button>
                <Button
                  onClick={() => {
                    setPlan(null);
                    setSelectedTarget(null);
                    setStatusMessage('已取消本次操作。');
                    appendLog('warning', '取消确认', '用户已取消本次操作。');
                  }}
                >
                  取消
                </Button>
              </Space>
            </Space>
          </Card>
        ) : null}

        {busy ? (
          <Card size="small" style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}>
            <Space>
              <Spin size="small" />
              <Typography.Text style={{ color: 'rgba(255,255,255,0.72)' }}>处理中...</Typography.Text>
            </Space>
          </Card>
        ) : null}

        <Card size="small" style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}>
          <Typography.Text style={{ color: '#fff' }}>对话记录</Typography.Text>
          <Divider style={{ margin: '12px 0', borderColor: 'rgba(255,255,255,0.08)' }} />
          <Space direction="vertical" size={10} style={{ width: '100%' }}>
            {messages.map((item) => (
              <div key={item.id} style={{ color: item.role === 'user' ? '#cbe2ff' : '#ffffff' }}>
                <Tag color={item.role === 'user' ? 'blue' : 'gold'} style={{ marginRight: 8 }}>
                  {item.role === 'user' ? '我' : 'AI'}
                </Tag>
                <span style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{item.content}</span>
              </div>
            ))}
          </Space>
        </Card>

        <Card size="small" style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}>
          <Typography.Text style={{ color: '#fff' }}>操作日志</Typography.Text>
          <Divider style={{ margin: '12px 0', borderColor: 'rgba(255,255,255,0.08)' }} />
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            {logEntries.length === 0 ? (
              <Typography.Text style={{ color: 'rgba(255,255,255,0.58)' }}>暂无日志</Typography.Text>
            ) : (
              logEntries.map((entry) => (
                <div key={entry.id} style={{ color: '#fff' }}>
                  <Space align="center" size={8} style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Space size={8} align="center">
                      <Tag
                        color={
                          entry.level === 'success'
                            ? 'green'
                            : entry.level === 'warning'
                              ? 'orange'
                              : entry.level === 'error'
                                ? 'red'
                                : 'blue'
                        }
                      >
                        {getLogLevelLabel(entry.level)}
                      </Tag>
                      <Typography.Text style={{ color: '#fff' }}>{entry.title}</Typography.Text>
                    </Space>
                    <Typography.Text style={{ color: 'rgba(255,255,255,0.46)', fontSize: 12 }}>{entry.timestamp}</Typography.Text>
                  </Space>
                  {entry.detail ? (
                    <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.66)', marginBottom: 0, marginTop: 4 }}>
                      {entry.detail}
                    </Typography.Paragraph>
                  ) : null}
                </div>
              ))
            )}
          </Space>
        </Card>
      </div>
    </div>
  );
};

const CompareModeIcon = () => <span style={{ fontWeight: 700 }}>对</span>;

export default MiradorAiPanel;
