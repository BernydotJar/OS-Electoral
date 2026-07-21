"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("campaignos_frontend_render_failed", error.digest ?? "unknown");
  }, [error]);
  return (
    <main className="state-panel">
      <p className="eyebrow">FAIL CLOSED</p>
      <h1>CampaignOS could not render this context</h1>
      <p>No partial tenant or campaign data was displayed.</p>
      <button type="button" onClick={reset}>
        Retry
      </button>
    </main>
  );
}
