import type { TeamRoleCard } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

type TeamRoleConsultingProfile = Pick<
  TeamRoleCard,
  "decision_scope" | "deliverables" | "collaboration_points" | "success_signals"
>;

export function TeamRoleDossier({
  profile,
  dictionary,
}: Readonly<{
  profile: TeamRoleConsultingProfile;
  dictionary: Dictionary;
}>) {
  const sections = [
    {
      key: "decisions",
      title: dictionary.teamWorkspace.decisionScopeLabel,
      items: profile.decision_scope,
    },
    {
      key: "deliverables",
      title: dictionary.teamWorkspace.deliverablesLabel,
      items: profile.deliverables,
    },
    {
      key: "collaboration",
      title: dictionary.teamWorkspace.collaborationPointsLabel,
      items: profile.collaboration_points,
    },
    {
      key: "signals",
      title: dictionary.teamWorkspace.successSignalsLabel,
      items: profile.success_signals,
    },
  ] as const;
  const hasProfile = sections.some((section) => section.items.length > 0);

  return (
    <details className="team-role-dossier">
      <summary>
        <span>{dictionary.teamWorkspace.roleDossierAction}</span>
        <small>{dictionary.teamWorkspace.consultingReadout}</small>
      </summary>
      {hasProfile ? (
        <div className="team-role-dossier-grid">
          {sections.map((section) =>
            section.items.length > 0 ? (
              <section key={section.key}>
                <h6>{section.title}</h6>
                <ul>
                  {section.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ) : null,
          )}
        </div>
      ) : (
        <p className="team-role-dossier-missing">
          {dictionary.teamWorkspace.roleDossierMissing}
        </p>
      )}
    </details>
  );
}
