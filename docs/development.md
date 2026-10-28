# Development

The image is built with [frappe_docker](https://github.com/frappe/frappe_docker)'s layered
Containerfile, unchanged. `build/Containerfile` then adds `/home/frappe/source-commit`, the
revision frappe_restic tags backups and restores with: the Git tree of `build/`
(`git rev-parse <commit>:build`), whose first 12 characters name the image
(`frappe-v16:build-<tree>`). A release re-tags that image, so its backups show the same
revision under every tag; `git log --find-object=<tree> -- build` finds the commit that
introduced it.

## Layout

| Path | Purpose |
| --- | --- |
| `build/apps.json` | The apps in the image and their versions. |
| `build/frappe.env` | The Frappe release and frappe_docker commit the image is built from. |
| `build/Containerfile` | Records the image's revision for frappe_restic. |
| `.github/workflows/build-image.yml` | Builds and checks the image once per change to `build/`, then deploys and redeploys it with Compose. |
| `scripts/image_ref.sh` | Names the image after the files it is built from. |
| `.github/workflows/lint.yml` | Checks the workflows, scripts and Compose file. |
| `renovate.json` | Keeps Frappe, the apps, frappe_docker and the Compose images current. |
| `compose.yaml` | The deployment. |
| `.env.example` | Its settings. |

## Changing Frappe or an app

Change `build/frappe.env` or `build/apps.json` in a pull request. The pull request builds and
tests the image.

## Releases

Pull requests go to `develop` and are squash-merged, so their titles must be
[conventional commits](https://www.conventionalcommits.org). A bot keeps a `develop` → `main`
pull request open; merging it tags the image `develop` built and tested as
`ghcr.io/grayhatdevelopers/frappe-v16:vX.Y.Z` and sets `APP_IMAGE` in `.env.example` to it.
`:latest` follows the newest release and `:develop` follows `develop` for testing. Version tags
are never overwritten; deploy by version.
