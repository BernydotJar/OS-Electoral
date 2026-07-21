export default function Loading() {
  return (
    <main className="state-panel" aria-busy="true">
      <p className="eyebrow">CAMPAIGNOS</p>
      <h1>Loading verified context…</h1>
      <div className="loading-bar" aria-hidden="true">
        <span />
      </div>
    </main>
  );
}
