"use client";

import { useMemo, useState } from "react";

import type { Dictionary } from "@/lib/i18n";

export function GuidedTeamSelector({
  dictionary,
  defaultValues,
}: Readonly<{
  dictionary: Dictionary;
  defaultValues: readonly string[];
}>) {
  const options = useMemo(
    () => Object.values(dictionary.intake.currentTeamOptions),
    [dictionary.intake.currentTeamOptions],
  );
  const [items, setItems] = useState(() => [...new Set(defaultValues)]);
  const [selection, setSelection] = useState(options[0] ?? "");
  const [custom, setCustom] = useState("");

  function add(value: string) {
    const normalized = value.trim();
    if (!normalized || items.includes(normalized) || items.length >= 30) return;
    setItems((current) => [...current, normalized]);
    setCustom("");
  }

  return (
    <fieldset className="guided-team-selector">
      <legend>{dictionary.intake.currentTeam}</legend>
      <p>{dictionary.intake.currentTeamHelp}</p>
      <input type="hidden" name="current_team" value={items.join("\n")} />

      <div className="guided-team-selector-controls">
        <label>
          <span>{dictionary.intake.currentTeamPresetLabel}</span>
          <select
            value={selection}
            onChange={(event) => setSelection(event.target.value)}
          >
            {options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => add(selection)}>
          {dictionary.intake.currentTeamAddAction}
        </button>
      </div>

      <div className="guided-team-custom-row">
        <label>
          <span>{dictionary.intake.currentTeamCustomLabel}</span>
          <input
            value={custom}
            maxLength={160}
            placeholder={dictionary.intake.currentTeamCustomPlaceholder}
            onChange={(event) => setCustom(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                add(custom);
              }
            }}
          />
        </label>
        <button type="button" onClick={() => add(custom)}>
          {dictionary.intake.currentTeamAddAction}
        </button>
      </div>

      {items.length > 0 ? (
        <ul className="guided-team-chips" aria-label={dictionary.intake.currentTeamSelectedLabel}>
          {items.map((item) => (
            <li key={item} data-team-chip="true">
              <span>{item}</span>
              <button
                type="button"
                aria-label={`${dictionary.intake.currentTeamRemoveAction}: ${item}`}
                onClick={() =>
                  setItems((current) => current.filter((value) => value !== item))
                }
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="guided-team-empty">{dictionary.intake.currentTeamEmpty}</p>
      )}
      <small>{dictionary.intake.currentTeamBoundary}</small>
    </fieldset>
  );
}
