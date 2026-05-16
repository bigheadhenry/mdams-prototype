import React, { useMemo, useState } from 'react';
import { Image } from 'antd';
import { BlockOutlined } from '@ant-design/icons';
import type { ThreeDPreviewData } from '../types/assets';

type ThreeDTurntablePreviewProps = {
  title: string;
  previewData?: ThreeDPreviewData | null;
  fallbackUrl?: string | null;
  height?: number;
};

const ThreeDTurntablePreview: React.FC<ThreeDTurntablePreviewProps> = ({
  title,
  previewData,
  fallbackUrl,
  height = 160,
}) => {
  const frames = useMemo(
    () => (previewData?.frames || []).filter(Boolean),
    [previewData],
  );
  const [frameIndex, setFrameIndex] = useState(0);
  const imageUrl = frames[frameIndex] || previewData?.poster_url || fallbackUrl || null;

  return (
    <div
      onMouseMove={(event) => {
        if (!frames.length) return;
        const rect = event.currentTarget.getBoundingClientRect();
        const ratio = Math.min(0.999, Math.max(0, (event.clientX - rect.left) / rect.width));
        setFrameIndex(Math.floor(ratio * frames.length));
      }}
      onMouseLeave={() => setFrameIndex(0)}
      style={{
        height,
        background: '#f8fafc',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {imageUrl ? (
        <Image
          src={imageUrl}
          alt={title}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
          preview={false}
        />
      ) : (
        <BlockOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />
      )}
      {frames.length > 1 ? (
        <div
          style={{
            position: 'absolute',
            right: 8,
            bottom: 8,
            padding: '2px 6px',
            borderRadius: 4,
            background: 'rgba(15, 23, 42, 0.62)',
            color: '#fff',
            fontSize: 11,
          }}
        >
          {frameIndex + 1}/{frames.length}
        </div>
      ) : null}
    </div>
  );
};

export default ThreeDTurntablePreview;
