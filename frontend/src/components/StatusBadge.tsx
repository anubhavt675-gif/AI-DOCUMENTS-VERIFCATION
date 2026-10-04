import type { DocumentStatus } from '../types';

interface StatusBadgeProps {
  status: DocumentStatus;
}

const STATUS_CONFIG: Record<
  DocumentStatus,
  { label: string; className: string }
> = {
  uploaded:   { label: 'Uploaded',   className: 'badge badge-uploaded' },
  processing: { label: 'Processing', className: 'badge badge-processing' },
  verified:   { label: 'Verified',   className: 'badge badge-verified' },
  suspicious: { label: 'Suspicious', className: 'badge badge-suspicious' },
  failed:     { label: 'Failed',     className: 'badge badge-failed' },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, className: 'badge' };
  return <span className={cfg.className}>{cfg.label}</span>;
}

interface ProcessingBadgeProps {
  status: string | null | undefined;
}

export function ProcessingBadge({ status }: ProcessingBadgeProps) {
  const s = (status || 'pending').toLowerCase();
  let className = 'badge badge-uploaded';
  let label = 'Pending';

  if (s === 'completed') {
    className = 'badge badge-verified';
    label = 'Completed';
  } else if (s === 'processing') {
    className = 'badge badge-processing';
    label = 'Processing...';
  } else if (s === 'failed') {
    className = 'badge badge-failed';
    label = 'Failed';
  }

  return <span className={className}>{label}</span>;
}

interface ReadinessBadgeProps {
  processingStatus: string | null | undefined;
}

export function ReadinessBadge({ processingStatus }: ReadinessBadgeProps) {
  const s = (processingStatus || 'pending').toLowerCase();
  if (s === 'completed') {
    return <span className="badge badge-readiness-ready">Ready for Phase 3</span>;
  }
  if (s === 'failed') {
    return <span className="badge badge-readiness-failed">Preprocessing Failed</span>;
  }
  return <span className="badge badge-readiness-pending">Pending Preprocessing</span>;
}
