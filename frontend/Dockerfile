# syntax=docker/dockerfile:1.7@sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e

ARG NODE_IMAGE=node:22.23.1-alpine3.23@sha256:8516dce0483394d5708d4b2ee6cacb79fb1d617ea4e2787c2120bcca92ce372e

FROM ${NODE_IMAGE} AS dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts \
    && npm cache clean --force

FROM ${NODE_IMAGE} AS builder

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app

COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE_IMAGE} AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 10001 campaignos \
    && adduser --system --uid 10001 --ingroup campaignos \
        --home /nonexistent --shell /sbin/nologin campaignos

WORKDIR /app

COPY --from=builder --chown=10001:10001 /app/public ./public
COPY --from=builder --chown=10001:10001 /app/.next/standalone ./
COPY --from=builder --chown=10001:10001 /app/.next/static ./.next/static

USER 10001:10001

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:3000/es').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

STOPSIGNAL SIGTERM

CMD ["node", "server.js"]
