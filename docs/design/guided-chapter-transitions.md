# Guided campaign chapters and operating motion

`C3-FRONT-007` introduced URL-addressable campaign chapters. `C3-FRONT-008R1` repairs their presentation hierarchy after human QA: the requested workspace now follows a compact command bar instead of a full route-wide navigator or repeated mission hero.

## Navigation model

```text
/{locale}
/{locale}/campaign/foundation
/{locale}/campaign/evidence
/{locale}/campaign/team
/{locale}/campaign/strategy
/{locale}/campaign/operations
```

The locale root is the command overview. It contains campaign context, the interactive campaign path and governed readiness information, but no chapter workspace.

A chapter route contains:

1. a compact command bar;
2. the selected workspace;
3. no active-mission hero;
4. no unselected workspace.

The command bar exposes overview, current chapter, previous/next and a closed-by-default full campaign map. This preserves orientation without displacing the primary task.

Workspace anchors remain canonical inside their chapter route. Form redirects, preview requests and locale changes preserve chapter, query and anchor. Browser back/forward restores campaign locations rather than replaying scroll positions in one document.

A valid but locked chapter request fails closed to the current available mission and explains the fallback. Invalid chapter slugs return `404`.

## Transition behavior

CampaignOS uses the Next.js/React View Transition integration already present in the locked dependency graph. No animation library, third-party media, tracking or external host is added.

- forward navigation communicates movement to a later chapter;
- backward navigation mirrors the direction;
- the current chapter indicator uses one shared transition identity;
- navigation remains interruptible and degrades to normal App Router navigation;
- `prefers-reduced-motion: reduce` disables non-essential route animation.

Motion never changes authorization, data, completion, evidence or availability.

## Progressive disclosure

The complete five-stage map is available through a native `details` element. It begins closed, is keyboard-operable and exposes stable links only for navigable stages. Locked and blocked stages remain visible as status, not as broken actions.

## Accessibility and safety

- routes have stable URLs and native link semantics;
- one chapter carries `aria-current="step"`;
- previous/next labels remain explicit;
- focus, keyboard, locale switching and browser history are preserved;
- narrow screens keep the workspace one column and allow only the disclosed map to scroll horizontally;
- automated axe WCAG 2.2 AA, overflow and reduced-motion checks are release gates;
- chapter navigation grants no permission and causes no external campaign effect.

Production remains blocked.
