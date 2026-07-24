# brace-expansion compatibility shim

This private package keeps the CommonJS callable export required by `minimatch@3` while delegating expansion to patched `brace-expansion@5.0.8`.

It exists because GHSA-mh99-v99m-4gvg affects the legacy `brace-expansion` versions used by the current ESLint 9 / Next.js toolchain, while version 5 changed its CommonJS export shape. The shim exports both the legacy callable function and `.expand`, allowing `minimatch@3` and `minimatch@10` to share the patched implementation.

Remove this shim when every locked upstream consumer supports a patched `brace-expansion` release directly. Any change must continue to pass `make frontend-verify` and `npm audit --audit-level=moderate` with zero findings.
