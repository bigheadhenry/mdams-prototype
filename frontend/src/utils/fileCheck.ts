import { readPsd } from 'ag-psd';

export interface LayerCheckResult {
  hasLayers: boolean;
  message?: string;
  isLargeFile?: boolean; // If true, we skipped check due to size
}

const MAX_CHECK_SIZE = 1 * 1024 * 1024 * 1024; // 1GB limit for frontend check

export async function checkFileLayers(file: File): Promise<LayerCheckResult> {
  const name = file.name.toLowerCase();
  
  // 1. Check file size
  if (file.size > MAX_CHECK_SIZE) {
    return {
      hasLayers: false,
      isLargeFile: true,
      message: '文件过大 (>1GB)，跳过图层检测。请确保上传前已合并图层。'
    };
  }

  // 2. Check PSD/PSB
  if (name.endsWith('.psd') || name.endsWith('.psb')) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const psd = readPsd(arrayBuffer, {
        skipLayerImageData: true,
        skipCompositeImageData: true,
        skipThumbnail: true,
      });

      // Logic: If children exists and length > 0, it might have layers.
      // But standard flattened PSDs might still have 1 'Background' layer.
      const layers = psd.children || [];
      
      // If there are multiple layers, or 1 layer that isn't just "Background"
      // Note: This is a heuristic.
      if (layers.length > 1) {
        return {
          hasLayers: true,
          message: `检测到 ${layers.length} 个图层。建议合并图层后上传。`
        };
      }
      
      return { hasLayers: false };
    } catch (e) {
      console.warn('PSD Parse error:', e);
      // If parse fails, we assume it's fine or let backend handle it
      return { hasLayers: false };
    }
  }

  // 3. Check TIFF (Not implemented in frontend due to complexity)
  if (name.endsWith('.tif') || name.endsWith('.tiff')) {
    // Ideally we'd use UTIF.js here, but for now we skip
    return { hasLayers: false };
  }

  return { hasLayers: false };
}
