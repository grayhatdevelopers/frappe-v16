# Coolify v15 to v16 migration runbook

This runbook assumes the live deployment is a Coolify user-defined Service created from pasted Docker Compose, not an application bound to GitHub.

## Safety model

The production upgrade is deliberately split into two deployments. A backup must be created while both the application and database remain on their exact current versions. The currently deployed Compose declares `mariadb:10.6`, but scales that service with `ENABLE_DB`; confirm the live value and running container before assuming the database is internal. Only after the backup is checksummed and copied off the Docker host may the Compose be redeployed with the v16 image and MariaDB 11.8.

The deployable live Compose contains Coolify's resolved, UUID-prefixed volume names. Copy those exact names into `DB_VOLUME_NAME`, `SITES_VOLUME_NAME`, `LOGS_VOLUME_NAME`, `REDIS_CACHE_VOLUME_NAME`, and `REDIS_QUEUE_VOLUME_NAME` for both production phases. Do not delete and recreate the live Service or substitute newly generated volume names.

The `backups` volume is different: `BACKUP_VOLUME_NAME` gives it an explicit global Docker name. Keep that value unchanged so a separate recovery Service can mount the same backup set.

Before production work:

1. Record the exact current v15 application image, preferably by digest, and the exact MariaDB image.
2. Record every installed Frappe app. Any app installed in the database must also be present and v16-compatible in the new image.
3. Export the current Coolify Compose and environment values through an approved secret-handling path.
4. Confirm sufficient free space for the database dump plus public and private file archives.
5. Build the v16 image with the manual workflow, verify it, and publish an immutable tag.
6. Arrange an off-host destination for the completed backup directory. The named Docker volume protects against an application migration failure, but it is not disaster recovery for loss of the server.
7. Confirm the Coolify destination can authenticate to and pull the private GHCR image before the maintenance window. This does not require changing repository or package visibility.

The read-only helper `scripts/inspect_live_stack.sh BACKEND_CONTAINER [DB_CONTAINER]` collects the unresolved image digest, volume mounts, Bench apps/sites, non-secret database endpoint, and database version without dumping container environment variables.

The live Compose also mounts a separate `assets` volume at `sites/assets`. The v16 custom image carries immutable generated assets in the image and links them into the sites volume at startup, so the new Compose intentionally removes that submount. Do not delete the old `assets` or `redis-socketio-data` volumes until the upgrade and rollback window have closed.

`SITE_NAME` is the existing directory under `sites/` and the Bench site identifier; it is not necessarily the public hostname. The deployable Compose still interpolates this value, so confirm it from the live Coolify environment or sites volume rather than inferring it from `FRAPPE_SITE_NAME_HEADER`.

## Phase A: take the v15 cutover backup

Paste [`compose.yaml`](../compose.yaml) into the existing Coolify Service and set:

```dotenv
APP_IMAGE=<exact-current-v15-image-or-digest>
DB_IMAGE=<exact-current-database-image-or-digest>
MARIADB_AUTO_UPGRADE=
ENABLE_DB=<live-value-0-or-1>
RUNTIME_REPLICAS=0
DEPLOYMENT_MODE=backup
OPERATION_ID=v15-to-v16-20260715-01
MIGRATION_CONFIRMATION=BACKUP_V15_TO_V16
BACKUP_COPY_CONFIRMATION=
SITE_NAME=<current-site-name>
BACKUP_SITE_NAME=
BACKUP_VOLUME_NAME=<stable-global-backup-volume-name>
DB_VOLUME_NAME=<resolved-live-db-volume-name>
SITES_VOLUME_NAME=<resolved-live-sites-volume-name>
LOGS_VOLUME_NAME=<resolved-live-logs-volume-name>
REDIS_CACHE_VOLUME_NAME=<resolved-live-redis-cache-volume-name>
REDIS_QUEUE_VOLUME_NAME=<resolved-live-redis-queue-volume-name>
```

Keep the existing database root password and other site values. Deploy once.

Leave `MARIADB_AUTO_UPGRADE` empty when it is disabled. Do not use the string `0`; the MariaDB image treats a non-empty auto-upgrade variable as enabled.

`RUNTIME_REPLICAS=0` keeps all application runtime containers down throughout the backup cutover. This avoids serving traffic during the consistent backup and avoids reusing the v15-only generated-assets mount. The ordered lifecycle jobs then run the backup:

- enables maintenance mode and pauses the scheduler;
- checks that no pending work blocks migration;
- records Bench versions and installed apps;
- writes `database.sql.gz`, `public-files.tgz`, `private-files.tgz`, and `site-config.json` under `/backups/<site>/<operation-id>/`;
- validates the gzip/tar archives and writes `SHA256SUMS`;
- writes `backup.complete` last.

It intentionally leaves the site in maintenance mode. Do not change the operation ID between Phase A and Phase B.

Copy the entire operation directory off the Docker host, validate `sha256sum -c SHA256SUMS` on the copy, and retain the v15 image reference and Compose configuration with it.

## Recommended rehearsal: restore and migrate on fresh volumes

Before touching the production database engine, create a separate temporary Coolify Service from the same Compose. A new Service is desirable here because it gets fresh ordinary data volumes. Configure it with:

```dotenv
APP_IMAGE=<verified-v16-image-or-digest>
DB_IMAGE=mariadb:11.8
MARIADB_AUTO_UPGRADE=1
ENABLE_DB=1
RUNTIME_REPLICAS=1
DEPLOYMENT_MODE=restore
OPERATION_ID=v15-to-v16-20260715-01
MIGRATION_CONFIRMATION=RESTORE_V15_TO_V16
SITE_NAME=<temporary-target-site-name>
BACKUP_SITE_NAME=<production-source-site-name>
BACKUP_VOLUME_NAME=<same-global-backup-volume-name>
ADMIN_PASSWORD=<temporary-admin-password>
```

The restore mode refuses to operate when the target site directory already exists. It creates a new target site, verifies the backup checksums, restores the database and both file archives, then merges the backed-up site configuration (including its encryption key) while retaining the fresh target database credentials. It then runs the v16 migration. Validate the site and important business workflows before production Phase B.

For this rehearsal, assign deliberate fresh values to all five ordinary `*_VOLUME_NAME` variables. Reuse only `BACKUP_VOLUME_NAME`; never point the rehearsal at a production database or sites volume.

## Phase B: upgrade the existing production volumes

Return to the original Coolify Service. Keep `SITE_NAME`, `OPERATION_ID`, `BACKUP_VOLUME_NAME`, and all ordinary volume keys unchanged. Change only the controlled cutover values:

```dotenv
APP_IMAGE=<verified-v16-image-or-digest>
DB_IMAGE=mariadb:11.8
MARIADB_AUTO_UPGRADE=1
ENABLE_DB=<same-live-value-0-or-1>
RUNTIME_REPLICAS=1
DEPLOYMENT_MODE=upgrade
MIGRATION_CONFIRMATION=UPGRADE_V15_TO_V16
BACKUP_COPY_CONFIRMATION=OFF_HOST_COPY_VERIFIED
```

Deploy once. When `ENABLE_DB=1`, MariaDB's official image performs its major-version system-table upgrade before becoming healthy. When `ENABLE_DB=0`, the external database must be upgraded to and verified on a Frappe-v16-supported release separately before this deployment. The migration job then verifies the v15 backup again, requires the embedded Grayhat v16 image manifest, runs `bench --site <site> migrate`, verifies the required apps, and only then clears scheduler pause and maintenance mode.

If migration fails, the job exits non-zero and leaves the site paused and in maintenance mode. Preserve its logs and do not repeatedly change operation IDs or rerun commands blindly.

## Phase C: normal runtime

After validation, retain the same v16 application and database images and set:

```dotenv
MARIADB_AUTO_UPGRADE=
RUNTIME_REPLICAS=1
DEPLOYMENT_MODE=runtime
MIGRATION_CONFIRMATION=
BACKUP_COPY_CONFIRMATION=
```

Redeploy. Runtime mode performs only the idempotent shared configuration before starting backend, frontend, websocket, workers, and scheduler.

Assign the public domain to the `frontend` service on container port `8080`. No host port mapping or hard-coded Coolify network identifier is required.

## Rollback and recovery

Do not point the v15 application or the pre-upgrade MariaDB image at volumes already upgraded to v16/11.8. Frappe does not support database downgrades, and a partially migrated production volume is not a rollback target.

Create a separate recovery Coolify Service with fresh ordinary volumes, then use:

```dotenv
APP_IMAGE=<exact-v15-image-used-for-the-backup>
DB_IMAGE=<exact-database-image-used-for-the-backup>
MARIADB_AUTO_UPGRADE=
ENABLE_DB=1
RUNTIME_REPLICAS=1
DEPLOYMENT_MODE=rollback
OPERATION_ID=v15-to-v16-20260715-01
MIGRATION_CONFIRMATION=RESTORE_V15_ROLLBACK
SITE_NAME=<rollback-target-site-name>
BACKUP_SITE_NAME=<production-source-site-name>
BACKUP_VOLUME_NAME=<same-global-backup-volume-name>
ADMIN_PASSWORD=<temporary-admin-password>
```

Rollback mode restores the v15 backup and starts the v15 runtime without applying v16 migrations. After validation, move traffic at the proxy/domain layer. Keep the failed production volumes stopped for investigation.

Rollback also requires deliberate fresh values for all five ordinary `*_VOLUME_NAME` variables. Reuse only the backup volume name.

If the Docker host itself is unavailable, first recreate the named backup volume and copy the off-host operation directory back into `<source-site>/<operation-id>/`, preserving `SHA256SUMS` and `backup.complete`.
