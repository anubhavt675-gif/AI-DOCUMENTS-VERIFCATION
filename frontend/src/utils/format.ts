import type { DocumentStatus } from '../types';

/**
 * Format bytes to human-readable string.
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Truncate a UUID to a short display form.
 */
export function shortId(uuid: string): string {
  return uuid.split('-')[0].toUpperCase();
}

/**
 * Map a DocumentStatus to a display label.
 */
export function statusLabel(status: DocumentStatus): string {
  const map: Record<DocumentStatus, string> = {
    uploaded: 'Uploaded',
    processing: 'Processing',
    verified: 'Verified',
    suspicious: 'Suspicious',
    failed: 'Failed',
  };
  return map[status] ?? status;
}

/**
 * Map MIME type to a friendly short name.
 */
export function mimeLabel(mime: string): string {
  const map: Record<string, string> = {
    'application/pdf': 'PDF',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/tiff': 'TIFF',
    'image/bmp': 'BMP',
  };
  return map[mime] ?? mime;
}
