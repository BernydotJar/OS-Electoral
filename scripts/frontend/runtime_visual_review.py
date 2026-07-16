#!/usr/bin/env python3
"""Runtime and visual review for CampaignOS frontend modules.

The runner reuses a healthy CampaignOS server when one already exists. If the
configured URL is unavailable and points to localhost, it starts a temporary
static server and stops it after the review. When the default port is occupied
by an unhealthy process, the runner selects an available local port.
"