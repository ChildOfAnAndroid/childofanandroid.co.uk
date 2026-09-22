# Charis Cat // Child of an Android

Vue/Vite frontend in `src/`, public OAuth information pages in `public/`, and the
Flask gateway in `PYTHON/bbyServer.py`. BabyLLM's brain is a separate process.

## Local development

Install the locked frontend dependencies with `npm ci`, then `npm run dev`.
The browser uses same-origin `/api` URLs, including paint-event polling. Vite
proxies these to **http://127.0.0.1:8420**, not the live website. Vite listens on
127.0.0.1:6969 by default; use its explicit `--host` option for deliberate LAN use.

`BBY_DEV_API_TARGET` can select another backend origin. A non-loopback target also
requires `BBY_ALLOW_REMOTE_DEV_API=1`; this deliberately opts into affecting that
backend. Neither variable contains a credential.

The Python gateway needs Flask, Flask-Cors, requests, and Pillow. Its environment
is supplied by the shell/service manager, not automatically loaded from `.env`.
`.env.example` illustrates local development settings. Keep an existing deployed
`LLM_SERVER_URL` and storage directory unchanged during an upgrade.

## Public versus privileged operations

- Chat, painting, new snapshots, and gallery submissions remain public.
- Public `/api/state` changes are limited to RGB integers in 0..255 and the existing
  boolean jump/blush/stretch-up controls. Other state changes require the admin token.
- `/api/brain_push` requires the internal token. It is not a public state-write API.
- Gallery metadata edits require the admin token.
- A browser may fill the **current, blank auto-burst snapshot** once. Repeated
  autosnap uploads preserve the existing image. Other attachments or replacements
  require the admin token. IDs must refer to existing snapshots and uploads must
  be valid PNGs. This retains the collaborative autosnap behaviour; it is not an
  authenticated attribution scheme for public contributors.

The server reads separate `BBY_ADMIN_TOKEN` and `BBY_INTERNAL_TOKEN` secrets,
each at least 32 characters, from its environment. Privileged routes return 503
when their secret is not configured and 401 for a missing/wrong bearer token.
There is no default password, loopback bypass, or Origin-based authentication.
Generate independent secrets with a password manager or `secrets.token_urlsafe(32)`.
Never commit them, put them in a `VITE_*` variable, or store them in browser storage.

The existing browser console helper has the signature
`cab.name(imageUrl, title, optionalLabel, adminToken)`. It passes the token to that
single fixed admin endpoint only; public requests never inherit it.

The BabyLLM reactive-push caller must send
`Authorization: Bearer <BBY_INTERNAL_TOKEN>` using the matching server-side secret.
Coordinate that caller update before enabling the new gateway in production.
The existing state polling still reads the configured
brain at ten-second intervals when reactive push is unavailable; preserve the
private reverse-tunnel configuration. No change here configures the remote caller.

CORS uses explicit origins only. `BBY_ALLOWED_ORIGINS` defaults to the apex and
www HTTPS website origins. Local development needs its localhost origins in the
local Python server's environment. Requests with a disallowed browser Origin
cannot perform writes. CORS is not a substitute for the bearer checks.

## Tests

`npm run test:frontend` strictly typechecks the API module and runs mocked-fetch
Node tests. `npm run test:server` runs isolated tests of the actual Python handler
bodies and PNG/file behaviour without starting workers or making live requests.
A Flask route-registration smoke test runs when Flask and Flask-Cors are installed;
otherwise unittest reports it as skipped. These are not a full security audit.

`npm run build` remains the full Vue/TypeScript/Vite production build.

## Deployment boundary

The ICHARIS2 Bopit website step builds this repository's `main` and uploads `dist/`.
That publishes the frontend and static OAuth pages **only**. It does not install
or restart `PYTHON/bbyServer.py`, configure its secrets, or update BabyLLM.
A merged Python change is not evidence that the live API is protected.

Deploy the gateway with the existing backend service/deploy helper, preserving
`PYTHON/storage` (or `BBY_STORAGE_DIR`) and coordinating the reactive-push token.
Do not point a destructive frontend sync at a directory containing backend state.
`deploy_bby.sh` remains ignored because it is an existing operator-local helper;
its contents and remote service configuration are not defined by this repository.

The configured OAuth paths remain `/`, `/privacy-policy`, and `/terms`;
`/monzboi/` provides the app explanation and `/privacy/` remains the existing alias.
