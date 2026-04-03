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
import type { MiradorAIPlan, MiradorSearchResult } from './types/assets';

interface ApplicationCandidate {
  assetId: number;
  resourceId: string;
  title: string;
  manifestUrl: string;
  objectNumber?: string | null;
  sourceLabel?: string | null;
}

interface MiradorAiPanelProps {
  manifestId: string;
  currentCandidate: ApplicationCandidate | null;
  viewerApiRef: React.MutableRefObject<any>;
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

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content: '你可以直接告诉我：放大、缩小、平移，或者帮你找图并打开对比。',
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
      return '打开对比';
    case 'switch_compare_mode':
      return '切换比较模式';
    case 'close_compare':
      return '关闭对比';
    default:
      return '未知动作';
  }
};

const getCompareModeLabel = (mode: WorkspaceMode) => (mode === 'mosaic' ? '比较模式' : '单图模式');

const nowLabel = () => new Date().toLocaleTimeString();

const MiradorAiPanel: React.FC<MiradorAiPanelProps> = ({ manifestId, currentCandidate, viewerApiRef }) => {
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
      current_resource_id: currentCandidate?.resourceId ?? null,
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

  const dispatchMirador = (action: any) => {
    const api = viewerApiRef.current;
    if (!api?.store || !api?.actions) {
      throw new Error('Mirador 视图尚未就绪');
    }
    api.store.dispatch(action);
  };

  const setWorkspaceMode = (mode: WorkspaceMode) => {
    const api = viewerApiRef.current;
    if (!api?.actions) {
      throw new Error('Mirador 视图尚未就绪');
    }
    dispatchMirador(api.actions.updateWorkspace({ type: mode }));
  };

  const ensureCompareMode = (mode: WorkspaceMode, reason: string) => {
    setWorkspaceMode(mode);
    appendLog('success', '切换比较状态', `${getCompareModeLabel(mode)} - ${reason}`);
    setStatusMessage(`已切换到 ${getCompareModeLabel(mode)}。`);
  };

  const applyViewportAction = (action: MiradorAIPlan['action'], panPixels = 120, zoomFactor = 1.2) => {
    const api = viewerApiRef.current;
    const store = api?.store;
    const windowId = getCurrentWindowId(store);
    if (!api?.actions || !store || !windowId) {
      throw new Error('Mirador 视图尚未就绪');
    }

    const viewport = getCurrentViewport(store);
    const next = {
      flip: viewport?.flip ?? false,
      rotation: viewport?.rotation ?? 0,
      x: viewport?.x ?? 0,
      y: viewport?.y ?? 0,
      zoom: viewport?.zoom ?? 1,
    };

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
      case 'fit_to_window': {
        const viewerRef = OSDReferences.get(windowId)?.current;
        if (viewerRef?.viewport?.goHome) {
          viewerRef.viewport.goHome(true);
          return;
        }
        next.x = 0;
        next.y = 0;
        next.zoom = 1;
        break;
      }
      default:
        return;
    }

    dispatchMirador(api.actions.updateViewport(windowId, next));
  };

  const openCompareTarget = async (target: MiradorSearchResult) => {
    const api = viewerApiRef.current;
    if (!api?.store || !api?.actions) {
      throw new Error('Mirador 视图尚未就绪');
    }

    const response = await axios.get(target.manifest_url, {
      headers: withAuthHeaders(),
    });

    const windowId = `compare-${target.asset_id}-${Date.now()}`;
    dispatchMirador(
      api.actions.addWindow({
        id: windowId,
        manifestId: target.manifest_url,
        manifest: response.data,
      }),
    );
    dispatchMirador(api.actions.focusWindow(windowId, true));
    ensureCompareMode('mosaic', `opened ${target.title} (#${target.asset_id})`);
    appendLog('success', '打开对比图', `${target.title} (#${target.asset_id})`);
  };

  const toggleCompareMode = () => {
    const store = viewerApiRef.current?.store;
    const currentMode = getWorkspaceMode(store);
    const windowCount = getWindowIds(store).length;

    if (currentMode === 'elastic') {
      if (windowCount < 2 && !selectedTarget) {
        appendLog('warning', '切换比较模式失败', '当前只有一个窗口，先打开一张对比图');
        setStatusMessage('请先打开一张对比图，再进入比较模式。');
        return;
      }
      ensureCompareMode('mosaic', 'toggle on');
      return;
    }

    ensureCompareMode('elastic', 'toggle off');
  };

  const closeCompare = () => {
    const api = viewerApiRef.current;
    const store = api?.store;
    if (!api?.actions || !store) {
      throw new Error('Mirador 视图尚未就绪');
    }

    const windowIds = getWindowIds(store);
    if (windowIds.length <= 1) {
      ensureCompareMode('elastic', 'single window remains');
      appendLog('info', '关闭对比跳过', '当前只剩一个窗口');
      return;
    }

    const currentWindowId = getCurrentWindowId(store);
    const removeTarget = windowIds.find((id) => id !== currentWindowId) || windowIds[windowIds.length - 1];
    if (removeTarget) {
      dispatchMirador(api.actions.removeWindow(removeTarget));
      appendLog('success', '关闭对比图', removeTarget);
    }

    if (getWindowIds(store).length <= 1) {
      ensureCompareMode('elastic', 'after close');
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
        appendLog('info', '等待选择候选图', target ? `${target.title} (#${target.asset_id})` : 'no target');
        return;
      }

      if (nextPlan.action === 'open_compare') {
        if (!target) {
          throw new Error('还没有可打开的候选图。');
        }
        await openCompareTarget(target);
        return;
      }

      if (nextPlan.action === 'switch_compare_mode') {
        const desiredMode = nextPlan.compare_mode === 'single' ? 'elastic' : 'mosaic';
        ensureCompareMode(desiredMode, nextPlan.compare_mode ? `explicit ${nextPlan.compare_mode}` : 'toggle');
        return;
      }

      if (nextPlan.action === 'close_compare') {
        closeCompare();
        return;
      }

      if (nextPlan.action === 'noop') {
        appendLog('warning', '忽略空动作', 'noop');
        return;
      }

      applyViewportAction(nextPlan.action, nextPlan.pan_pixels ?? 120, nextPlan.zoom_factor ?? 1.2);
      appendLog('success', '视图已更新', getActionLabel(nextPlan.action));
      setStatusMessage(`已执行 ${getActionLabel(nextPlan.action)}。`);
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
      appendLog('info', 'AI 生成计划', `${getActionLabel(nextPlan.action)}${nextPlan.requires_confirmation ? ' / 需要确认' : ''}`);

      const firstTarget = nextPlan.target_asset || nextPlan.search_results?.[0] || null;
      setSelectedTarget(firstTarget);
      if (firstTarget) {
        appendLog('info', '选中候选图', `${firstTarget.title} (#${firstTarget.asset_id})`);
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
      appendMessage('assistant', `抱歉，${text}`);
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
            <Tag color="blue">{currentCandidate ? `Asset #${currentCandidate.assetId}` : '未加载'}</Tag>
          </Space>
          <Space wrap>
            <Tag color={compareMode === 'mosaic' ? 'green' : 'default'}>{getCompareModeLabel(compareMode)}</Tag>
            <Tag color="purple">{windowCount} 窗口</Tag>
          </Space>
          <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.68)', marginBottom: 0 }}>
            你可以直接告诉我如何操作当前图像，或者让我帮你找图、打开对比、切换比较模式。
          </Typography.Paragraph>
        </Space>
      </div>

      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto', flex: 1 }}>
        <Card size="small" style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)' }}>
          <Space wrap>
            <Button icon={<ZoomInOutlined />} onClick={() => handleQuickAction('zoom_in')}>
              放大
            </Button>
            <Button icon={<ZoomOutOutlined />} onClick={() => handleQuickAction('zoom_out')}>
              缩小
            </Button>
            <Button icon={<ArrowLeftOutlined />} onClick={() => handleQuickAction('pan_left')}>
              左移
            </Button>
            <Button icon={<ArrowRightOutlined />} onClick={() => handleQuickAction('pan_right')}>
              右移
            </Button>
            <Button icon={<ArrowUpOutlined />} onClick={() => handleQuickAction('pan_up')}>
              上移
            </Button>
            <Button icon={<ArrowDownOutlined />} onClick={() => handleQuickAction('pan_down')}>
              下移
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => handleQuickAction('reset_view')}>
              重置
            </Button>
            <Button icon={<AimOutlined />} onClick={() => handleQuickAction('fit_to_window')}>
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
              <Button type="primary" onClick={() => toggleCompareMode()} icon={<CompareModeIcon />}>
                {compareMode === 'mosaic' ? '退出比较模式' : '进入比较模式'}
              </Button>
              <Button danger onClick={() => closeCompare()} icon={<CloseCircleOutlined />}>
                关闭对比
              </Button>
            </Space>
            <Typography.Text style={{ color: 'rgba(255,255,255,0.64)' }}>
              当前窗口数：{windowCount}，模式为 {getCompareModeLabel(compareMode)}。
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
              placeholder="例如：放大一点，再帮我找一张类似的图打开对比"
              autoSize={{ minRows: 3, maxRows: 6 }}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault();
                  void handleSubmit();
                }
              }}
            />
            <Space>
              <Button data-testid="mirador-ai-send" type="primary" icon={<SearchOutlined />} onClick={() => void handleSubmit()} loading={busy}>
                发送
              </Button>
              {plan?.requires_confirmation ? (
                <Button data-testid="mirador-ai-confirm" icon={<CheckOutlined />} onClick={() => void confirmPending()} loading={busy}>
                  确认执行
                </Button>
              ) : null}
            </Space>
          </Space>
        </Card>

        {errorMessage ? <Alert type="error" showIcon message="执行失败" description={errorMessage} /> : null}
        {statusMessage ? <Alert type="info" showIcon message={statusMessage} /> : null}

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
                    appendLog('info', '切换候选图', `${item.title} (#${item.asset_id})`);
                  }}
                >
                  <Space direction="vertical" size={2} style={{ width: '100%' }}>
                    <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
                      <Typography.Text style={{ color: '#fff' }}>{item.title}</Typography.Text>
                      <Tag color={selectedTarget?.asset_id === item.asset_id ? 'blue' : 'default'}>#{item.asset_id}</Tag>
                    </Space>
                    <Typography.Text style={{ color: 'rgba(255,255,255,0.56)', fontSize: 12 }}>
                      {item.object_number || item.filename || item.resource_id}
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
                  对比目标：{selectedTarget.title}
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
                    appendLog('warning', '取消确认', 'user cancelled');
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
                        {entry.level}
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

const CompareModeIcon = () => <span style={{ fontWeight: 700 }}>⇄</span>;

export default MiradorAiPanel;
