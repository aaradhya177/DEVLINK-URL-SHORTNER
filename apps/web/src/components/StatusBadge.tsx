interface StatusBadgeProps {
  active: boolean;
  flaggedReason: string | null;
  expiresAt: string | null;
}

export function StatusBadge({
  active,
  flaggedReason,
  expiresAt,
}: StatusBadgeProps) {
  const status = getStatus(active, flaggedReason, expiresAt);
  return (
    <span className={`badge ${status.className}`} title={status.title}>
      {status.label}
    </span>
  );
}

function getStatus(
  active: boolean,
  flaggedReason: string | null,
  expiresAt: string | null,
): { label: string; className: string; title: string | undefined } {
  if (flaggedReason) {
    return {
      label: "Flagged",
      className: "badge-danger",
      title: flaggedReason,
    };
  }
  if (expiresAt && new Date(expiresAt).getTime() <= Date.now()) {
    return {
      label: "Expired",
      className: "badge-warning",
      title: undefined,
    };
  }
  if (!active) {
    return {
      label: "Inactive",
      className: "badge-muted",
      title: undefined,
    };
  }
  return {
    label: "Active",
    className: "badge-active",
    title: undefined,
  };
}
