import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock ag-psd
vi.mock('ag-psd', () => ({
  readPsd: vi.fn(),
}));

// Mock utif
vi.mock('utif', () => ({
  default: {
    decode: vi.fn(),
  },
}));

import { checkFileLayers } from '../fileCheck';
import { readPsd } from 'ag-psd';
import UTIF from 'utif';

function createMockFile(name: string, size: number, type = 'application/octet-stream'): File {
  return new File([new ArrayBuffer(size)], name, { type });
}

beforeEach(() => {
  vi.clearAllMocks();
});

const asPsdResult = (value: unknown): ReturnType<typeof readPsd> =>
  value as ReturnType<typeof readPsd>;

const asTiffResult = (value: unknown): ReturnType<typeof UTIF.decode> =>
  value as ReturnType<typeof UTIF.decode>;

describe('checkFileLayers', () => {
  // ─── File Size Check ───
  describe('file size validation', () => {
    it('returns isLargeFile for files >1GB', async () => {
      const file = createMockFile('test.psd', 2 * 1024 * 1024 * 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({
        hasLayers: false,
        isLargeFile: true,
        message: '文件过大 (>1GB)，跳过图层检测。请确保上传前已合并图层。',
      });
    });

    it('does NOT flag files exactly at 1GB', async () => {
      const file = createMockFile('plain.txt', 1024 * 1024 * 1024);
      const result = await checkFileLayers(file);
      expect(result.isLargeFile).toBeUndefined();
    });

    it('does NOT flag files under 1GB', async () => {
      const file = createMockFile('plain.txt', 500 * 1024 * 1024);
      const result = await checkFileLayers(file);
      expect(result.isLargeFile).toBeUndefined();
    });
  });

  // ─── Non-target file types ───
  describe('non-PSD/TIFF files', () => {
    it('returns hasLayers: false for .txt files', async () => {
      const file = createMockFile('readme.txt', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false for .jpg files', async () => {
      const file = createMockFile('photo.jpg', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false for .png files', async () => {
      const file = createMockFile('image.png', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false for files without extension', async () => {
      const file = createMockFile('README', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });
  });

  // ─── PSD/PSB ───
  describe('PSD/PSB files', () => {
    it('returns hasLayers: true when psd has multiple layers (>1)', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [
          { name: 'Background' },
          { name: 'Layer 2' },
        ],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('design.psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({
        hasLayers: true,
        message: '检测到 2 个图层。建议合并图层后上传。',
      });
    });

    it('returns hasLayers: false when psd has only 1 layer', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [{ name: 'Background' }],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('design.psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false when psd has 0 layers (empty children)', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('design.psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false when psd children is undefined', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('design.psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('handles parse errors gracefully (hasLayers: false)', async () => {
      vi.mocked(readPsd).mockImplementation(() => {
        throw new Error('Corrupted PSD');
      });

      const file = createMockFile('corrupted.psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('processes .psb files same as .psd', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [{ name: 'Background' }, { name: 'Layer 1' }, { name: 'Layer 2' }],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('large.psb', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({
        hasLayers: true,
        message: '检测到 3 个图层。建议合并图层后上传。',
      });
    });
  });

  // ─── TIFF ───
  describe('TIFF files', () => {
    it('returns hasLayers: true for multi-page TIFF', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult([{ t37724: undefined }, { t37724: undefined }]));

      const file = createMockFile('multipage.tif', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({
        hasLayers: true,
        message: '检测到 TIFF 文件包含 2 个页面/图层。建议合并图层后上传。',
      });
    });

    it('returns hasLayers: true for single-page TIFF with Photoshop layers tag 37724', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult([{ t37724: new ArrayBuffer(10) }]));

      const file = createMockFile('photoshop.tiff', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({
        hasLayers: true,
        message: '检测到 TIFF 文件包含隐藏的 Photoshop 图层数据 (Tag 37724)。这可能会导致图像处理失败，建议合并图层。',
      });
    });

    it('returns hasLayers: false for single-page TIFF without layers', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult([{}]));

      const file = createMockFile('flat.tif', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('handles TIFF parse errors gracefully (hasLayers: false)', async () => {
      vi.mocked(UTIF.decode).mockImplementation(() => {
        throw new Error('BigTIFF or corrupted');
      });

      const file = createMockFile('big.tiff', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false when UTIF.decode returns null/undefined IFDs', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult(null));

      const file = createMockFile('empty.tif', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });

    it('returns hasLayers: false when UTIF.decode returns empty array', async () => {
      vi.mocked(UTIF.decode).mockReturnValue([]);

      const file = createMockFile('empty.tif', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
    });
  });

  // ─── Case Insensitivity ───
  describe('case insensitivity', () => {
    it('detects .PSD (uppercase) as PSD file', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [{ name: 'Background' }, { name: 'Layer 1' }],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('DESIGN.PSD', 1024);
      const result = await checkFileLayers(file);
      expect(result.hasLayers).toBe(true);
      expect(readPsd).toHaveBeenCalledOnce();
    });

    it('detects .Psd (mixed case) as PSD file', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('design.Psd', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
      expect(readPsd).toHaveBeenCalledOnce();
    });

    it('detects .TIF (uppercase) as TIFF file', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult([{}, {}]));

      const file = createMockFile('SCAN.TIF', 1024);
      const result = await checkFileLayers(file);
      expect(result.hasLayers).toBe(true);
      expect(UTIF.decode).toHaveBeenCalledOnce();
    });

    it('detects .TIFF (uppercase) as TIFF file', async () => {
      vi.mocked(UTIF.decode).mockReturnValue(asTiffResult([{ t37724: new ArrayBuffer(8) }]));

      const file = createMockFile('PHOTOSHOP.TIFF', 1024);
      const result = await checkFileLayers(file);
      expect(result.hasLayers).toBe(true);
      expect(UTIF.decode).toHaveBeenCalledOnce();
    });

    it('detects .PSB (uppercase) as PSB file', async () => {
      vi.mocked(readPsd).mockReturnValue(asPsdResult({
        children: [{ name: 'Background' }],
        width: 1920,
        height: 1080,
      }));

      const file = createMockFile('LARGE.PSB', 1024);
      const result = await checkFileLayers(file);
      expect(result).toEqual({ hasLayers: false });
      expect(readPsd).toHaveBeenCalledOnce();
    });
  });
});
