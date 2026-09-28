#!/usr/bin/env python3
"""Bring an app's /play-ready files into the current layout.

Everything for an app belongs in <project>/play-store/ (see user_config.py).
Earlier versions scattered it: a config in ~/templates/play-store/config/ or at
<project>/play-store.yaml, assets in store_assets/, guides in
docs/plans/play-store/ or ~/plans/<app>/play-store/, and developer details
copied into every app config.

Safe to run any number of times: it only acts on what's still in an old place.
Dry run by default; pass --apply to make the changes. Tracked files are moved
with `git mv` so history follows them. Pages still served by the app's own
hosting are reported, never moved, because moving them would break live URLs.

    pipenv run python migrate.py ~/repos/my-app            # show what would change
    pipenv run python migrate.py ~/repos/my-app --apply    # do it
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from user_config import (
    ASSETS,
    CONFIG,
    GUIDES,
    PAGES,
    PROFILE_FIELDS,
    app_folder,
    developer_profile,
    load_user_config,
)

# Old generated file name -> where it belongs now, relative to play-store/
GENERATED = {
    "privacy-policy.html": f"{PAGES}/privacy.html",
    "data-deletion.html": f"{PAGES}/delete-data.html",
    "data-safety-answers.md": f"{GUIDES}/data-safety-answers.md",
    "content-rating-answers.md": f"{GUIDES}/content-rating-answers.md",
    "store-listing-guide.md": f"{GUIDES}/store-listing-guide.md",
    "play-console-walkthrough.md": f"{GUIDES}/play-console-walkthrough.md",
}


class Migration:
    def __init__(self, project: Path, apply: bool):
        self.project = project
        self.folder = app_folder(project)
        self.apply = apply
        self.actions: list[str] = []
        self.notes: list[str] = []

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project))
        except ValueError:
            return str(path).replace(str(Path.home()), "~", 1)

    def tracked(self, path: Path) -> bool:
        return subprocess.run(
            ["git", "-C", str(self.project), "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
        ).returncode == 0

    def move(self, src: Path, dst: Path) -> None:
        if dst.exists():
            self.notes.append(f"Both {self.rel(src)} and {self.rel(dst)} exist; kept both. Remove the old one by hand.")
            return
        self.actions.append(f"move {self.rel(src)} -> {self.rel(dst)}")
        if not self.apply:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        src = src.resolve()  # ~/plans/<app> may be a symlink into the repo
        inside_repo = self.project in src.parents
        if inside_repo and self.tracked(src):
            subprocess.run(["git", "-C", str(self.project), "mv", str(src), str(dst)], check=True)
        else:
            shutil.move(str(src), str(dst))

    def move_tree(self, src_dir: Path, dst_dir: Path) -> None:
        for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
            self.move(src, dst_dir / src.relative_to(src_dir))
        if self.apply:
            remove_empty_dirs(src_dir)

    # --- steps -----------------------------------------------------------

    def config(self) -> None:
        target = self.folder / CONFIG
        slug = self.project.name
        candidates = [
            self.project / "play-store.yaml",
            self.project / "play-store.draft.yaml",
            Path.home() / "templates" / "play-store" / "config" / f"{slug}.yaml",
        ]
        for src in candidates:
            if not src.exists():
                continue
            dst = target if not src.name.endswith(".draft.yaml") else self.folder / "config.draft.yaml"
            self.move(src, dst)

    def developer_fields(self) -> None:
        """Drop developer fields that only repeat the user config's profile."""
        target = self.folder / CONFIG
        path = target if target.exists() else self.project / "play-store.yaml"
        if not path.exists():
            return
        text = path.read_text()
        app = (yaml.safe_load(text) or {}).get("app", {})
        profile = developer_profile(load_user_config(), app.get("developer_profile"))
        redundant = [
            key for pkey, key in PROFILE_FIELDS.items()
            if key in app and profile.get(pkey) and str(app[key]) == str(profile[pkey])
        ]
        if not redundant:
            return
        self.actions.append(f"remove {', '.join(redundant)} from {self.rel(path)} (same as the user config profile)")
        if self.apply:
            lines = [l for l in text.splitlines(True) if not any(l.lstrip().startswith(f"{k}:") for k in redundant)]
            path.write_text("".join(lines))

    def assets(self) -> None:
        old = self.project / "store_assets"
        if old.is_dir():
            self.move_tree(old, self.folder / ASSETS)

    def guides(self) -> None:
        dirs = [
            self.project / "docs" / "plans" / "play-store",
            self.project / "docs" / "plans" / "completed" / "play-store",
            Path.home() / "plans" / self.project.name / "play-store",
            Path.home() / "plans" / self.project.name / "completed" / "play-store",
        ]
        seen = set()
        for d in dirs:
            if not d.is_dir() or d.resolve() in seen:
                continue
            # ~/plans/<app> can be a symlink into some repo; only follow it into this one
            if (Path.home() / "repos") in d.resolve().parents and self.project not in d.resolve().parents:
                continue
            seen.add(d.resolve())
            for src in sorted(p for p in d.iterdir() if p.is_file()):
                dst = self.folder / GENERATED.get(src.name, f"{GUIDES}/{src.name}")
                self.move(src, dst)
            if self.apply:
                remove_empty_dirs(d)

    def served_pages(self) -> None:
        """Old pages the app's own hosting may still serve: report only."""
        for rel in ("privacy-policy.html", "privacy_policy.html", "PRIVACY_POLICY.md",
                    "public/delete-data.html", "public/delete-account.html", "public/privacy-policy.html"):
            path = self.project / rel
            if path.exists():
                self.notes.append(
                    f"{rel} may still be served at its old URL. Keep it until Play Console points at the "
                    f"new policy URLs, then delete it."
                )

    def run(self) -> None:
        self.config()
        self.developer_fields()
        self.assets()
        self.guides()
        self.served_pages()


def remove_empty_dirs(root: Path) -> None:
    if not root.is_dir():
        return
    for d in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    if not any(root.iterdir()):
        root.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser(description="Move an app's /play-ready files into <project>/play-store/")
    parser.add_argument("project", help="Path to the app repo")
    parser.add_argument("--apply", action="store_true", help="Make the changes (default: dry run)")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        sys.exit(f"Not a directory: {project}")

    m = Migration(project, args.apply)
    m.run()

    if not m.actions and not m.notes:
        print(f"{project.name}: already in the current layout.")
        return
    verb = "Done" if args.apply else "Would do (dry run; pass --apply)"
    if m.actions:
        print(f"{project.name}: {verb}:")
        for a in m.actions:
            print(f"  - {a}")
    for n in m.notes:
        print(f"  ! {n}")


if __name__ == "__main__":
    main()
