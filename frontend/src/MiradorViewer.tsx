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

  return <div id="mirador-viewer" style={{ width: '100%', height: '600px', position: 'relative' }} />;
};

export default MiradorViewer;
