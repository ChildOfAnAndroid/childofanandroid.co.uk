# Website safety and regression patch

Prepared against website `main` at `536955b52597389c5569816c328aec2c4b98b2a6`.

## Public interaction stays public

Chat, painting, gallery submissions, and appearance controls remain available.
The appearance endpoint now accepts only its named RGB, eyes, mouth, and boolean
movement controls. Internal speech state, arbitrary keys, and malformed values
are rejected before forwarding to BabyLLM.

A browser may still finish the current `auto-burst` snapshot. It cannot attach to
an arbitrary historical snapshot without owner authorisation. Attachments are
immutable: a repeated completion acknowledges the existing PNG instead of
replacing it. Files are validated and atomically installed without overwrite.

`/api/brain_push` remains compatible with existing BabyLLM notification clients,
but their request body is no longer written into public state. The endpoint
returns an accepted refresh hint. The existing state worker coalesces hints and
pulls authoritative state from `LLM_SERVER_URL`, at most once a second. Network
failure backoff is not bypassed by hints. No new bot-to-site secret is required.

## Owner-only operations

Gallery metadata edits and raw user-record access require
`Authorization: Bearer ...`, checked against the existing server-side
`GALLERY_ADMIN_TOKEN`. Missing configuration disables these owner operations;
there is no default password or development bypass. Never place this secret in
a `VITE_*` variable, a public asset, a URL, or version control.

The existing browser console helper accepts a fourth, per-call `adminToken`
argument. It does not store the token in localStorage or sessionStorage, and it
does not contain a bundled secret. The actual permission check is on the server.

## Reliability fixes

- One chat request makes one brain generation request, including `speak: true`.
  A timeout does not trigger the old second call.
- Completely transparent gallery images are encoded as real PNG files.
- Gallery uploads distinguish JSON envelopes from raw PNG bodies before reading
  the body. PNGs are decoded, checked, and re-encoded before public storage.
- Offline startup is reported as a warning, not a contradictory fatal message.
- Flask defaults to loopback; `BBY_HOST` is the explicit override for other
  deployment topologies. The existing Caddy-to-Flask topology uses loopback.
- Browser write origins are explicitly allowed, separately from owner auth.
  JSON errors do not turn CORS into an authentication mechanism.

## Development

All frontend API requests, including paint polling, use the current origin.
Vite's default backend is `http://127.0.0.1:8420`, not the public website.
`BBY_DEV_API_TARGET` changes it. Non-loopback targets additionally require
`BBY_DEV_ALLOW_REMOTE=1`.

Vite loads these development settings from `.env.local`. Flask does not load
Vite's environment file: export backend configuration in its own process
or preserve the existing deployment environment. `BBY_ALLOWED_ORIGINS` is a
comma-separated exact list. Defaults include the website's two HTTPS origins and
localhost/127.0.0.1 on the normal Vite port, 6969. Wildcard origins are rejected.
Private `.env` files, Python storage, bytecode, and virtual environments are ignored.

## Validation

Run from the website checkout:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --experimental-strip-types --test tests/frontend.test.mjs
npm run build
```

The isolated Python tests exercise the actual function definitions with fake
transport and real temporary storage/Pillow processing. They do not import/start
Flask or claim to test HTTP middleware. The separate Flask test-client suite uses
a temporary server copy and suppresses background thread startup. It is explicitly
skipped when Flask or flask-cors is unavailable.

## Applying and deploying

The supplied Git patch changes source and adds tests/documentation. It does not
commit, push, send email, restart services, or deploy itself. Apply it with
`git apply --check` followed by `git apply` in the website repository.

Use the existing `deploy_bby.sh` workflow to ship both the frontend and the
updated `PYTHON/bbyServer.py`, preserving the backend storage directory and its
private environment. Do not replace backend storage with build output.

The Bopit website hook introduced in ICHARIS2 #2406 publishes `dist/`; that is not
by itself a backend-code rollout. These server guards are not live until the
backend file is updated and the running server is restarted through its existing
owner. No new deployment mechanism is introduced by this patch.

This is a focused remediation, not a complete security review of every public
chat/consent, account-identity, resource-limit, or hosting behaviour.
