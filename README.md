# Grayhat Frappe v16 deployment

This repository builds and operates a combined Frappe v16 image containing ERPNext, HRMS, and Payments. It is intentionally a small deployment repository rather than a copy of `frappe_docker`.

## Repository contract

- [`build/versions.env`](build/versions.env) is the human-readable version lock.
- [`build/image-manifest.json`](build/image-manifest.json) is embedded in every image and checked before migration.
- [`build/apps.json`](build/apps.json) selects the released ERPNext and HRMS tags. Payments is checked out to the exact commit in the version lock because it currently has no v16 release tag.
- [`.github/workflows/build-image.yml`](.github/workflows/build-image.yml) is manual-only. It checks out the official `frappe_docker` builder at a pinned commit, builds, verifies all four apps, and only publishes when `publish=true` is explicitly selected.
- [`compose.yaml`](compose.yaml) is pull-only and designed to be pasted into a Coolify user-defined Service. Coolify is not connected to this Git repository.

The image workflow publishes an immutable release tag and a `sha-<repository commit>` tag. Do not deploy `latest` or a mutable branch tag.

## Operating modes

| Mode | Image/database | Purpose |
| --- | --- | --- |
| `runtime` | Current production versions | Idempotent configuration and normal service startup; never backs up, restores, creates, or migrates a site. |
| `backup` | Existing v15 image + exact current database image | Pauses the site, checks pending jobs and installed apps, then creates and verifies a deterministic database/files/config backup set. |
| `upgrade` | Verified v16 image + MariaDB 11.8 | Requires the matching v15 backup and off-host-copy confirmation, then runs the v16 migration. |
| `restore` | Verified v16 image + MariaDB 11.8 on fresh volumes | Restores a v15 backup set into a new site and immediately migrates it to v16. |
| `rollback` | Exact v15 image + exact pre-upgrade database image on fresh volumes | Restores the v15 backup without applying v16 migrations. |
| `fresh` | Verified v16 image + MariaDB 11.8 on fresh volumes | Creates a new site with ERPNext, HRMS, and Payments. |

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
