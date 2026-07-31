"use client";

import { useMemo, useState } from "react";

import type {
  TeamRoleCard,
  TeamWorkItem,
  TeamWorkItemStatus,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";

const STATUSES: readonly TeamWorkItemStatus[] = [
  "PLANNED",
  "ACTIVE",
  "BLOCKED",
  "COMPLETE",
];

export function TeamOperationsBoard({
  locale,
  dictionary,
  roles,
  workItems,
  workspaceVersion,
  canUpdate,
  embedded = false,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  roles: readonly TeamRoleCard[];
  workItems: readonly TeamWorkItem[];
  workspaceVersion: number;
  canUpdate: boolean;
  embedded?: boolean;
}>) {
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<
    "ALL" | "ATTENTION" | TeamWorkItemStatus
  >("ALL");
  const rolesById = useMemo(
    () => new Map(roles.map((role) => [role.id, role])),
    [roles],
  );
  const filtered = useMemo(
    () =>
      workItems.filter(
        (item) =>
          (statusFilter === "ALL" ||
            item.status === statusFilter ||
            (statusFilter === "ATTENTION" &&
              (item.status === "BLOCKED" ||
                item.health === "AT_RISK" ||
                item.health === "OFF_TRACK"))) &&
          (roleFilter === "ALL" ||
            item.assignments.some(
              (assignment) => assignment.role_id === roleFilter,
            )),
      ),
    [roleFilter, statusFilter, workItems],
  );
  const counts = useMemo(
    () => ({
      PLANNED: workItems.filter((item) => item.status === "PLANNED").length,
      ACTIVE: workItems.filter((item) => item.status === "ACTIVE").length,
      BLOCKED: workItems.filter((item) => item.status === "BLOCKED").length,
      COMPLETE: workItems.filter((item) => item.status === "COMPLETE").length,
      attention: workItems.filter(
        (item) =>
          item.status === "BLOCKED" ||
          item.health === "AT_RISK" ||
          item.health === "OFF_TRACK",
      ).length,
    }),
    [workItems],
  );

  return (
    <section
      id="team-operations-board"
      className="team-operations-board"
      aria-labelledby={embedded ? undefined : "team-operations-title"}
      aria-label={embedded ? dictionary.teamWorkspace.operationsTitle : undefined}
    >
      <div className="team-operations-heading" data-embedded={embedded}>
        {embedded ? null : (
          <div>
            <p className="eyebrow">
              {dictionary.teamWorkspace.operationsEyebrow}
            </p>
            <h3 id="team-operations-title">
              {dictionary.teamWorkspace.operationsTitle}
            </h3>
            <p>{dictionary.teamWorkspace.operationsBody}</p>
          </div>
        )}
        <div
          className="team-work-pulse"
          aria-label={dictionary.teamWorkspace.workPulse}
        >
          {STATUSES.map((status) => (
            <button
              key={status}
              type="button"
              data-active={statusFilter === status}
              aria-pressed={statusFilter === status}
              onClick={() =>
                setStatusFilter(statusFilter === status ? "ALL" : status)
              }
            >
              <strong>{counts[status]}</strong>
              <span>{dictionary.teamWorkspace.workStatusLabels[status]}</span>
            </button>
          ))}
          <button
            type="button"
            className="attention"
            data-active={statusFilter === "ATTENTION"}
            aria-pressed={statusFilter === "ATTENTION"}
            onClick={() =>
              setStatusFilter(
                statusFilter === "ATTENTION" ? "ALL" : "ATTENTION",
              )
            }
          >
            <strong>{counts.attention}</strong>
            <span>{dictionary.teamWorkspace.attention}</span>
          </button>
        </div>
      </div>

      <div className="team-board-filters">
        <label>
          <span>{dictionary.teamWorkspace.filterRole}</span>
          <select
            value={roleFilter}
            onChange={(event) => setRoleFilter(event.target.value)}
          >
            <option value="ALL">{dictionary.teamWorkspace.allRoles}</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.teamWorkspace.filterStatus}</span>
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value as "ALL" | TeamWorkItemStatus)
            }
          >
            <option value="ALL">{dictionary.teamWorkspace.allStatuses}</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {dictionary.teamWorkspace.workStatusLabels[status]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {filtered.length === 0 ? (
        <p className="team-board-empty" role="status">
          {dictionary.teamWorkspace.noWorkItems}
        </p>
      ) : (
        <div className="team-work-columns">
          {STATUSES.map((status) => {
            const items = filtered.filter((item) => item.status === status);
            if (
              statusFilter !== "ALL" &&
              statusFilter !== "ATTENTION" &&
              statusFilter !== status
            ) {
              return null;
            }
            if (statusFilter === "ATTENTION" && items.length === 0) return null;
            return (
              <section
                key={status}
                data-status={status}
                aria-labelledby={`team-column-${status}`}
              >
                <header>
                  <h4 id={`team-column-${status}`}>
                    {dictionary.teamWorkspace.workStatusLabels[status]}
                  </h4>
                  <span>{items.length}</span>
                </header>
                <div className="team-work-column-list">
                  {items.map((item) => {
                    const accountable = item.assignments.find(
                      (assignment) =>
                        assignment.responsibility === "ACCOUNTABLE",
                    );
                    const accountableRole = accountable
                      ? rolesById.get(accountable.role_id)
                      : undefined;
                    const canActivate = item.assignments
                      .filter(
                        (assignment) =>
                          assignment.responsibility === "ACCOUNTABLE" ||
                          assignment.responsibility === "RESPONSIBLE",
                      )
                      .every(
                        (assignment) =>
                          rolesById.get(assignment.role_id)?.status ===
                          "FILLED",
                      );
                    return (
                      <article
                        key={item.id}
                        className="team-work-card"
                        data-status={item.status}
                        data-priority={item.priority}
                        data-health={item.health}
                      >
                        <div className="team-work-card-topline">
                          <span
                            className="team-work-card-status"
                            data-status={item.status}
                          >
                            {dictionary.teamWorkspace.workStatusLabels[item.status]}
                          </span>
                          <div className="team-work-card-meta">
                            <span data-kind="type">
                              {
                                dictionary.teamWorkspace.workTypeLabels[
                                  item.work_type
                                ]
                              }
                            </span>
                            <span data-kind="priority" data-value={item.priority}>
                              {
                                dictionary.teamWorkspace.priorityLabels[
                                  item.priority
                                ]
                              }
                            </span>
                            <span data-kind="health" data-value={item.health}>
                              {dictionary.teamWorkspace.healthLabels[item.health]}
                            </span>
                          </div>
                        </div>
                        <div className="team-work-card-copy">
                          <h5>{item.name}</h5>
                          <p>{item.description}</p>
                        </div>
                        <dl className="team-work-card-facts">
                          <div>
                            <dt>{dictionary.teamWorkspace.assignedFunction}</dt>
                            <dd>
                              {accountableRole?.title ??
                                accountable?.role_id ??
                                "—"}
                            </dd>
                          </div>
                          <div>
                            <dt>{dictionary.teamWorkspace.targetDate}</dt>
                            <dd>{item.target_date ?? "—"}</dd>
                          </div>
                          <div>
                            <dt>{dictionary.teamWorkspace.cadence}</dt>
                            <dd>
                              {
                                dictionary.teamWorkspace.cadenceLabels[
                                  item.cadence
                                ]
                              }
                            </dd>
                          </div>
                        </dl>
                        {item.next_action ? (
                          <section
                            className="team-work-next-action"
                            aria-label={dictionary.teamWorkspace.workNextAction}
                          >
                            <strong>
                              {dictionary.teamWorkspace.workNextAction}
                            </strong>
                            <p>{item.next_action}</p>
                          </section>
                        ) : null}
                        {item.blocker ? (
                          <div className="team-work-blocker" role="note">
                            <strong>{dictionary.teamWorkspace.blocker}</strong>
                            <p>{item.blocker}</p>
                          </div>
                        ) : null}
                        <details className="team-work-details">
                          <summary>
                            {dictionary.teamWorkspace.operationalDetails}
                          </summary>
                          {item.evidence.length > 0 ? (
                            <div>
                              <strong>
                                {dictionary.teamWorkspace.workEvidence}
                              </strong>
                              <ul>
                                {item.evidence.map((entry) => (
                                  <li key={entry}>{entry}</li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                          {item.check_in_note ? (
                            <div>
                              <strong>
                                {dictionary.teamWorkspace.checkInNote}
                              </strong>
                              <p>{item.check_in_note}</p>
                              <small>
                                {dictionary.teamWorkspace.lastCheckIn}:{" "}
                                {item.last_check_in_at ?? "—"}
                              </small>
                            </div>
                          ) : null}
                          <ul className="team-work-raci">
                            {item.assignments.map((assignment) => (
                              <li
                                key={`${assignment.role_id}:${assignment.responsibility}`}
                              >
                                <span>
                                  {
                                    dictionary.teamWorkspace
                                      .responsibilityLabels[
                                      assignment.responsibility
                                    ]
                                  }
                                </span>
                                {rolesById.get(assignment.role_id)?.title ??
                                  assignment.role_id}
                              </li>
                            ))}
                          </ul>
                        </details>
                        {canUpdate ? (
                          <details className="team-work-check-in">
                            <summary>
                              {dictionary.teamWorkspace.updateWorkItem}
                            </summary>
                            <form
                              action="/api/ui/team-workspace/work-item-status"
                              method="post"
                            >
                              <input
                                type="hidden"
                                name="locale"
                                value={locale}
                              />
                              <input
                                type="hidden"
                                name="version"
                                value={workspaceVersion}
                              />
                              <input
                                type="hidden"
                                name="work_item_id"
                                value={item.id}
                              />
                              <input
                                type="hidden"
                                name="idempotency_key"
                                value={`team-work-item-update:${workspaceVersion}:${item.id}`}
                              />
                              <label>
                                <span>
                                  {dictionary.teamWorkspace.workStatus}
                                </span>
                                <select
                                  name="status"
                                  defaultValue={item.status}
                                >
                                  {STATUSES.map((candidate) => (
                                    <option
                                      key={candidate}
                                      value={candidate}
                                      disabled={
                                        !canActivate &&
                                        (candidate === "ACTIVE" ||
                                          candidate === "BLOCKED" ||
                                          candidate === "COMPLETE")
                                      }
                                    >
                                      {
                                        dictionary.teamWorkspace
                                          .workStatusLabels[candidate]
                                      }
                                    </option>
                                  ))}
                                </select>
                                {!canActivate ? (
                                  <small>
                                    {
                                      dictionary.teamWorkspace
                                        .activateRequiresFilledRole
                                    }
                                  </small>
                                ) : null}
                              </label>
                              <label>
                                <span>{dictionary.teamWorkspace.priority}</span>
                                <select
                                  name="priority"
                                  defaultValue={item.priority}
                                >
                                  {Object.entries(
                                    dictionary.teamWorkspace.priorityLabels,
                                  ).map(([value, label]) => (
                                    <option key={value} value={value}>
                                      {label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label>
                                <span>{dictionary.teamWorkspace.health}</span>
                                <select
                                  name="health"
                                  defaultValue={item.health}
                                >
                                  {Object.entries(
                                    dictionary.teamWorkspace.healthLabels,
                                  ).map(([value, label]) => (
                                    <option key={value} value={value}>
                                      {label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label>
                                <span>{dictionary.teamWorkspace.cadence}</span>
                                <select
                                  name="cadence"
                                  defaultValue={item.cadence}
                                >
                                  {Object.entries(
                                    dictionary.teamWorkspace.cadenceLabels,
                                  ).map(([value, label]) => (
                                    <option key={value} value={value}>
                                      {label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label>
                                <span>
                                  {dictionary.teamWorkspace.targetDate}
                                </span>
                                <input
                                  name="target_date"
                                  type="date"
                                  defaultValue={item.target_date ?? ""}
                                />
                              </label>
                              <label>
                                <span>
                                  {dictionary.teamWorkspace.workNextAction}
                                </span>
                                <textarea
                                  name="next_action"
                                  maxLength={1000}
                                  rows={2}
                                  defaultValue={item.next_action ?? ""}
                                />
                              </label>
                              <label>
                                <span>{dictionary.teamWorkspace.blocker}</span>
                                <textarea
                                  name="blocker"
                                  maxLength={1000}
                                  rows={2}
                                  defaultValue={item.blocker ?? ""}
                                />
                              </label>
                              <label>
                                <span>
                                  {dictionary.teamWorkspace.checkInNote}
                                </span>
                                <textarea
                                  name="check_in_note"
                                  maxLength={2000}
                                  rows={3}
                                  defaultValue={item.check_in_note ?? ""}
                                  required
                                />
                              </label>
                              <button type="submit">
                                {dictionary.teamWorkspace.saveCheckIn}
                              </button>
                            </form>
                          </details>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </section>
  );
}
