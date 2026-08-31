# Frappe v16 deployment

This repository provides a compact deployment layout and build workflow for a Frappe v16 combined image (ERPNext, HRMS, Payments). It is intentionally a small, focused deployment repository and not a full fork of `frappe_docker`.

## Repository contract

- `build/apps.json` is the single source of app refs used by the image build.
- `.github/workflows/build-image.yml` (if present) is intended for manual image publishing: it pins the builder, uses the upstream layered Containerfile without modification, validates apps, and publishes only when explicitly requested.
- `compose.yaml` is a pull-only deployment manifest designed to be used with a container orchestration platform or deployment service. It defines the normal runtime services and separate opt-in maintenance jobs (backup, restore, restore-db).

The image workflow publishes immutable release tags. Avoid deploying the `latest` or mutable branch tags in production.

## Deployment sequence

Typical deploys perform these steps:

- Run the one-shot configurator to prepare the environment.
- Create a site only when the sites volume is empty; otherwise reuse existing sites.
- Install required apps (ERPNext, HRMS, Payments as configured) and run migrations before starting runtime services.

For major-version upgrades (for example v15→v16), test against an isolated copy of production data before rolling the image into a live environment.

## Backup and restore

The Compose manifest includes optional maintenance jobs: `backup`, `restore`, and `restore-db`. They are disabled by default and only run when the corresponding environment flags are enabled.

- Enabling backup runs Frappe's backup command and persists site data with an external snapshot tool (for example Restic).
- Enabling restore will restore a site snapshot into the sites volume.

Refer to your deployment platform's runbook before changing live Services or automation.

You can use `scripts/inspect_live_stack.sh` to inspect running containers and their metadata; adapt its usage to your environment.

## Authoritative references

- https://github.com/frappe/frappe_docker
- https://docs.frappe.io/framework/user/en/bench/reference/backup
- https://docs.frappe.io/framework/user/en/bench/reference/restore
- https://github.com/frappe/frappe/wiki/Migrating-to-version-16
- https://github.com/frappe/erpnext/wiki/Migration-Guide-To-ERPNext-Version-16
- https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/platform-specific-upgrade-guides/upgrading-between-major-mariadb-versions
