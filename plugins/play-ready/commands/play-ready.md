Prepare a Flutter app for Google Play Store submission. Analyzes the project, automates build config, and generates compliance artifacts.

Subcommands (passed as $ARGUMENTS):
- (empty) — full pipeline: analyze + automate + generate
- `analyze` — analyze project and print readiness checklist
- `generate` — render artifacts from existing config
- `templates` — re-render all templates for all configured apps

## Prerequisites

- Current directory must contain a `pubspec.yaml` (Flutter project).
- **`<play_ready_dir>`** is the `play-ready/` folder of the claude-code-config
  plugin: `${CLAUDE_PLUGIN_ROOT}/play-ready` when installed as a plugin,
  otherwise `~/repos/claude-code-config/play-ready`. It holds `templates/`,
  `scripts/` and `proguard/`.
- **App folder:** everything `/play-ready` makes for an app lives in
  `<project-root>/play-store/`, committed in the app's own repo:
  - `config.yaml` — the app's details (name, ID, data collected, content
    rating, signing alias, store assets)
  - `guides/` — filled-in Play Console answers and guides
  - `pages/` — `privacy.html` and `delete-data.html`. When `policy_hosting` is
    set, they're also published to that site.
  - `assets/` — icon, feature graphic, screenshots

  Nothing for the app goes anywhere else, except the published copies of the
  pages.
- **User config** at `~/.claude/play-ready.yaml` (or the path in
  `PLAY_READY_CONFIG`). It holds the personal details: `developer_profiles`,
  `policy_hosting` and `keystore`. Read it first. If it's missing, copy
  `config/play-ready.sample.yaml` from the plugin there and ask the user to
  fill it in. Never write its values into a public repo.
  - Developer name, email, website and phone come from a profile: `default`,
    or the one named by `app.developer_profile`. An app config sets them only
    to override the profile.
- Python dependencies: `cd <play_ready_dir>/scripts && pipenv install`

---

## Phase 0 — Migrate (every run)

Earlier versions scattered an app's files: `play-store.yaml` at the repo root,
`store_assets/`, `docs/plans/play-store/`, `~/plans/<app>/play-store/`, a
config in `~/templates/play-store/config/`, and developer details copied into
each config. Bring everything into the app folder before anything else:

```bash
cd <play_ready_dir>/scripts && pipenv run python migrate.py <project-root>
```

It's a dry run and safe to repeat. If it lists moves, show them to the user,
then run it again with `--apply`. Tracked files move with `git mv`. For each
`!` note about an old page the app's own hosting may still serve (e.g.
`public/delete-data.html`), tell the user to keep it until Play Console points
at the new URLs, and don't delete it yourself. If it says "already in the
current layout", continue.

Every later phase is also safe to re-run: steps check before acting, and
generated guides and pages are overwritten with fresh renders.

---

## Phase 1 — Analyze

1. Detect the Flutter project. Read `pubspec.yaml` to get the app name.
2. Check if `<project-root>/play-store/config.yaml` exists (Phase 0 has
   already moved an old one there).
   - If yes: load it and use it as the source of truth.
   - If no: run the analyzer to generate a draft:
     ```
     cd <play_ready_dir>/scripts && pipenv run python analyze.py <project-path>
     ```
     Show the user the generated config and ask them to review before continuing.
3. Print a readiness checklist by checking these items in the project:

| Item | How to check |
|------|-------------|
| applicationId set | grep `applicationId` in `android/app/build.gradle.kts` or `build.gradle` |
| Version set | read `version:` from `pubspec.yaml` |
| Upload keystore exists | check `android/key.jks` exists |
| Release signing configured | grep `signingConfigs` in build.gradle |
| key.properties exists | check `android/key.properties` |
| INTERNET permission | grep in `AndroidManifest.xml` |
| .gitignore covers signing | grep `key.properties` and `*.jks` in `.gitignore` |
| Privacy policy exists | check `play-store/pages/privacy.html` |
| Data deletion page exists | check `play-store/pages/delete-data.html` |
| ProGuard rules exist | check `android/app/proguard-rules.pro` |
| R8/minification enabled | grep `isMinifyEnabled = true` in build.gradle |
| Firestore rules file exists | check `firestore.rules` |
| App icon source exists | check the `icon_source` path from config |
| Feature graphic exists | check `play-store/assets/feature_graphic.png` (1024x500) |

Print as a checklist with `[x]` for present and `[ ]` for missing.

If the subcommand is `analyze`, stop here.

---

## Phase 2 — Automate

Execute these steps in order. Skip anything already done (checked in Phase 1). Ask the user before destructive or irreversible steps.

### 2.1 Keystore Generation
If `android/key.jks` is missing:
```bash
keytool -genkey -v -keystore android/key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias <signing.key_alias from app config> \
  -storepass <generate a random password> -keypass <same password> \
  -dname "CN=<app.name>, OU=<keystore.organizational_unit>, O=<keystore.organization>, L=<keystore.locality>, ST=<keystore.state>, C=<keystore.country>"
```
The `keystore` values come from the user config.
**IMPORTANT**: Show the generated passwords to the user and tell them to save them securely.

### 2.2 key.properties
If `android/key.properties` is missing, create it:
```properties
storePassword=<password from above>
keyPassword=<password from above>
keyAlias=<from config>
storeFile=../key.jks
```

### 2.3 build.gradle.kts Signing Config
If the release buildType uses debug signing, patch it:
- Add `import java.io.FileInputStream` and `import java.util.Properties` at the top
- Add keystoreProperties loading block before `android {`
- Add `signingConfigs.create("release")` block
- Change release buildType to use `signingConfigs.getByName("release")`

### 2.4 ProGuard Rules
If `android/app/proguard-rules.pro` is missing:
- Copy from `<play_ready_dir>/proguard/flutter.pro`
- Add app-specific keep rules for the app's namespace
- In build.gradle.kts release buildType, add:
  ```kotlin
  isMinifyEnabled = true
  isShrinkResources = true
  proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
  ```

### 2.5 INTERNET Permission
If missing from `AndroidManifest.xml`, add:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
```

### 2.6 .gitignore
Add these lines if not already present:
```
key.properties
*.jks
*.keystore
```

### 2.7 Privacy Policy and Data Deletion Page
These are rendered with everything else in Phase 3, into
`<project-root>/play-store/pages/`. If the user config has `policy_hosting`,
the same render also publishes them to that site and prints their public URLs
(`<base_url>/<app>/privacy` and `/delete-data`). The site's copies go live
only after that site repo is committed and deployed. Ask the user before
committing or deploying it.

Without `policy_hosting`, tell the user they need to host
`play-store/pages/privacy.html` somewhere public and enter its URL in Play
Console.

### 2.9 Generate Store Assets (Icon, Feature Graphic, Screenshots)

Run the asset generator for icon and feature graphic. Output goes to
`<project-root>/play-store/assets/` by default:
```bash
cd <play_ready_dir>/scripts && pipenv run python generate_assets.py \
  --config <project-root>/play-store/config.yaml \
  icon
```
```bash
cd <play_ready_dir>/scripts && pipenv run python generate_assets.py \
  --config <project-root>/play-store/config.yaml \
  feature
```

Show the generated icon and feature graphic to the user for approval. If they want changes (different colors, layout), the config supports `store_assets.feature_graphic.bg_gradient: ["#hex1", "#hex2"]`.

For screenshots, launch the Android emulator and run the app:
```bash
flutter emulators --launch <emulator-id>
# Wait for boot...
adb wait-for-device
adb shell getprop sys.boot_completed  # wait until "1"
flutter run -d <device-id>
```

Then capture screenshots by navigating to key screens and using `adb`:
```bash
adb shell screencap -p /sdcard/screenshot.png && adb pull /sdcard/screenshot.png <output-path>
```

Capture 2–8 screenshots covering the app's main features: home screen, key feature screens (from the `screens` list in config), and any unique selling points. Save to `<project-root>/play-store/assets/screenshots/`.

The `generate_assets.py` script also supports `screenshots` command for automated capture from a running emulator.

### 2.10 Build Release AAB
```bash
flutter build appbundle
```
Verify the output exists at `build/app/outputs/bundle/release/app-release.aab`.
Verify it's signed:
```bash
jarsigner -verify build/app/outputs/bundle/release/app-release.aab
```

---

## Phase 3 — Generate Artifacts

Render everything into the app folder:

```bash
cd <play_ready_dir>/scripts && pipenv run python render.py \
  --config <project-root>/play-store/config.yaml --all
```

This writes:
- `play-store/guides/data-safety-answers.md` — exact answers for the Play Console Data Safety form
- `play-store/guides/content-rating-answers.md` — exact answers for the IARC content rating questionnaire
- `play-store/guides/store-listing-guide.md` — description, screenshot specs, asset requirements, policy URLs
- `play-store/guides/play-console-walkthrough.md` — step-by-step Play Console submission guide
- `play-store/pages/privacy.html` and `delete-data.html`, also published to
  the `policy_hosting` site when configured

Print a summary listing all generated files with their paths.

---

## `templates` Subcommand

If subcommand is `templates`:
1. Find every app: `ls ~/repos/*/play-store/config.yaml ~/repos/*/play-store.yaml`
   (the second pattern finds apps still in the old layout)
2. For each app, run Phase 0 (migrate), then Phase 3 (render into its
   `play-store/` folder, publishing pages when `policy_hosting` is set)
3. Print summary of all rendered files

---

## Final Summary

Print a table summarizing what was done:
- Items that were already complete
- Items that were automated in this run
- Items that still need manual action (screenshots, feature graphic, Play Console account)
- Paths to all generated artifacts
- Next steps: open Play Console, upload AAB, fill forms using the generated guides
