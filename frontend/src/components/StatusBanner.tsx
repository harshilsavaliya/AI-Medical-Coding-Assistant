interface StatusBannerProps {
  kind: "idle" | "loading" | "success" | "error";
  message?: string;
}

export function StatusBanner({ kind, message }: StatusBannerProps) {
  if (kind === "idle" || !message) {
    return null;
  }

  return <div className={`status-banner status-banner--${kind}`}>{message}</div>;
}
