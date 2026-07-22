# Grayhat Frappe v16 deployment

This repository builds and operates a combined Frappe v16 image containing ERPNext, HRMS, and Payments. It is intentionally a small deployment repository rather than a copy of `frappe_docker`.

## Repository contract

- [`build/apps.json`](build/apps.json) is the only source of ERPNext, HRMS, and Payments refs used by the image build.
- [`.github/workflows/build-image.yml`](.github/workflows/build-image.yml) is manual-only. It pins Frappe and the official `frappe_docker` builder once, uses the upstream layered Containerfile without modification, verifies all four apps, and only publishes when `publish=true` is explicitly selected.
- [`compose.yaml`](compose.yaml) is pull-only and designed to be pasted into a Coolify user-defined Service. It defines the normal deployment path plus separate opt-in backup and restore jobs. Coolify is not connected to this Git repository.

The image workflow publishes the requested immutable release tag. Do not deploy `latest` or a mutable branch tag.

## Deployment sequence

Each deployment runs the official-style one-shot configurator, creates a site only when the sites volume is genuinely empty, ensures Payments, ERPNext, and HRMS are installed, and runs Frappe migration before starting the runtime services. Existing cloned and production sites skip creation automatically.

The v15-to-v16 rehearsal uses a complete isolated copy of the production database and sites data. After the clone passes with the v16 application image and MariaDB 11.8, production receives the same image and Compose changes. There are no deployment modes; backup and restore are separate opt-in jobs.

## Backup and restore

The Compose file includes three optional maintenance jobs: `backup`, `restore`, and `restore-db`. They are disabled by default and only run when the corresponding environment flag is enabled.

- `ENABLE_BACKUP=true` runs a Frappe backup and then stores the site data with Restic.
- `ENABLE_RESTORE=true` restores a site snapshot from Restic into the sites volume.
- `ENABLE_DB_RESTORE=true` restores the database backup files from the site's `private/backups` directory.

See [the Coolify migration runbook](docs/coolify-v15-to-v16.md) before changing the live Service.

Run [`scripts/inspect_live_stack.sh`](scripts/inspect_live_stack.sh) from the Coolify Docker host with the backend container name and, when internal, the database container name. It reports image IDs/digests, mounts, app versions, site names, and the database version without printing environment secrets.

## Authoritative references

- [Official Frappe Docker repository](https://github.com/frappe/frappe_docker)
- [Frappe backup command](https://docs.frappe.io/framework/user/en/bench/reference/backup)
- [Frappe restore command](https://docs.frappe.io/framework/user/en/bench/reference/restore)
- [Frappe v16 migration notes](https://github.com/frappe/frappe/wiki/Migrating-to-version-16)
- [ERPNext v16 migration notes](https://github.com/frappe/erpnext/wiki/Migration-Guide-To-ERPNext-Version-16)
- [MariaDB major-version upgrade guidance](https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/platform-specific-upgrade-guides/upgrading-on-linux/upgrading-between-major-mariadb-versions)
- [Coolify user-defined Services](https://coolify.io/docs/services/introduction)
- [Coolify Compose behavior](https://coolify.io/docs/knowledge-base/docker/compose)
