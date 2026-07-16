(() => {
  const EVIDENCE_CLASSES = {
    OFFICIAL: "war-evidence-official",
    CAMPAIGN_RESEARCH: "war-evidence-research",
    PERCEPTION: "war-evidence-perception",
    HYPOTHESIS: "war-evidence-hypothesis",
    UNKNOWN: "war-evidence-unknown"
  };

  let snapshot = null;
  let detailInvoker = null;

  const escapeHtml = (value) => String(value)
    .replaceAll("&", "&amp