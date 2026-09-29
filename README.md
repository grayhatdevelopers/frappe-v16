# Frappe v16 deployment

ERPNext and Frappe HR in one image, with a Compose file that deploys a site safely: every
deploy is backed up first and rolled back if the migration fails, and backups go offsite with
[Restic](https://restic.net). Made for [Coolify](https://coolify.io); plain Docker Compose works
too.

## What's included

| App | What it does |
| --- | --- |
| [ERPNext](https://github.com/frappe/erpnext) | Accounting, buying, selling, stock and projects. |
| [Frappe HR](https://github.com/frappe/hrms) | HR and payroll. |
| [Payments](https://github.com/frappe/payments) | Payment gateway integrations. |
| [Frappe Assistant Core](https://github.com/buildswithpaul/Frappe_Assistant_Core) | MCP server that lets AI assistants work with Frappe data. |
| [Overtime Management](https://github.com/grayhatdevelopers/frappe_overtime_management) | Ours: overtime on top of Frappe HR. |
| [Restic Backups](https://github.com/grayhatdevelopers/frappe_restic) | Ours: backups, safe deploys and restores. |

Versions are pinned in [`build/apps.json`](build/apps.json) and
[`build/frappe.env`](build/frappe.env). Images are published as
`ghcr.io/grayhatdevelopers/frappe-v16:vX.Y.Z`.

## Quick start

1. Copy [`.env.example`](.env.example) to `.env` and replace the `replace-me` values.
2. Run `docker compose up -d`.
3. Put a reverse proxy in front of the `frontend` service; its port is not published.

On Coolify, create a Docker Compose resource from this repository and set the same variables
there.

## Configuration

| Variable | Purpose |
| --- | --- |
| `APP_IMAGE` | The image to run: a release of this repository. |
| `SITE_NAME` | The site's name. |
| `ADMIN_PASSWORD` | Administrator password, used only when creating a new site. |
| `ENABLE_DB`, `DB_HOST`, `DB_PORT`, `DB_ROOT_PASSWORD` | The bundled MariaDB, or an external one with `ENABLE_DB=0`. |
| `RESTIC_OFFSITE_BACKUP_ENABLED` | `1` uploads backups; `0` keeps them on the server. |
| `RESTIC_REPOSITORY`, `RESTIC_PASSWORD`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Where backups go. Keep a copy of `RESTIC_PASSWORD` outside the server. |
| `RESTIC_BACKUP_UPTIME_KUMA_URL`, `RESTIC_DEPLOYMENT_BACKUP_UPTIME_KUMA_URL` | Optional Uptime Kuma push monitors. |
| `SITE_OPERATION`, `RESTIC_RESTORE_SNAPSHOT` | Deploy normally, or restore a snapshot. |

## Deploying

```text
db, redis → configurator → create-site → site-operation → install-apps → runtime services
```

- **create-site** creates the site on empty volumes; otherwise it does nothing.
- **site-operation** backs up the site, migrates it and records the release. If the migration
  fails, the site is returned to that backup and the new image never starts.
- **install-apps** installs any app in the image that the site does not have yet.
- **Runtime services** (backend, websocket, frontend, workers, scheduler) refuse to start
  during a restore.

Stop the runtime services before each deployment; Coolify does this on every deploy. See
[Restic Backups' deployment docs](https://github.com/grayhatdevelopers/frappe_restic/blob/main/docs/deployment.md)
for details.

## Restoring

1. Set `SITE_OPERATION=restore` and `RESTIC_RESTORE_SNAPSHOT` to a short snapshot ID (or
   `latest`).
2. Deploy. The site is restored and migrated to this image; a failed restore returns it to
   where it was.
3. Set `SITE_OPERATION=migrate` again.

Redeploying the same snapshot does nothing. A restore works on empty volumes too.

## Upgrading

- **Frappe and apps:** Renovate opens pull requests for new releases; each one builds and
  tests the image.
- **Frappe v15 to v16:** see [docs/coolify-v15-to-v16.md](docs/coolify-v15-to-v16.md).

## Development

How the image is built, tested and released: [docs/development.md](docs/development.md).

## License

[MIT](LICENSE), by [Grayhat](https://github.com/grayhatdevelopers).
