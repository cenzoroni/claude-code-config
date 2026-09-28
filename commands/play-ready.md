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
- **App config:** `<project-root>/play-store.yaml`, committed in the app's own
  repo. It holds the app's details (name, ID, data collected, content rating,
  signing alias, store assets).
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

## Phase 1 — Analyze

1. Detect the Flutter project. Read `pubspec.yaml` to get the app name.
2. Check if `<project-root>/play-store.yaml` exists.
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
| Privacy policy exists | check for `privacy-policy.html`, `PRIVACY_POLICY.md`, or similar |
| Data deletion page exists | check for `delete-data.html`, `delete-account.html` in `public/` |
| ProGuard rules exist | check `android/app/proguard-rules.pro` |
| R8/minification enabled | grep `isMinifyEnabled = true` in build.gradle |
| Firestore rules file exists | check `firestore.rules` |
| App icon source exists | check the `icon_source` path from config |
| Feature graphic exists | check for 1024x500 feature graphic |

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
**If the user config has `policy_hosting`** (the normal case), render both
pages into the hosting site:
```bash
cd <play_ready_dir>/scripts && pipenv run python render.py \
  --config <project-root>/play-store.yaml --hosted
```
This writes `<repo>/<dir>/<app-name>/privacy.html` and `delete-data.html` and
prints the two public URLs (`<base_url>/<app-name>/privacy` and
`/delete-data`). Tell the user the pages go live only after they commit and
deploy that site repo. Ask before committing or deploying it.

**Without `policy_hosting`**, render into the app repo instead:
```bash
cd <play_ready_dir>/scripts && pipenv run python render.py \
  --config <project-root>/play-store.yaml \
  --template privacy-policy.html.j2 \
  --output <project-root>/privacy-policy.html
cd <play_ready_dir>/scripts && pipenv run python render.py \
  --config <project-root>/play-store.yaml \
  --template data-deletion.html.j2 \
  --output <project-root>/public/delete-data.html
```

### 2.9 Generate Store Assets (Icon, Feature Graphic, Screenshots)

Run the asset generator for icon and feature graphic:
```bash
cd <play_ready_dir>/scripts && pipenv run python generate_assets.py \
  --config <project-root>/play-store.yaml \
  --output <project-root>/store_assets \
  icon
```
```bash
cd <play_ready_dir>/scripts && pipenv run python generate_assets.py \
  --config <project-root>/play-store.yaml \
  --output <project-root>/store_assets \
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

Capture 2–8 screenshots covering the app's main features: home screen, key feature screens (from the `screens` list in config), and any unique selling points. Save to `<project-root>/store_assets/screenshots/`.

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

Render all compliance/guide templates and write to `<app repo>/docs/plans/play-store/`:

```bash
cd <play_ready_dir>/scripts && pipenv run python render.py \
  --config <project-root>/play-store.yaml \
  --all \
  --output <app repo>/docs/plans/play-store/
```

This produces:
- `data-safety-answers.md` — exact answers for the Play Console Data Safety form
- `content-rating-answers.md` — exact answers for the IARC content rating questionnaire
- `store-listing-guide.md` — description, screenshot specs, asset requirements
- `play-console-walkthrough.md` — step-by-step Play Console submission guide
- `privacy-policy.html` — rendered privacy policy (also in repo)
- `data-deletion.html` — rendered data deletion page (also in repo)

Print a summary listing all generated files with their paths.

---

## `templates` Subcommand

If subcommand is `templates`:
1. Find every app config: `ls ~/repos/*/play-store.yaml`
2. For each one, render all templates to `<that repo>/docs/plans/play-store/`
   (and the hosted pages with `--hosted` if `policy_hosting` is set)
3. Print summary of all rendered files

---

## Final Summary

Print a table summarizing what was done:
- Items that were already complete
- Items that were automated in this run
- Items that still need manual action (screenshots, feature graphic, Play Console account)
- Paths to all generated artifacts
- Next steps: open Play Console, upload AAB, fill forms using the generated guides
