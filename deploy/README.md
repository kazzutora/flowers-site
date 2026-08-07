# Test VPS deploy — one-time setup

`.github/workflows/deploy.yml` builds the `prod` image, pushes it to
`ghcr.io`, then SSHes in and restarts the stack. None of this runs until
the steps below are done by hand once — provisioning a server, DNS and
secrets isn't something CI can do for itself.

## 1. Server

- Ubuntu 22.04+ VPS with Docker Engine + the Compose plugin installed.
- `git clone` this repo to `/srv/flowers-site` (only `deploy/` and `.env`
  are actually read at runtime — the app itself runs from the pulled
  image, not from this checkout).
- Copy `.env.example` to `/srv/flowers-site/.env`, fill in real values
  (`DEBUG=false`, real `SECRET_KEY`/`POSTGRES_PASSWORD`, S3 media
  credentials), and add two deploy-only keys the compose file expects:
  `SITE_DOMAIN=your-test-domain.example` and `IMAGE=` (left blank; the
  deploy workflow fills it in on each run).
- `systemctl enable --now docker`
- Copy `deploy/flowers-site.service` to `/etc/systemd/system/`, then
  `systemctl enable flowers-site` so the stack survives a reboot.

## 2. DNS

Point `SITE_DOMAIN`'s A/AAAA record at the VPS. Caddy issues its own TLS
certificate on first request — no manual certbot step.

## 3. GitHub repo secrets

| Secret | Value |
|---|---|
| `TEST_VPS_HOST` | server IP or hostname |
| `TEST_VPS_USER` | SSH user with docker access |
| `TEST_VPS_SSH_KEY` | private key matching a public key in that user's `~/.ssh/authorized_keys` |

`GITHUB_TOKEN` (pushing to `ghcr.io`, pulling on the VPS) is provided
automatically by Actions — nothing to add for it, but the deploy user on
the VPS needs `docker login ghcr.io` to succeed, which the workflow does
on every run using that same token.

## 4. First deploy

Push to `main`, or run the "Deploy to test VPS" workflow manually. After
that, every merge to `main` redeploys automatically — this is the
acceptance criterion in DEV.md S0.10: no manual step from merge to live.
