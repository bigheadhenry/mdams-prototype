import React, { useEffect } from 'react';
import mirador from 'mirador';

interface MiradorViewerProps {
  manifestId: string;
}

const MiradorViewer: React.FC<MiradorViewerProps> = ({ manifestId }) => {
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
    };

    mirador.viewer(config);
  }, [manifestId]);

  return <div id="mirador-viewer" style={{ width: '100%', height: '600px', position: 'relative' }} />;
};

export default MiradorViewer;
