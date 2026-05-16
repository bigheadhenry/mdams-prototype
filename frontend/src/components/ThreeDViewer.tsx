import React, { useEffect, useRef, useState } from 'react';
import { Alert, Button, Card, Descriptions, Space, Tag, Typography } from 'antd';
import { DownloadOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import axios from 'axios';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { ThreeDDetailResponse } from '../types/assets';

const { Text } = Typography;

const WEB_PREVIEW_FORMATS = ['.glb', '.gltf'];
const ARCHIVE_MODEL_FORMATS = ['.glb', '.gltf', '.obj', '.fbx', '.stl', '.usdz'];

const WEB_PREVIEW_LABELS: Record<string, string> = {
  ready: '已就绪',
  pending: '准备中',
  disabled: '未启用',
};

const getWebPreviewLabel = (value?: string | null) => {
  if (!value) return '-';
  return WEB_PREVIEW_LABELS[value] || value;
};

const getRendererLabel = (value?: string | null) => {
  if (!value || value === 'model-viewer') return '三维预览器';
  return value;
};

const getFilenameExtension = (filename?: string | null) => {
  if (!filename || !filename.includes('.')) return '';
  return `.${filename.split('.').pop()?.toLowerCase() || ''}`;
};

type ThreeDViewerProps = {
  viewer: ThreeDDetailResponse['viewer'] | null | undefined;
  title?: string;
  onOpenPreview?: (url: string) => void;
};

const ThreeDViewer: React.FC<ThreeDViewerProps> = ({ viewer, title, onOpenPreview }) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [modelSrc, setModelSrc] = useState<string | null>(null);
  const [modelLoadError, setModelLoadError] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const previewFile = viewer?.preview_file;
  const previewUrl = viewer?.preview_url || previewFile?.preview_url || previewFile?.download_url || null;
  const previewExtension = getFilenameExtension(previewFile?.actual_filename || previewFile?.filename);
  const isPreviewFormatSupported = !previewExtension || WEB_PREVIEW_FORMATS.includes(previewExtension);
  const canRenderPreview = Boolean(viewer?.enabled && previewUrl && isPreviewFormatSupported);

  useEffect(() => {
    if (!canRenderPreview) {
      setModelSrc(null);
      setModelLoadError(null);
      return undefined;
    }

    let cancelled = false;
    let objectUrl: string | null = null;
    setModelSrc(null);
    setModelLoadError(null);

    const loadModel = async () => {
      try {
        if (!previewUrl.startsWith('/api/')) {
          setModelSrc(previewUrl);
          return;
        }

        const res = await axios.get<Blob>(previewUrl, { responseType: 'blob' });
        if (cancelled) return;
        objectUrl = URL.createObjectURL(res.data);
        setModelSrc(objectUrl);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setModelLoadError('三维模型文件加载失败，请确认当前用户有三维查看权限。');
        }
      }
    };

    void loadModel();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [canRenderPreview, previewUrl]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!modelSrc || !mount) {
      return undefined;
    }

    let disposed = false;
    let animationFrame = 0;
    setRenderError(null);

    const width = mount.clientWidth || 720;
    const height = mount.clientHeight || 480;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeef2f7);

    const camera = new THREE.PerspectiveCamera(35, width / height, 0.01, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    mount.replaceChildren(renderer.domElement);

    const ambient = new THREE.HemisphereLight(0xffffff, 0x445566, 2.0);
    scene.add(ambient);
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
    keyLight.position.set(4, 6, 5);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xffffff, 1.2);
    fillLight.position.set(-4, 2, -3);
    scene.add(fillLight);

    const controlsTarget = new THREE.Vector3();
    const loader = new GLTFLoader();
    let root: THREE.Object3D | null = null;

    const frameModel = (object: THREE.Object3D) => {
      const box = new THREE.Box3().setFromObject(object);
      if (box.isEmpty()) {
        camera.position.set(2, 1.5, 3);
        camera.lookAt(0, 0, 0);
        return;
      }

      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      object.position.sub(center);
      controlsTarget.set(0, 0, 0);

      const maxDim = Math.max(size.x, size.y, size.z) || 1;
      const distance = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
      camera.near = Math.max(distance / 100, 0.01);
      camera.far = distance * 100;
      camera.position.set(distance * 0.9, distance * 0.65, distance * 1.35);
      camera.lookAt(controlsTarget);
      camera.updateProjectionMatrix();
    };

    loader.load(
      modelSrc,
      (gltf) => {
        if (disposed) return;
        root = gltf.scene;
        root.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.frustumCulled = false;
            const materials = Array.isArray(child.material) ? child.material : [child.material];
            materials.forEach((material) => {
              material.side = THREE.DoubleSide;
              material.needsUpdate = true;
            });
          }
        });
        scene.add(root);
        frameModel(root);

        const animate = () => {
          if (disposed) return;
          if (root) {
            root.rotation.y += 0.006;
          }
          renderer.render(scene, camera);
          animationFrame = window.requestAnimationFrame(animate);
        };
        animate();
      },
      undefined,
      (error) => {
        console.error(error);
        if (!disposed) {
          setRenderError('三维模型解析或渲染失败。');
        }
      },
    );

    const resizeObserver = new ResizeObserver(([entry]) => {
      const nextWidth = Math.max(1, entry.contentRect.width);
      const nextHeight = Math.max(1, entry.contentRect.height);
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    });
    resizeObserver.observe(mount);

    return () => {
      disposed = true;
      window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
      renderer.dispose();
      mount.replaceChildren();
    };
  }, [modelSrc]);

  if (!viewer) {
    return null;
  }

  const canOpen = Boolean(viewer.enabled && previewUrl);

  return (
    <Card
      size="small"
      title="Web 预览"
      extra={
        <Space wrap>
          <Tag color={viewer.enabled ? 'green' : 'default'}>
            {viewer.enabled ? getWebPreviewLabel('ready') : getWebPreviewLabel('disabled')}
          </Tag>
          <Tag color="blue">{getRendererLabel(viewer.renderer)}</Tag>
        </Space>
      }
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="3D 格式支持"
        description={
          <Space direction="vertical" size={0}>
            <Text>可直接在线预览：{WEB_PREVIEW_FORMATS.join('、')}。</Text>
            <Text type="secondary">
              可上传保存：{ARCHIVE_MODEL_FORMATS.join('、')}。其中 OBJ、FBX、STL、USDZ 当前作为归档/下载文件保存，暂不直接在线预览；glTF 需要同时保留 .bin 和贴图等依赖文件。
            </Text>
          </Space>
        }
      />
      {viewer.enabled && previewUrl && !isPreviewFormatSupported ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="当前预览文件格式暂不支持在线渲染"
          description={`已保存文件 ${previewFile?.filename || previewExtension || ''}，可以下载或打包导出；如需浏览器直接预览，请上传 GLB，或上传包含完整依赖文件的 glTF。`}
        />
      ) : null}
      {canRenderPreview ? (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div style={{ borderRadius: 12, overflow: 'hidden', background: '#eef2f7', minHeight: 480 }}>
            {modelLoadError ? (
              <Alert type="error" showIcon message={modelLoadError} style={{ margin: 16 }} />
            ) : renderError ? (
              <Alert type="error" showIcon message={renderError} style={{ margin: 16 }} />
            ) : modelSrc ? (
              <div
                ref={mountRef}
                role="img"
                aria-label={title || previewFile?.filename || '三维模型'}
                style={{ width: '100%', height: 480, background: '#eef2f7' }}
              />
            ) : (
              <div style={{ height: 480, display: 'grid', placeItems: 'center', color: '#fff' }}>
                正在加载三维模型...
              </div>
            )}
          </div>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="预览文件">{previewFile?.filename || '-'}</Descriptions.Item>
            <Descriptions.Item label="文件角色">{previewFile?.role_label || previewFile?.role || '-'}</Descriptions.Item>
            <Descriptions.Item label="预览地址">
              {previewUrl ? <Text copyable>{previewUrl}</Text> : '-'}
            </Descriptions.Item>
          </Descriptions>
          <Space wrap>
            {previewUrl ? (
              <Button icon={<EyeOutlined />} onClick={() => onOpenPreview ? onOpenPreview(previewUrl) : window.open(previewUrl, '_blank', 'noopener,noreferrer')}>
                打开预览文件
              </Button>
            ) : null}
            {previewFile?.download_url ? (
              <Button
                icon={<DownloadOutlined />}
                onClick={() => {
                  window.location.href = previewFile.download_url || '';
                }}
              >
                下载预览文件
              </Button>
            ) : null}
            {previewUrl ? (
              <Button icon={<LinkOutlined />} onClick={() => window.open(previewUrl, '_blank', 'noopener,noreferrer')}>
                新标签页打开
              </Button>
            ) : null}
          </Space>
        </Space>
      ) : (
        <Alert
          type="info"
          showIcon
          message={viewer.reason || '当前资源没有可用的 Web 预览。'}
          description={
            previewFile ? (
              <Space direction="vertical" size={0}>
                <Text>候选文件：{previewFile.filename}</Text>
                <Text type="secondary">角色：{previewFile.role_label || previewFile.role}</Text>
              </Space>
            ) : (
              '没有可用于预览的模型文件。'
            )
          }
        />
      )}
      {!canOpen && viewer.preview_file ? (
        <Alert
          style={{ marginTop: 16 }}
          type="warning"
          showIcon
          message="仅支持查看，不支持当前版本直接展示"
          description="该对象已保存对应模型文件，但当前版本未标记为 Web 展示。你仍然可以下载文件或切换到可展示版本。"
        />
      ) : null}
    </Card>
  );
};

export default ThreeDViewer;
