# Frappe v16 deployment

A Frappe v16 image and a Compose file to run one site with it, made for
[Coolify](https://coolify.io) but plain Docker Compose otherwise.

The image is Frappe with the apps in [`build/apps.json`](build/apps.json), including
[frappe_restic](https://github.com/grayhatdevelopers/frappe_restic) for backups. It is built
with [frappe_docker](https://github.com/frappe/frappe_docker)'s layered Containerfile, unchanged.

## Layout

| Path | Purpose |
| --- | --- |
| `build/apps.json` | The apps in the image and their versions. |
| `.github/workflows/build-image.yml` | Builds the image and checks its apps and tools when a pull request changes `build/`; a release also publishes it to GHCR. |
| `.github/workflows/lint.yml` | Checks the workflows, scripts and Compose file. |
| `renovate.json` | Keeps Frappe, the apps, frappe_docker and the Compose images current. |
| `compose.yaml` | The deployment. |
| `.env.example` | Its settings. |

## What a deployment does

```text
db, redis → configurator → create-site → site-operation → install-apps → runtime services
```

- **configurator** points the bench at the database and Redis.
- **create-site** creates the site on empty volumes; otherwise it does nothing.
- **site-operation** runs frappe_restic's deploy job: it backs up the site, migrates it and
  records the release. If the migration fails, the site is returned to that backup and the
  deployment stops, so the new image never starts. See
  [frappe_restic's deployment docs](https://github.com/grayhatdevelopers/frappe_restic/blob/main/docs/deployment.md).
- **install-apps** installs any app in the image that the site does not have yet.
- **Runtime services** (backend, websocket, frontend, workers, scheduler) start behind
  frappe_restic's guard, which refuses to start them during a restore.

Stop the runtime services before each deployment; Coolify does this on every deploy.

## Backups

frappe_restic runs scheduled backups and a backup before every deployment. Set
`RESTIC_OFFSITE_BACKUP_ENABLED=1` and the repository settings in `.env.example` to upload
them with Restic. Keep a copy of `RESTIC_PASSWORD` outside the server.

## Restore

1. Set `SITE_OPERATION=restore` and `RESTIC_RESTORE_SNAPSHOT` to a short snapshot ID (or
   `latest`), using the image the snapshot was taken with.
2. Deploy. The site is restored and migrated; a failed restore returns it to where it was.
3. Set `SITE_OPERATION=migrate` again.

Redeploying the same snapshot does nothing. A restore works on empty volumes too.

## Upgrades

- **Apps:** change `build/apps.json` in a pull request; Renovate opens these for new app
  releases. Pull requests build and check the image without publishing it.
- **Frappe v15 to v16:** see [docs/coolify-v15-to-v16.md](docs/coolify-v15-to-v16.md).

## Releases

Pull requests go to `develop` and are squash-merged, so their titles must be
[conventional commits](https://www.conventionalcommits.org). A bot keeps a `develop` → `main`
pull request open; merging it releases `ghcr.io/grayhatdevelopers/frappe-v16:vX.Y.Z` and sets
`APP_IMAGE` in `.env.example` to it. Image tags are never overwritten; deploy by version.
