"use client";

import { useState } from "react";

import type { Dictionary } from "@/lib/i18n";

type CandidateView = "ACTIONS" | "PROFILE" | "EVIDENCE";

export function CandidateWorkspaceDeck({
  dictionary,
  profile,
  evidence,
  actions,
}: Readonly<{
  dictionary: Dictionary;
  profile: React.ReactNode;
  evidence: React.ReactNode;
  actions: React.ReactNode;
}>) {
  const [view, setView] = useState<CandidateView>("ACTIONS");
  const tabs: readonly Readonly<{ key: CandidateView; label: string }>[] = [
    { key: "ACTIONS", label: dictionary.candidate.actionViewLabel },
    { key: "PROFILE", label: dictionary.candidate.profileViewLabel },
    { key: "EVIDENCE", label: dictionary.candidate.evidenceViewLabel },
  ];

  function activateTab(next: CandidateView, ownerDocument: Document) {
    setView(next);
    ownerDocument
      .getElementById(`candidate-${next.toLowerCase()}-tab`)
      ?.focus();
  }

  function handleTabKey(
    event: React.KeyboardEvent<HTMLButtonElement>,
    current: CandidateView,
  ) {
    const index = tabs.findIndex((tab) => tab.key === current);
    let nextIndex = index;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft")
      nextIndex = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = tabs.length - 1;
    else return;
    event.preventDefault();
    const next = tabs[nextIndex];
    if (next) activateTab(next.key, event.currentTarget.ownerDocument);
  }

  return (
    <section className="candidate-workspace-deck" data-view={view}>
      <div
        className="candidate-workspace-tabs"
        role="tablist"
        aria-label={dictionary.candidate.workspaceViewLabel}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            id={`candidate-${tab.key.toLowerCase()}-tab`}
            type="button"
            role="tab"
            aria-selected={view === tab.key}
            aria-controls={`candidate-${tab.key.toLowerCase()}-panel`}
            onClick={() => setView(tab.key)}
            onKeyDown={(event) => handleTabKey(event, tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab) => (
        <div
          key={tab.key}
          id={`candidate-${tab.key.toLowerCase()}-panel`}
          className="candidate-workspace-layer"
          role="tabpanel"
          aria-labelledby={`candidate-${tab.key.toLowerCase()}-tab`}
          hidden={view !== tab.key}
        >
          {tab.key === "ACTIONS"
            ? actions
            : tab.key === "PROFILE"
              ? profile
              : evidence}
        </div>
      ))}
    </section>
  );
}
