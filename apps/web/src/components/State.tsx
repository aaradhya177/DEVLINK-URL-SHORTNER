export function LoadingState({ label = "Loading" }: { label?: string }) {
  return <div className="state state-loading">{label}</div>;
}

export function EmptyState({ message }: { message: string }) {
  return <div className="state">{message}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="state state-error">{message}</div>;
}
