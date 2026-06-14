export function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`badge ${active ? "badge-active" : "badge-muted"}`}>
      {active ? "Active" : "Inactive"}
    </span>
  );
}
