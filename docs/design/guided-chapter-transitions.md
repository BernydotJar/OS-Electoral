# Guided campaign chapters and operating motion

`C3-FRONT-007` replaces the continuously stacked campaign workspaces with one command overview and one URL-addressable route per campaign chapter.

## Navigation model

```text
/{locale}
/{locale}/campaign/foundation
/{locale}/campaign/evidence
/{locale}/campaign/team
/{locale}/campaign/strategy
/{locale}/campaign/operations
```

The locale root is the command overview: it contains campaign context, current mission, the roadmap and governed readiness information. It does not render the five chapter workspaces. A chapter route renders one mission, the compact chapter navigator and previous/next controls.

Existing workspace anchors remain canonical inside their chapter route. Form redirects, preview requests and locale changes preserve the current chapter, query and anchor. Browser back/forward therefore restores real campaign locations instead of replaying scroll positions in one document.

A valid but locked chapter request fails closed to the current available mission and explains the fallback. Invalid chapter slugs return `404`.

## Transition behavior

CampaignOS uses the experimental Next.js 16 / React 19 `ViewTransition` integration already present in the locked dependency graph. No animation library, third-party media, tracking or external host is added.

- forward navigation moves the outgoing chapter left and introduces the next chapter from the right;
- backward navigation mirrors the direction;
- the current chapter indicator uses one shared transition identity;
- navigation remains interruptible and degrades to ordinary App Router navigation when the browser lacks View Transition support;
- `prefers-reduced-motion: reduce` disables every route animation and loading sweep.

Motion never changes authorization, data, completion, evidence or availability. It only communicates direction and continuity.

## Mission cadence

The campaign hero includes one visible three-stage operating cadence:

1. evidence;
2. human decision;
3. governed execution.

The moving pulse communicates flow rather than decoration. The active chapter changes the pulse accent without changing meaning. Reduced-motion mode renders the same three stages as a static diagram.

## Accessibility and safety

- routes have stable URLs and native link semantics;
- one chapter is marked `aria-current="step"`;
- previous/next labels remain explicit;
- focus, keyboard, locale switching and browser history are preserved;
- narrow screens use horizontal chapter navigation with snap points while the mission itself remains one column;
- the primary hero action uses a solid high-contrast foreground/background pair;
- axe WCAG 2.2 AA automation, overflow checks and reduced-motion browser checks are required.

Production remains blocked. Chapter navigation grants no permission and causes no external campaign effect.
