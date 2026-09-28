#!/usr/bin/env python3
"""Render Jinja2 templates using a per-app YAML config."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

from user_config import (
    GUIDES,
    PAGES,
    app_folder,
    app_slug,
    apply_user_config,
    load_user_config,
    policy_hosting,
    project_root,
)
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
ALL_TEMPLATES = [
    "privacy-policy.html.j2",
    "data-deletion.html.j2",
    "data-safety-answers.md.j2",
    "content-rating-answers.md.j2",
    "store-listing-guide.md.j2",
    "play-console-walkthrough.md.j2",
]

# Pages published to the policy_hosting site: template -> file name
HOSTED_PAGES = {
    "privacy-policy.html.j2": "privacy.html",
    "data-deletion.html.j2": "delete-data.html",
}


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return apply_user_config(config, slug=app_slug(config, config_path))


def render_template(env: Environment, template_name: str, context: dict) -> str:
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


def output_name(template_name: str) -> str:
    return template_name.replace(".j2", "")


def main():
    parser = argparse.ArgumentParser(description="Render Play Store templates from app config")
    parser.add_argument("--config", required=True, help="Path to the app's play-store/config.yaml")
    parser.add_argument("--template", help="Single template name to render (e.g. privacy-policy.html.j2)")
    parser.add_argument("--all", action="store_true", help="Render all templates")
    parser.add_argument(
        "--output",
        help="Output file (single template) or directory (--all). "
             "Default for --all: the app's play-store/ folder (guides/ and pages/)",
    )
    parser.add_argument(
        "--hosted", action="store_true",
        help="Render the privacy and data-deletion pages into the policy_hosting site from the user config",
    )
    args = parser.parse_args()

    if not args.template and not args.all and not args.hosted:
        parser.error("Specify --template <name>, --all or --hosted")

    config = load_config(args.config)
    config["current_date"] = datetime.now().strftime("%B %Y")
    config.setdefault("firebase", {})  # templates check firebase.* even for apps without it

    perms = [p.lower() for p in config.get("permissions", [])]
    config["has_location"] = any("location" in p for p in perms)
    config["has_camera"] = any("camera" in p for p in perms)
    config["has_photos"] = any(
        d.get("type") in ("photos", "photos_and_videos") for d in config.get("data_collected", [])
    )
    config["data_types"] = [d.get("type") for d in config.get("data_collected", [])]

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )

    if args.hosted and not args.all:
        publish_pages(env, config, args.config)
        return

    templates = ALL_TEMPLATES if args.all else [args.template]

    for tmpl_name in templates:
        if not (TEMPLATES_DIR / tmpl_name).exists():
            print(f"WARNING: template {tmpl_name} not found, skipping", file=sys.stderr)
            continue

        rendered = render_template(env, tmpl_name, config)

        if args.all and not args.output:
            folder = app_folder(project_root(args.config))
            if tmpl_name in HOSTED_PAGES:
                out_path = folder / PAGES / HOSTED_PAGES[tmpl_name]
            else:
                out_path = folder / GUIDES / output_name(tmpl_name)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        elif args.all:
            out_dir = Path(args.output)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / output_name(tmpl_name)
        elif args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            print(rendered)
            continue

        out_path.write_text(rendered)
        print(f"Rendered: {out_path}")

    # A full render into the app folder also publishes the pages when a site is configured
    if args.all and not args.output and (args.hosted or policy_hosting(load_user_config(), app_slug(config, args.config))):
        publish_pages(env, config, args.config)


def publish_pages(env: Environment, config: dict, config_path: str) -> None:
    """Render the privacy and data-deletion pages into the policy_hosting site."""
    hosting = policy_hosting(load_user_config(), app_slug(config, config_path))
    if not hosting:
        sys.exit("No policy_hosting in the user config (~/.claude/play-ready.yaml)")
    hosting["dir"].mkdir(parents=True, exist_ok=True)
    for tmpl_name, page in HOSTED_PAGES.items():
        out_path = hosting["dir"] / page
        out_path.write_text(render_template(env, tmpl_name, config))
        print(f"Published: {out_path}")
    print(f"Privacy policy URL: {config['hosting']['privacy_url']}")
    print(f"Data deletion URL:  {config['hosting']['delete_data_url']}")


if __name__ == "__main__":
    main()
