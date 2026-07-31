# Cinematic campaign journey

Status: historical design record for `C3-FRONT-006`; production remains blocked.

> Superseded presentation note: human QA in `C3-FRONT-008R1` removed the separate first-use/active mission hero from the current product. CampaignOS now uses one restrained command overview and compact chapter bars. The safety, route-motion and no-external-media constraints in this record remain authoritative.

## Intent

CampaignOS uses cinematic composition to communicate consequence, continuity and progress. It does not imitate a generic marketing landing page and does not depend on third-party video, tracking, browser storage or remote visual assets.

The experience adapts to persisted campaign state:

- `FIRST_USE`: an owned five-act opening — territory, evidence, team, strategy and operation — introduces the operating path once.
- `ACTIVE`: the opening contracts into the current mission, exact progress and next safe action.
- `COMPLETE`: onboarding language is replaced by a command-center entry while human authority remains explicit.

## Taste controls

```yaml
design_variance: 8
motion_intensity: 7
visual_density: 4
```

- Asymmetry and large editorial type establish hierarchy.
- One dominant chapter occupies the viewport; the remaining stages form a navigable horizon.
- Motion is limited to opacity and transform and communicates entry, progress and orientation.
- Operational forms remain denser than the opening and are not covered by decorative motion.

## Visual narrative

The first-use storyboard presents five owned visual signals:

1. Territory
2. Evidence
3. Team
4. Strategy
5. Operation

The signals are CSS-rendered and contain no runtime request. Reference products such as SceneAI informed only scale, depth and atmosphere; no asset, implementation, logo, video or tracking dependency was copied into CampaignOS.

## Motion contract

- `scene-arrive`: sequential opacity/translation for the five-act opening.
- `progress-reveal`: scale transform tied to persisted completion count.
- `beacon-breathe`: non-essential atmospheric transform/opacity.
- existing shared duration, easing and distance tokens remain authoritative.
- `prefers-reduced-motion: reduce` removes all non-essential animation and current-card displacement.
- no animation blocks interaction, changes layout geometry or moves focus.

## Accessibility contract

- the current chapter carries `aria-current="step"`;
- exact completion is exposed through a named `progressbar` with min/max/current values;
- blocked stages include a title and corrective explanation, not only a color or icon;
- focus remains visible on all actions;
- the horizon supports horizontal overflow without page overflow;
- mobile, keyboard, English/Spanish and reduced-motion variants are release gates;
- the decorative storyboard is hidden from assistive technology because equivalent meaning exists in the heading and ordered route.

## Safety and authority

The journey never converts UI completion into political, legal, financial, publication, contact, mobilization, deployment or production authority. Links remain bounded to implemented internal workspaces. A blocked stage cannot render an action link.
