# Coolify v15 to v16 migration

The rehearsal target is a complete clone of production: copied database and sites data, the same installed apps, and separate container, volume, network, and domain identities. It is not an empty restore target.

## Before changing the clone

1. Record the exact production v15 application image, database image/version, site name, installed apps, and resolved Docker volume names. [`scripts/inspect_live_stack.sh`](../scripts/inspect_live_stack.sh) can collect these without printing secrets.
2. Create and verify one complete off-host production backup containing the database, public files, private files, and site configuration/encryption key.
3. Create the isolated Coolify clone, including copies of the production database and sites data. Confirm that the clone cannot receive production traffic and cannot connect to production volumes or external integrations unintentionally.
4. Confirm the clone works on the original v15 images before upgrading it.

The backup is the recovery copy. It is not restored during the normal clone or production upgrade because both already contain the live site data.

## What one deployment does

The Compose startup order is:

```text
database and Redis
→ configurator
→ create-site
→ install-apps
→ migrate
→ backend, frontend, websocket, workers, and scheduler
```

- `configurator` writes the shared database and Redis settings.
- `create-site` exits immediately when the site directory already exists. It only creates a site for a genuinely empty installation.
- `install-apps` ensures Payments, ERPNext, and HRMS are installed. Existing installed apps are left unchanged.
- `migrate` enables maintenance mode, runs `bench --site <site> migrate`, clears cache, and only then allows runtime services to start. A failed migration leaves maintenance mode and scheduler pause enabled.

No deployment mode or restore flag is involved.

## Upgrade the clone

Keep the clone's copied database and sites volume names. Change its application and database images:

```dotenv
APP_IMAGE=<verified-combined-v16-image-tag-or-digest>
DB_IMAGE=mariadb:11.8
MARIADB_AUTO_UPGRADE=1
```

Deploy once. For an internal database, MariaDB upgrades the copied data volume before the configurator can connect. The one-shot Frappe services then configure, verify/install the required apps, and migrate the copied site using the v16 code baked into `APP_IMAGE`.

Validate login, encrypted credentials and integrations, ERPNext transactions, HRMS, Payments, files, websocket events, scheduler, background jobs, and logs. Keep the clone available as the reference for the production change.

## Upgrade production

Use the exact Compose, application image, database image, and relevant environment values that passed on the clone. Keep the existing production database, sites, logs, and Redis volume names.

Deploy once with:

```dotenv
APP_IMAGE=<same-verified-v16-image-tag-or-digest>
DB_IMAGE=mariadb:11.8
MARIADB_AUTO_UPGRADE=1
```

For an external database, upgrade and validate it separately and leave `MARIADB_AUTO_UPGRADE` empty. After the deployment succeeds, leaving `MARIADB_AUTO_UPGRADE=1` is safe but optional; the MariaDB image checks whether an upgrade is required at startup.

The old v15 deployment mounts a separate generated-assets volume. The v16 image links baked assets into the sites volume, so this Compose intentionally does not mount the legacy assets volume. Keep that old volume until production is confirmed.

## Failure recovery

Do not reconnect v15 containers to a database volume already upgraded by MariaDB or Frappe. Recover the verified off-host backup into fresh v15 volumes and move traffic to that recovery instance.
