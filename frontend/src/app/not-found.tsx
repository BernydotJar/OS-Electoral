import Link from "next/link";

export default function NotFound() {
  return (
    <main className="state-panel">
      <p className="eyebrow">404</p>
      <h1>CampaignOS route not found</h1>
      <p>The requested locale or module is not available.</p>
      <Link href="/es">Return to CampaignOS</Link>
    </main>
  );
}
