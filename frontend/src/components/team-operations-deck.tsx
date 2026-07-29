"use client";

import { useState } from "react";

import type { Dictionary } from "@/lib/i18n";

type DeckView = "BOARD" | "CREATE";

export function TeamOperationsDeck({
  dictionary,
  hasWorkItems,
  creator,
  board,
}: Readonly<{
  dictionary: Dictionary;
  hasWorkItems: boolean;
  creator: React.ReactNode;
  board: React.ReactNode;
}>) {
  const [view, setView] = useState<DeckView>(hasWorkItems ? "BOARD" : "CREATE");
  const views: readonly DeckView[] = ["BOARD", "CREATE"];

  function activateTab(next: DeckView, ownerDocument: Document) {
    setView(next);
    ownerDocument
      .getElementById(next === "BOARD" ? "team-board-tab" : "team-create-tab")
      ?.focus();
  }

  function handleTabKey(
    event: React.KeyboardEvent<HTMLButtonElement>,
    current: DeckView,
  ) {
    const index = views.indexOf(current);
    let nextIndex = index;
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      nextIndex = index === 0 ? 1 : 0;
    } else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = views.length - 1;
    else return;
    event.preventDefault();
    const next = views[nextIndex];
    if (next) activateTab(next, event.currentTarget.ownerDocument);
  }

  return (
    <section className="team-operations-deck" data-view={view}>
      <div className="team-operations-deck-heading">
        <div>
          <p className="eyebrow">
            {dictionary.teamWorkspace.operationsEyebrow}
          </p>
          <h3>{dictionary.teamWorkspace.operationsTitle}</h3>
          <p>{dictionary.teamWorkspace.operationsBody}</p>
        </div>
        <span className="team-command-scope">
          {dictionary.teamWorkspace.commandViewLabel}
        </span>
      </div>

      <div
        className="team-operations-deck-tabs"
        role="tablist"
        aria-label={dictionary.teamWorkspace.operationsViewLabel}
      >
        <button
          id="team-board-tab"
          type="button"
          role="tab"
          aria-selected={view === "BOARD"}
          aria-controls="team-board-panel"
          onClick={() => setView("BOARD")}
          onKeyDown={(event) => handleTabKey(event, "BOARD")}
        >
          {dictionary.teamWorkspace.boardViewAction}
        </button>
        <button
          id="team-create-tab"
          type="button"
          role="tab"
          aria-selected={view === "CREATE"}
          aria-controls="team-create-panel"
          onClick={() => setView("CREATE")}
          onKeyDown={(event) => handleTabKey(event, "CREATE")}
        >
          {dictionary.teamWorkspace.createViewAction}
        </button>
      </div>

      <div className="team-operations-stack">
        <div
          id="team-board-panel"
          className="team-operations-layer"
          role="tabpanel"
          aria-labelledby="team-board-tab"
          aria-hidden={view !== "BOARD"}
          inert={view !== "BOARD"}
          tabIndex={view === "BOARD" ? 0 : -1}
          data-layer="board"
          data-active={view === "BOARD"}
        >
          {board}
        </div>
        <div
          id="team-create-panel"
          className="team-operations-layer"
          role="tabpanel"
          aria-labelledby="team-create-tab"
          aria-hidden={view !== "CREATE"}
          inert={view !== "CREATE"}
          tabIndex={view === "CREATE" ? 0 : -1}
          data-layer="create"
          data-active={view === "CREATE"}
        >
          {creator}
        </div>
      </div>

      <p className="team-command-boundary" role="note">
        {dictionary.teamWorkspace.commandViewBoundary}
      </p>
    </section>
  );
}
