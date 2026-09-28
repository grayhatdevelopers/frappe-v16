# Coolify v15 to v16 migration

Rehearse on a complete clone of production first: copied database and sites data, the same
installed apps, and its own containers, volumes, network and domain.

## Before changing the clone

1. Record the production v15 application image, database version, site name, installed apps
   and Docker volume names. [`scripts/inspect_live_stack.sh`](../scripts/inspect_live_stack.sh)
   collects these without printing secrets.
2. Take and verify one complete off-host backup of production: database, public and private
   files, and site configuration with its encryption key.
3. Create the clone in Coolify with copies of the production database and sites data. Make
   sure it cannot receive production traffic, touch production volumes or reach external
   integrations by accident.
4. Confirm the clone works on the v15 images before upgrading it.

## Upgrade the clone

Keep the clone's volumes and deploy this Compose with the v16 image:

```dotenv
APP_IMAGE=<verified v16 image tag>
MARIADB_AUTO_UPGRADE=1
```

MariaDB upgrades the copied data volume on startup. The deployment then backs up the site,
migrates it with the v16 code and installs any app the site lacks. If the migration fails,
the site is returned to that backup and v16 does not start.

Validate login, encrypted credentials and integrations, ERPNext transactions, HRMS,
Payments, files, websocket events, the scheduler, background jobs and logs.

## Upgrade production

Use the exact Compose, image and settings that passed on the clone, and keep the production
database, sites and logs volumes. Deploy once.

For an external database (`ENABLE_DB=0`), upgrade and validate it separately and leave
`MARIADB_AUTO_UPGRADE` empty.

The v15 deployment mounted a separate assets volume. The v16 image links its built assets
into the sites volume instead, so this Compose does not mount it. Keep the old volume until
production is confirmed.

## If it goes wrong

Do not reconnect v15 containers to a database that MariaDB or Frappe has already upgraded.
Restore the verified backup into fresh v15 volumes and move traffic to that instance.
