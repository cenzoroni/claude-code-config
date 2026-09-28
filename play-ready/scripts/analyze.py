#!/usr/bin/env python3
"""Static analysis of a Flutter project for Play Store readiness.

Analyzes a Flutter project's dependencies, configuration, and artifacts to
produce a draft Play Store config YAML and a readiness checklist.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from user_config import developer_profile, load_user_config
from tabulate import tabulate

# ---------------------------------------------------------------------------
# Dependency → service/capability mapping (Appendix C)
# ---------------------------------------------------------------------------
DEPENDENCY_MAP = {
    "firebase_core": {
        "firebase_services": ["core"],
    },
    "firebase_auth": {
        "firebase_services": ["auth"],
        "data_collected": [
            {"type": "email_address", "purpose": "account_management", "required": True,
             "shared_with_third_parties": False, "user_deletable": True},
        ],
    },
    "cloud_firestore": {
        "firebase_services": ["firestore"],
        "data_collected": [
            {"type": "app_interactions", "purpose": "app_functionality", "required": True,
             "shared_with_third_parties": False, "user_deletable": True},
        ],
    },
    "firebase_storage": {
        "firebase_services": ["storage"],
    },
    "firebase_analytics": {
        "firebase_services": ["analytics"],
        "data_collected": [
            {"type": "app_info_performance", "purpose": "analytics", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
            {"type": "device_ids", "purpose": "analytics", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
        ],
    },
    "firebase_crashlytics": {
        "firebase_services": ["crashlytics"],
        "data_collected": [
            {"type": "crash_logs", "purpose": "analytics", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
        ],
    },
    "firebase_messaging": {
        "firebase_services": ["messaging"],
        "data_collected": [
            {"type": "device_ids", "purpose": "app_functionality", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
        ],
    },
    "google_sign_in": {
        "auth_methods": ["google"],
        "data_collected": [
            {"type": "name", "purpose": "account_management", "required": False,
             "shared_with_third_parties": False, "user_deletable": True},
        ],
    },
    "sign_in_with_apple": {
        "auth_methods": ["apple"],
    },
    "google_mobile_ads": {
        "flags": {"contains_ads": True},
        "data_collected": [
            {"type": "device_ids", "purpose": "advertising", "required": True,
             "shared_with_third_parties": True, "user_deletable": False},
            {"type": "app_info_performance", "purpose": "advertising", "required": True,
             "shared_with_third_parties": True, "user_deletable": False},
        ],
    },
    "in_app_purchase": {
        "flags": {"in_app_purchases": True},
        "content_rating": {"digital_purchases": True},
    },
    "geolocator": {
        "permissions": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"],
        "content_rating": {"shares_location": "maybe"},
        "data_collected": [
            {"type": "precise_location", "purpose": "app_functionality", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
        ],
    },
    "location": {
        "permissions": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"],
        "content_rating": {"shares_location": "maybe"},
        "data_collected": [
            {"type": "precise_location", "purpose": "app_functionality", "required": True,
             "shared_with_third_parties": False, "user_deletable": False},
        ],
    },
    "camera": {
        "permissions": ["CAMERA"],
    },
    "image_picker": {
        "permissions": ["CAMERA"],
    },
    "url_launcher": {
        "content_rating": {"unrestricted_web": "maybe"},
    },
}

# Auth patterns to grep for in Dart source
AUTH_PATTERNS = {
    "email": [r"signInWithEmailAndPassword", r"createUserWithEmailAndPassword"],
    "google": [r"GoogleSignIn", r"signInWithGoogle"],
    "apple": [r"signInWithApple", r"SignInWithApple"],
    "phone": [r"PhoneAuthProvider", r"verifyPhoneNumber"],
}


def parse_pubspec(project: Path) -> dict:
    """Extract name, version, and dependencies from pubspec.yaml."""
    pubspec_path = project / "pubspec.yaml"
    if not pubspec_path.exists():
        return {}
    with open(pubspec_path) as f:
        data = yaml.safe_load(f) or {}
    deps = {}
    for key in ("dependencies", "dev_dependencies"):
        section = data.get(key, {}) or {}
        for dep_name in section:
            if dep_name in ("flutter", "flutter_test", "flutter_localizations",
                            "integration_test"):
                continue
            deps[dep_name] = True

    icon_config = data.get("flutter_launcher_icons", {}) or {}
    icon_path = icon_config.get("image_path")

    return {
        "name": data.get("name", "unknown"),
        "version": data.get("version", "1.0.0+1"),
        "dependencies": list(deps.keys()),
        "icon_path": icon_path,
    }


def map_dependencies(deps: list[str]) -> dict:
    """Map pubspec dependencies to Firebase services, auth methods, etc."""
    result = {
        "firebase_services": set(),
        "auth_methods": set(),
        "permissions": set(),
        "data_collected": [],
        "flags": {},
        "content_rating_overrides": {},
    }
    seen_data_types = set()
    for dep in deps:
        mapping = DEPENDENCY_MAP.get(dep)
        if not mapping:
            continue
        for svc in mapping.get("firebase_services", []):
            result["firebase_services"].add(svc)
        for method in mapping.get("auth_methods", []):
            result["auth_methods"].add(method)
        for perm in mapping.get("permissions", []):
            result["permissions"].add(perm)
        for entry in mapping.get("data_collected", []):
            key = (entry["type"], entry["purpose"])
            if key not in seen_data_types:
                seen_data_types.add(key)
                result["data_collected"].append(entry)
        result["flags"].update(mapping.get("flags", {}))
        result["content_rating_overrides"].update(mapping.get("content_rating", {}))

    result["firebase_services"] = sorted(result["firebase_services"])
    result["auth_methods"] = sorted(result["auth_methods"])
    result["permissions"] = sorted(result["permissions"])
    return result


def parse_manifest(project: Path) -> list[str]:
    """Extract declared permissions from AndroidManifest.xml."""
    manifest = project / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if not manifest.exists():
        return []
    text = manifest.read_text()
    return re.findall(r'android\.permission\.(\w+)', text)


def parse_build_gradle(project: Path) -> dict:
    """Extract applicationId, signing, minify settings from build.gradle."""
    for name in ("build.gradle.kts", "build.gradle"):
        path = project / "android" / "app" / name
        if path.exists():
            text = path.read_text()
            break
    else:
        return {}

    result = {}

    app_id = re.search(r'applicationId\s*=?\s*"([^"]+)"', text)
    if app_id:
        result["application_id"] = app_id.group(1)

    result["has_signing_config"] = bool(
        re.search(r'signingConfigs\s*\{', text) or
        re.search(r'signingConfigs\.create', text)
    )
    result["is_minify_enabled"] = bool(
        re.search(r'isMinifyEnabled\s*=\s*true', text) or
        re.search(r'minifyEnabled\s+true', text)
    )
    result["is_shrink_resources"] = bool(
        re.search(r'isShrinkResources\s*=\s*true', text) or
        re.search(r'shrinkResources\s+true', text)
    )
    result["has_proguard_ref"] = bool(
        re.search(r'proguardFiles', text) or
        re.search(r'proguard-rules', text)
    )

    return result


def detect_auth_methods(project: Path) -> list[str]:
    """Grep lib/ for auth method usage patterns."""
    lib_dir = project / "lib"
    if not lib_dir.exists():
        return []
    methods = set()
    for dart_file in lib_dir.rglob("*.dart"):
        try:
            text = dart_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for method, patterns in AUTH_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    methods.add(method)
    return sorted(methods)


def detect_firebase_project(project: Path) -> str | None:
    """Parse .firebaserc or firebase.json for the Firebase project ID."""
    firebaserc = project / ".firebaserc"
    if firebaserc.exists():
        try:
            data = json.loads(firebaserc.read_text())
            projects = data.get("projects", {})
            return projects.get("default")
        except (json.JSONDecodeError, KeyError):
            pass

    firebase_json = project / "firebase.json"
    if firebase_json.exists():
        try:
            data = json.loads(firebase_json.read_text())
            # Try to extract from flutter platforms config
            flutter_cfg = data.get("flutter", {}).get("platforms", {})
            for platform in flutter_cfg.values():
                if isinstance(platform, dict):
                    default = platform.get("default", {})
                    pid = default.get("projectId")
                    if pid:
                        return pid
                    for key, val in platform.items():
                        if isinstance(val, dict) and "projectId" in val:
                            return val["projectId"]
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def lint_firestore_rules(project: Path) -> dict:
    """Check firestore.rules for existence and overly permissive patterns."""
    rules_path = project / "firestore.rules"
    result = {"exists": rules_path.exists(), "warnings": []}
    if not result["exists"]:
        return result

    text = rules_path.read_text()
    if re.search(r'allow\s+write\s*:\s*if\s+true', text):
        result["warnings"].append("Overly permissive: 'allow write: if true' found")
    if re.search(r'allow\s+read\s*,\s*write\s*:\s*if\s+request\.auth\s*!=\s*null\s*;', text):
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.search(r'allow\s+read\s*,\s*write\s*:\s*if\s+request\.auth\s*!=\s*null', line):
                context_start = max(0, i - 3)
                context = "\n".join(lines[context_start:i + 1])
                if not re.search(r'match\s+/users/\{userId\}', context):
                    result["warnings"].append(
                        f"Line {i + 1}: 'allow read, write: if request.auth != null' "
                        "without uid constraint"
                    )

    return result


def check_existing_artifacts(project: Path) -> dict:
    """Check for existing Play Store preparation artifacts."""
    checks = {
        "privacy_policy": False,
        "privacy_policy_path": None,
        "data_deletion_page": False,
        "data_deletion_path": None,
        "key_properties": (project / "android" / "key.properties").exists(),
        "keystore": (project / "android" / "key.jks").exists(),
        "proguard": (project / "android" / "app" / "proguard-rules.pro").exists(),
    }

    for name in ("privacy-policy.html", "privacy_policy.html", "PRIVACY_POLICY.md"):
        path = project / name
        if path.exists():
            checks["privacy_policy"] = True
            checks["privacy_policy_path"] = str(path.relative_to(project))
            break

    for subdir in ("public", "web", "."):
        for name in ("delete-data.html", "delete-account.html", "data-deletion.html"):
            path = project / subdir / name
            if path.exists():
                checks["data_deletion_page"] = True
                checks["data_deletion_path"] = str(path.relative_to(project))
                break
        if checks["data_deletion_page"]:
            break

    return checks


def enumerate_screens(project: Path) -> list[str]:
    """Find all *_screen.dart and *_page.dart files in lib/."""
    lib_dir = project / "lib"
    if not lib_dir.exists():
        return []
    screens = []
    for pattern in ("**/*_screen.dart", "**/*_page.dart"):
        for path in sorted(lib_dir.glob(pattern)):
            name = path.stem
            readable = name.replace("_screen", "").replace("_page", "")
            readable = readable.replace("_", " ").title()
            screens.append(readable)
    return screens


def detect_icon(project: Path, pubspec_icon: str | None) -> dict:
    """Detect app icon and its resolution."""
    result = {"exists": False, "path": None, "width": None, "height": None}

    candidates = []
    if pubspec_icon:
        candidates.append(project / pubspec_icon)
    candidates.extend([
        project / "assets" / "icon" / "icon.png",
        project / "assets" / "icon.png",
        project / "res" / "icon.png",
    ])

    for path in candidates:
        if path.exists():
            result["exists"] = True
            result["path"] = str(path.relative_to(project))
            try:
                import subprocess
                out = subprocess.run(
                    ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                    capture_output=True, text=True, timeout=5,
                )
                for line in out.stdout.splitlines():
                    if "pixelWidth" in line:
                        result["width"] = int(line.split(":")[-1].strip())
                    if "pixelHeight" in line:
                        result["height"] = int(line.split(":")[-1].strip())
            except Exception:
                pass
            break

    return result


def build_config(project: Path) -> dict:
    """Assemble a complete draft config from analysis."""
    pubspec = parse_pubspec(project)
    dep_map = map_dependencies(pubspec.get("dependencies", []))
    manifest_perms = parse_manifest(project)
    gradle = parse_build_gradle(project)
    auth_methods_from_code = detect_auth_methods(project)
    firebase_project = detect_firebase_project(project)
    rules = lint_firestore_rules(project)
    artifacts = check_existing_artifacts(project)
    screens = enumerate_screens(project)
    icon = detect_icon(project, pubspec.get("icon_path"))

    all_auth = sorted(set(dep_map["auth_methods"]) | set(auth_methods_from_code))
    if "email" not in all_auth and "auth" in dep_map["firebase_services"]:
        all_auth = ["email"] + all_auth

    all_perms = sorted(set(dep_map["permissions"]) | set(manifest_perms))
    if "INTERNET" not in all_perms:
        all_perms.append("INTERNET")
        all_perms.sort()

    app_name = pubspec.get("name", "unknown").replace("_", " ").title()
    profile = developer_profile(load_user_config())

    config = {
        "app": {
            "name": app_name,
            "application_id": gradle.get("application_id", "com.example.app"),
            "repo": str(project),
            "description_short": "CHANGEME (80 chars max)",
            "description_long": "CHANGEME (4000 chars max)",
            "category": "CHANGEME",
            "target_audience": "general",
            "contains_ads": dep_map["flags"].get("contains_ads", False),
            "in_app_purchases": dep_map["flags"].get("in_app_purchases", False),
        },
        "permissions": all_perms,
        "content_rating": {
            "violence": "none",
            "sexual_content": "none",
            "profanity": "none",
            "controlled_substances": "none",
            "user_interaction": len(all_auth) > 0 and "firestore" in dep_map["firebase_services"],
            "shares_location": dep_map["content_rating_overrides"].get("shares_location", False),
            "allows_user_generated_content": False,
            "digital_purchases": dep_map["content_rating_overrides"].get("digital_purchases", False),
        },
        "signing": {
            "keystore_path": "android/key.jks",
            "key_alias": pubspec.get("name", "upload").replace("_", "").replace("-", "").lower(),
        },
    }

    # Developer details come from the user config (~/.claude/play-ready.yaml)
    # at render time. Only draft placeholders when there's no profile to use.
    if not profile:
        config["app"]["developer_name"] = "CHANGEME"
        config["app"]["developer_email"] = "CHANGEME@example.com"

    if dep_map["firebase_services"]:
        config["firebase"] = {
            "project_id": firebase_project or "CHANGEME",
            "services": dep_map["firebase_services"],
            "auth_methods": all_auth,
            "has_security_rules": rules["exists"],
            "rules_file": "firestore.rules" if rules["exists"] else None,
        }

    if dep_map["data_collected"]:
        config["data_collected"] = dep_map["data_collected"]

    if icon["exists"]:
        config["store_assets"] = {"icon_source": icon["path"]}

    config["_analysis"] = {
        "screens": screens,
        "gradle": {
            "has_signing_config": gradle.get("has_signing_config", False),
            "is_minify_enabled": gradle.get("is_minify_enabled", False),
            "is_shrink_resources": gradle.get("is_shrink_resources", False),
            "has_proguard_ref": gradle.get("has_proguard_ref", False),
        },
        "artifacts": artifacts,
        "rules_warnings": rules.get("warnings", []),
    }

    return config


def build_checklist(config: dict, project: Path) -> list[tuple[str, str]]:
    """Build a readiness checklist from the analyzed config."""
    analysis = config.get("_analysis", {})
    gradle = analysis.get("gradle", {})
    artifacts = analysis.get("artifacts", {})
    rules_warnings = analysis.get("rules_warnings", [])

    items = []

    app_id = config["app"]["application_id"]
    if app_id and app_id != "com.example.app":
        items.append(("[x]", f"applicationId set ({app_id})"))
    else:
        items.append(("[ ]", "applicationId not detected"))

    version = config["app"].get("_version", "")
    # Grab version from the pubspec path stored during analysis
    items.append(("[x]", f"Version set ({config.get('_version', 'unknown')})"))

    if artifacts.get("keystore"):
        items.append(("[x]", "Upload keystore exists"))
    else:
        items.append(("[ ]", "Upload keystore missing"))

    if artifacts.get("key_properties"):
        items.append(("[x]", "key.properties exists"))
    else:
        items.append(("[ ]", "key.properties missing"))

    if gradle.get("has_signing_config"):
        items.append(("[x]", "Release signing configured"))
    else:
        items.append(("[ ]", "Release signing not configured"))

    if "INTERNET" in config.get("permissions", []):
        items.append(("[x]", "INTERNET permission declared"))
    else:
        items.append(("[ ]", "INTERNET permission missing"))

    if gradle.get("is_minify_enabled"):
        items.append(("[x]", "R8/minification enabled"))
    else:
        items.append(("[ ]", "R8/minification not enabled"))

    if gradle.get("is_shrink_resources"):
        items.append(("[x]", "Resource shrinking enabled"))
    else:
        items.append(("[ ]", "Resource shrinking not enabled"))

    if artifacts.get("proguard"):
        items.append(("[x]", "ProGuard rules exist"))
    else:
        items.append(("[ ]", "ProGuard rules missing"))

    if gradle.get("has_proguard_ref"):
        items.append(("[x]", "ProGuard referenced in build.gradle"))
    else:
        items.append(("[ ]", "ProGuard not referenced in build.gradle"))

    if artifacts.get("privacy_policy"):
        items.append(("[x]", f"Privacy policy exists ({artifacts['privacy_policy_path']})"))
    else:
        items.append(("[ ]", "Privacy policy missing"))

    if artifacts.get("data_deletion_page"):
        items.append(("[x]", f"Data deletion page exists ({artifacts['data_deletion_path']})"))
    else:
        items.append(("[ ]", "Data deletion page missing"))

    firebase = config.get("firebase", {})
    if firebase.get("has_security_rules"):
        if not rules_warnings:
            items.append(("[x]", "Firestore rules exist (no warnings)"))
        else:
            items.append(("[!]", f"Firestore rules exist but have warnings:"))
            for w in rules_warnings:
                items.append(("   ", f"  - {w}"))
    elif firebase.get("services") and "firestore" in firebase["services"]:
        items.append(("[ ]", "Firestore rules missing"))

    icon_assets = config.get("store_assets", {})
    if icon_assets.get("icon_source"):
        items.append(("[x]", f"App icon found ({icon_assets['icon_source']})"))
    else:
        items.append(("[ ]", "App icon not found"))

    fg_path = project / "store_assets" / "feature_graphic.png"
    if fg_path.exists():
        items.append(("[x]", f"Feature graphic exists ({fg_path.relative_to(project)})"))
    else:
        items.append(("[ ]", "Feature graphic missing (1024x500) — run generate_assets.py feature"))

    ss_dir = project / "store_assets" / "screenshots"
    if ss_dir.exists():
        pngs = list(ss_dir.glob("*.png"))
        if len(pngs) >= 2:
            items.append(("[x]", f"Screenshots exist ({len(pngs)} in {ss_dir.relative_to(project)})"))
        elif pngs:
            items.append(("[!]", f"Only {len(pngs)} screenshot(s) — need at least 2"))
        else:
            items.append(("[ ]", "Screenshots dir empty — run generate_assets.py screenshots"))
    else:
        items.append(("[ ]", "Screenshots missing — run generate_assets.py screenshots"))

    return items


def print_checklist(app_name: str, items: list[tuple[str, str]]) -> None:
    """Print the readiness checklist."""
    header = f"Play Store Readiness — {app_name}"
    print(f"\n{header}")
    print("=" * len(header))
    print(
        tabulate(
            items,
            tablefmt="simple_grid",
            colalign=("left", "left"),
        )
    )

    done = sum(1 for status, _ in items if status == "[x]")
    total = sum(1 for status, _ in items if status in ("[x]", "[ ]"))
    print(f"\n{done}/{total} items complete\n")


def write_config(config: dict, output_path: Path) -> None:
    """Write the draft config YAML, stripping internal analysis keys."""
    clean = {k: v for k, v in config.items() if not k.startswith("_")}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("# Play Store config — auto-generated by analyze.py\n")
        f.write("# Review and fill in CHANGEME values before running /play-ready\n\n")
        yaml.dump(clean, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Config written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a Flutter project for Play Store readiness",
    )
    parser.add_argument("project", help="Path to the Flutter project root")
    parser.add_argument(
        "--output", "-o",
        help="Output path for the config YAML (default: <project>/play-store.yaml)",
    )
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not (project / "pubspec.yaml").exists():
        print(f"Error: {project} does not appear to be a Flutter project (no pubspec.yaml)", file=sys.stderr)
        sys.exit(1)

    config = build_config(project)

    pubspec = parse_pubspec(project)
    config["_version"] = pubspec.get("version", "unknown")
    app_name = config["app"]["name"]

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        existing = project / "play-store.yaml"
        if existing.exists():
            output_path = project / "play-store.draft.yaml"
            print(f"NOTE: Existing config found at {existing} — writing draft to {output_path}")
        else:
            output_path = existing

    checklist = build_checklist(config, project)
    print_checklist(app_name, checklist)
    write_config(config, output_path)


if __name__ == "__main__":
    main()
