import exifr from 'exifr';

// Define the shape of the message we expect
interface WorkerMessage {
  file: File;
}

self.onmessage = async (e: MessageEvent<WorkerMessage>) => {
  const { file } = e.data;
  
  try {
    // Report progress (mock start)
    self.postMessage({ type: 'progress', step: 'starting', message: '正在读取文件...' });

    // 1. Read file as ArrayBuffer
    // Note: For very large files (>1GB), this might crash the browser tab.
    // In a production environment, use a streaming hasher (like hash-wasm) and read chunks.
    const arrayBuffer = await file.arrayBuffer();
    
    // 2. Extract Metadata (Exif/XMP)
    // We do this before hashing because exifr only needs the header, but here we pass the buffer
    self.postMessage({ type: 'progress', step: 'metadata', message: '正在提取元数据...' });
    let metadata = null;
    try {
      // Parse all available tags
      metadata = await exifr.parse(arrayBuffer, {
        tiff: true,
        xmp: true,
        icc: true,
        iptc: true,
        exif: true,
      });
    } catch (err) {
      console.warn('Metadata extraction failed', err);
      // Non-fatal
    }

    // 3. Calculate SHA256 Hash
    self.postMessage({ type: 'progress', step: 'hashing', message: '正在计算 SHA256...' });
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    // 4. Done
    self.postMessage({ 
      type: 'complete', 
      result: {
        hash: hashHex,
        metadata: metadata || {},
        fileSize: file.size,
        fileName: file.name,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    self.postMessage({ type: 'error', error: String(error) });
  }
};
