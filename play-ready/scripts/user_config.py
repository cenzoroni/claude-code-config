"""Personal details for /play-ready, kept out of per-app configs.

The user config lives at ~/.claude/play-ready.yaml (override with the
PLAY_READY_CONFIG environment variable). A sample with dummy values ships with
the plugin at config/play-ready.sample.yaml. Each app's own settings live in
play-store/config.yaml in the app's repo.

An app config picks a developer profile with `app.developer_profile`; without
one it uses `default`. Any `app.developer_*` field set in the app config wins
over the profile.
"""

import os
from pathlib import Path

import yaml

DEFAULT_PATH = Path.home() / ".claude" / "play-ready.yaml"

# Profile key -> app config key
PROFILE_FIELDS = {
    "name": "developer_name",
    "email": "developer_email",
    "website": "developer_website",
    "phone": "developer_phone",
}


def config_path() -> Path:
    return Path(os.environ.get("PLAY_READY_CONFIG", DEFAULT_PATH)).expanduser()


def load_user_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def developer_profile(user: dict, name: str | None = None) -> dict:
    profiles = user.get("developer_profiles") or {}
    key = name or "default"
    if key not in profiles:
        if name:
            raise SystemExit(f"developer_profile '{name}' not found in {config_path()}")
        return {}
    return profiles[key] or {}


def policy_hosting(user: dict, slug: str) -> dict:
    """Where an app's privacy and data-deletion pages are published, if configured.

    Pages go in <repo>/<dir>/<slug>/ and are served at <base_url>/<slug>/...
    (the site drops the .html extension).
    """
    hosting = user.get("policy_hosting") or {}
    if not hosting.get("base_url"):
        return {}
    base = hosting["base_url"].rstrip("/")
    return {
        "dir": Path(hosting.get("repo", ".")).expanduser() / hosting.get("dir", "") / slug,
        "privacy_url": f"{base}/{slug}/privacy",
        "delete_data_url": f"{base}/{slug}/delete-data",
    }


def apply_user_config(app_config: dict, slug: str | None = None) -> dict:
    """Fill an app config from the user config: missing developer fields, and
    the `hosting` URLs when policy_hosting is set and the app slug is known."""
    user = load_user_config()
    app = app_config.setdefault("app", {})
    profile = developer_profile(user, app.get("developer_profile"))
    for profile_key, app_key in PROFILE_FIELDS.items():
        value = profile.get(profile_key)
        if value and not app.get(app_key):
            app[app_key] = value
    if slug:
        hosting = policy_hosting(user, slug)
        if hosting:
            app_config["hosting"] = {
                "privacy_url": hosting["privacy_url"],
                "delete_data_url": hosting["delete_data_url"],
            }
    return app_config


# Everything /play-ready makes for an app lives in one folder of the app's repo:
#   play-store/config.yaml   the app's settings
#   play-store/guides/       filled-in Play Console answers and guides
#   play-store/pages/        privacy.html and delete-data.html (also published
#                            to the policy_hosting site when configured)
#   play-store/assets/       icon, feature graphic, screenshots
APP_FOLDER = "play-store"
GUIDES = "guides"
PAGES = "pages"
ASSETS = "assets"
CONFIG = "config.yaml"


def app_folder(project: str | Path) -> Path:
    return Path(project).expanduser().resolve() / APP_FOLDER


def project_root(config_path: str | Path) -> Path:
    """The app repo a config belongs to: the parent of play-store/ for the
    current layout, or the config's own directory for an older one."""
    path = Path(config_path).expanduser().resolve()
    return path.parent.parent if path.parent.name == APP_FOLDER else path.parent


def app_slug(app_config: dict, config_path: str | Path) -> str:
    """The app's short name in hosted-page URLs: `app.slug` if set, otherwise
    the name of the app's repo directory."""
    return app_config.get("app", {}).get("slug") or project_root(config_path).name
