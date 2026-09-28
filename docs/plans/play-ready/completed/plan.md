# `/play-ready` — Google Play Store Preparation Skill

## Overview

A Claude Code skill that takes any Flutter app from development to Play Store submission-ready. It automates everything programmatic (signing, build config, security rules, templated legal pages) and generates comprehensive artifacts (PDFs/Markdown) for manual steps (content rating questionnaire, data safety form, store listing guide, Play Console walkthrough).

Shared templates live in `~/templates/play-store/` so all current and future apps reuse the same legal/compliance scaffolding — each app just provides a small YAML config.

---

## Architecture

```
~/templates/play-store/
  config/
    my-app.yaml              # per-app config
  templates/
    privacy-policy.html.j2   # Jinja2 templates
    data-deletion.html.j2
    data-safety-answers.md.j2
    content-rating-answers.md.j2
    store-listing-guide.md.j2
    play-console-walkthrough.md.j2
  proguard/
    flutter.pro              # shared proguard base rules
  scripts/
    render.py                # template renderer (Jinja2 + config YAML → output)
    analyze.py               # static analysis of a Flutter project
```

The skill itself is a Claude Code custom slash command defined in the repo's `.claude/commands/play-ready.md` (or global `~/.claude/commands/play-ready.md` to make it available everywhere). It orchestrates: detect project → load/create config → run phases → report.

---

## Part 1: Shared Templates

### 1.1 App Config Schema

Each app gets a YAML file in `~/templates/play-store/config/`. The skill can auto-generate a draft by analyzing the project.

```yaml
# ~/templates/play-store/config/my-app.yaml
app:
  name: "My App"
  application_id: "com.example.my_app"
  developer_name: "Your Name"
  developer_email: "you@example.com"
  repo: "~/repos/my-app"
  description_short: "One-line summary of what the app does (80 chars max)."
  description_long: |
    A few paragraphs describing the app for the store listing (4000 chars max).
  category: "PARENTING"        # Play Store category
  target_audience: "general"   # general | children | mixed
  contains_ads: false
  in_app_purchases: false

firebase:
  project_id: "my-app-12345"
  services:
    - auth
    - firestore
  auth_methods:
    - email
    - google
  has_security_rules: true
  rules_file: "firestore.rules"

permissions:
  - INTERNET

data_collected:
  - type: "email_address"
    purpose: "account_management"
    required: true
    shared_with_third_parties: false
    user_deletable: true
  - type: "app_interactions"
    label: "In-app preferences and choices"
    purpose: "app_functionality"
    required: true
    shared_with_third_parties: false
    user_deletable: true

content_rating:
  violence: "none"
  sexual_content: "none"
  profanity: "none"
  controlled_substances: "none"
  user_interaction: true          # shared spaces = user interaction
  shares_location: false
  allows_user_generated_content: false
  digital_purchases: false

signing:
  keystore_path: "android/key.jks"
  key_alias: "upload"
  # passwords NOT stored here — key.properties is the runtime source

store_assets:
  icon_source: "assets/icon.png"    # 1024x1024 source for Play Store hi-res icon
  # feature_graphic: null           # must be created manually (1024x500)
  # screenshots: []                 # must be captured manually
```

### 1.2 Template: Privacy Policy (`privacy-policy.html.j2`)

Parameterized by:
- `app.name`, `app.developer_name`, `app.developer_email`
- `firebase.services` (determines which services section to include)
- `firebase.auth_methods` (determines what personal info is mentioned)
- `data_collected[]` (drives the "What We Collect" section)
- `permissions` (if location/camera, adds those sections)
- Current date for "Last updated"

Consolidates the existing baby-names `privacy-policy.html` and gofish `PRIVACY_POLICY.md` into one template that covers both (and future apps).

### 1.3 Template: Data Deletion Page (`data-deletion.html.j2`)

Parameterized by:
- `app.name`, `app.developer_email`
- `data_collected[]` (lists what gets deleted)

The template produces a simple hosted page explaining how to request deletion and what data is removed.

### 1.4 Template: Data Safety Answers (`data-safety-answers.md.j2`)

Maps `data_collected[]` and `firebase.services` to Google's exact Data Safety form structure. Output is a step-by-step guide with the exact answers to select in Play Console.

Google's Data Safety form has these top-level categories:
- **Data collection and security**: Is all data encrypted in transit? Can users request deletion?
- **Data types collected**: Personal info, Financial info, Health info, Messages, Photos/videos, Audio, Files, App activity, Web browsing, App info/performance, Device IDs
- **Data usage per type**: For each collected type — Is it shared? Purpose? Required or optional?

The template produces a markdown table mapping each `data_collected[]` entry to Google's categories:

```markdown
## Data Safety Form Answers

### Overview
| Question | Answer |
|----------|--------|
| Does your app collect or share any user data? | Yes |
| Is all collected data encrypted in transit? | Yes (Firebase uses HTTPS) |
| Can users request data deletion? | Yes (via email to {{ developer_email }}) |

### Data Types Collected

#### Personal Info → Email Address
| Question | Answer |
|----------|--------|
| Is this data collected, shared, or both? | Collected |
| Is this data processed ephemerally? | No |
| Is this data required or optional? | Required |
| Why is this data collected? | Account management |

#### App Activity → App interactions
| Question | Answer |
|----------|--------|
| Is this data collected, shared, or both? | Collected |
...
```

### 1.5 Template: Content Rating Answers (`content-rating-answers.md.j2`)

Maps `content_rating.*` to the IARC questionnaire. Google uses the International Age Rating Coalition questionnaire, which has ~25 questions across categories. The template pre-fills based on config:

```markdown
## Content Rating Questionnaire (IARC)

Complete this at: Play Console → Policy → App content → Content rating

### Violence
1. Does the app contain violence? → **No**
2. Is violence directed at specific characters? → **N/A**
3. Does the app depict realistic violence? → **N/A**

### Sexual Content
4. Does the app contain sexual content or nudity? → **No**

### Language
5. Does the app contain profanity or crude humor? → **No**

### Controlled Substances
6. Does the app reference or depict drug use? → **No**
7. Does the app reference or depict alcohol or tobacco? → **No**

### Interactive Elements
8. Do users interact with each other? → **Yes**
   (Partners share a space and see each other's picks)
9. Can users share their location? → **No**
10. Does the app allow digital purchases? → **No**
11. Does the app share personal info with third parties? → **No**
12. Does the app allow user-generated content? → **No**

### Miscellaneous
13. Is the app a game? → **No**
14. Does the app allow unrestricted internet access? → **No**

Expected rating: **Rated for Everyone** (ESRB: E / PEGI: 3)
```

### 1.6 Template: Store Listing Guide (`store-listing-guide.md.j2`)

Produces a comprehensive guide with:
- **Short description** (pre-filled from config, 80 char limit enforced)
- **Full description** (pre-filled from config, 4000 char limit)
- **Category** recommendation
- **Screenshot requirements**: exact dimensions, what to capture (list key screens in the app by analyzing route names or screen files), suggested device frames
- **Feature graphic**: spec (1024x500), design tips, tools (Figma/Canva)
- **Hi-res icon**: spec (512x512), note if source icon exists and at what resolution
- **Contact info**: pre-filled from config

### 1.7 Template: Play Console Walkthrough (`play-console-walkthrough.md.j2`)

Step-by-step guide through Play Console, tailored to the app:

1. **Create app** — app name, default language, app/game, free/paid
2. **Store listing** — point to the store listing guide artifact
3. **Content rating** — point to the content rating artifact
4. **Target audience** — pre-filled from `target_audience`
5. **App access** — if app requires login, explain that a test account must be provided to Google reviewers (include instructions to create one)
6. **Data safety** — point to the data safety artifact
7. **Ads declaration** — pre-filled from `contains_ads`
8. **Testing track** — recommend internal testing first, explain the flow
9. **Upload AAB** — path to the built AAB
10. **Review & publish** — timeline expectations (typically 1-3 days for new apps)

---

## Part 2: Analysis Engine (`analyze.py`)

A Python script (using pipenv) that statically analyzes a Flutter project and produces a draft config YAML. This is what makes the skill smart — you point it at any Flutter repo and it figures out what the app does.

### Inputs
- Path to Flutter project root

### Analysis Steps

1. **pubspec.yaml** → extract app name, version, dependencies
2. **Dependency mapping** — known dependency → service/capability:
   ```
   firebase_core          → firebase
   firebase_auth          → firebase.auth
   cloud_firestore        → firebase.firestore
   firebase_storage       → firebase.storage
   firebase_analytics     → firebase.analytics
   firebase_crashlytics   → firebase.crashlytics
   google_sign_in         → auth_methods: [google]
   sign_in_with_apple     → auth_methods: [apple]
   google_mobile_ads      → contains_ads: true
   in_app_purchase        → in_app_purchases: true
   geolocator / location  → permissions: [location], shares_location: maybe
   camera                 → permissions: [camera]
   image_picker           → permissions: [camera, photos]
   ```
3. **AndroidManifest.xml** → extract declared permissions, applicationId (cross-check with build.gradle.kts)
4. **build.gradle.kts** → extract applicationId, minSdk, signingConfigs presence, minify/shrink settings
5. **Auth method detection** — grep for `signInWithEmailAndPassword`, `signInWithGoogle`, `signInWithApple`, `signInWithCredential`, `PhoneAuthProvider`
6. **Firebase project** — parse `firebase.json` or `.firebaserc` for project ID
7. **Firestore rules** — check if `firestore.rules` exists, basic lint (warn if any `allow write: if true` or `allow read, write: if request.auth != null` on sensitive paths)
8. **Existing artifacts** — check for privacy policy, data deletion page, key.properties, keystore, proguard rules
9. **Screen enumeration** — find all `*_screen.dart` or `*_page.dart` files, extract class names → suggest which screens to screenshot
10. **Icon detection** — find `assets/icon.png` or similar, check resolution

### Output
- Draft `~/templates/play-store/config/<app-name>.yaml`
- Readiness checklist printed to stdout (what's done, what's missing)

---

## Part 3: The Skill Itself

### 3.1 Skill Definition

File: `~/.claude/commands/play-ready.md`

The skill is a global Claude Code slash command. When invoked:

```
/play-ready              # analyze + automate + generate for current project
/play-ready analyze      # just analyze, produce checklist and draft config
/play-ready generate     # just generate artifacts from existing config
/play-ready templates    # regenerate shared templates for all apps from configs
```

### 3.2 Execution Flow

#### Phase 1: Analyze
1. Detect Flutter project in current directory
2. Run `analyze.py` or equivalent inline analysis
3. Check if config YAML exists in `~/templates/play-store/config/`
   - If yes: load it, diff against analysis, warn about discrepancies
   - If no: generate draft, ask user to review/confirm
4. Print readiness checklist:
   ```
   Play Store Readiness — My App
   ========================================
   [x] applicationId set (com.example.my_app)
   [x] Version set (1.0.0+1)
   [x] Upload keystore exists
   [x] Release signing configured
   [x] INTERNET permission declared
   [x] .gitignore covers signing files
   [x] Privacy policy exists
   [ ] Data deletion page missing
   [ ] ProGuard rules missing (recommended for release)
   [x] Firestore rules hardened (uid-match on writes)
   [x] Firestore rules deployed
   [ ] Feature graphic missing (1024x500)
   [ ] Screenshots missing (min 2 phone)
   [ ] Play Store hi-res icon missing (512x512 export)
   [ ] R8/minification not enabled
   ```

#### Phase 2: Automate
Execute in order, skipping what's already done:

1. **Keystore** — generate if missing
   ```
   keytool -genkey -v -keystore android/key.jks \
     -keyalg RSA -keysize 2048 -validity 10000 \
     -alias <from config> \
     -storepass <generated> -keypass <generated> \
     -dname "CN=<app.name>, OU=Dev, O=<app.developer_name>, L=Unknown, ST=Unknown, C=US"
   ```

2. **key.properties** — create if missing
   ```properties
   storePassword=<password>
   keyPassword=<password>
   keyAlias=<alias>
   storeFile=../key.jks
   ```

3. **build.gradle.kts** — patch signing config if still using debug signing
   - Add `import java.io.FileInputStream` + `import java.util.Properties`
   - Add keystoreProperties loading block
   - Add `signingConfigs.create("release")` block
   - Change `release { signingConfig }` from debug to release

4. **ProGuard rules** — create `android/app/proguard-rules.pro` from shared base
   - Flutter engine rules
   - Firebase rules (if firebase detected)
   - Google Play Core rules
   - Add `isMinifyEnabled = true` and `isShrinkResources = true` to release buildType
   - Add `proguardFiles(...)` reference

5. **INTERNET permission** — add to AndroidManifest if missing

6. **.gitignore** — add `key.properties`, `*.jks`, `*.keystore` if missing

7. **Privacy policy** — render from template if missing or outdated

8. **Data deletion page** — render from template if missing

9. **Firestore rules hardening** (if firebase.firestore detected)
   - Check for overly permissive rules
   - Add uid-match constraints on write operations
   - Deploy with `firebase deploy --only firestore:rules --project <project_id>`

10. **Play Store hi-res icon** — if `icon_source` exists at 1024x1024, resize to 512x512
    ```
    sips -z 512 512 assets/icon.png --out android/app/src/main/play-store-icon.png
    ```

11. **Build release AAB**
    ```
    flutter build appbundle
    ```
    Verify output exists and is signed:
    ```
    jarsigner -verify build/app/outputs/bundle/release/app-release.aab
    ```

#### Phase 3: Generate Artifacts
Render all templates from config and write to `<app repo>/docs/plans/play-store/`:

```
<app repo>/docs/plans/play-store/
  data-safety-answers.md
  content-rating-answers.md
  store-listing-guide.md
  play-console-walkthrough.md
  privacy-policy.html        (also copied to repo)
  data-deletion.html          (also copied to repo)
```

Print summary with paths and next steps.

---

## Part 4: Implementation Plan

### Step 1: Create shared template directory structure
- `mkdir -p ~/templates/play-store/{config,templates,proguard,scripts}`
- Create the Jinja2 templates (privacy policy, data deletion, data safety, content rating, store listing, walkthrough)
- Create the shared proguard base rules file
- Create `scripts/render.py` — takes a config YAML + template name → rendered output

### Step 2: Create config files for existing apps
- `baby-names.yaml` — based on the survey data above
- `gofish.yaml` — based on the survey data above

### Step 3: Migrate existing artifacts to templates
- Consolidate baby-names `privacy-policy.html` and gofish `PRIVACY_POLICY.md` into `privacy-policy.html.j2`
- Consolidate gofish `public/delete-data.html` + `public/delete-account.html` into `data-deletion.html.j2`
- Verify rendered output matches (or improves on) the originals

### Step 4: Write the analysis engine
- `scripts/analyze.py` — static analysis of a Flutter project
- Dependency mapping table
- Config YAML draft generation
- Readiness checklist output

### Step 5: Write the content/compliance templates
- `data-safety-answers.md.j2` — full Google Data Safety form mapping
- `content-rating-answers.md.j2` — full IARC questionnaire mapping
- `store-listing-guide.md.j2` — screenshot specs, description templates, asset requirements
- `play-console-walkthrough.md.j2` — step-by-step Play Console instructions

### Step 6: Create the Claude Code skill
- `~/.claude/commands/play-ready.md` — skill definition with the three subcommands
- Wire up analyze → automate → generate flow
- Test against baby-names repo
- Test against gofish repo

### Step 7: Validate end-to-end
- Run `/play-ready` on baby-names from scratch (after reverting play-store prep)
- Run `/play-ready` on gofish
- Verify all artifacts are correct
- Verify AAB builds and is properly signed

---

## Appendix A: Google Data Safety — Full Category Reference

These are the exact categories Google asks about. The template maps `data_collected[]` entries to these.

### Data Types (select all that apply)
| Category | Types |
|----------|-------|
| Personal info | Name, Email, User IDs, Address, Phone, Other |
| Financial info | Purchase history, Credit info, Other |
| Health and fitness | Health info, Fitness info |
| Messages | Emails, SMS/MMS, Other messages |
| Photos and videos | Photos, Videos |
| Audio files | Voice/sound recordings, Music files, Other audio |
| Files and docs | Files and docs |
| Calendar | Calendar events |
| Contacts | Contacts |
| App activity | App interactions, Search history, Installed apps, Other UGC, Other actions |
| Web browsing | Web browsing history |
| App info and performance | Crash logs, Diagnostics, Other performance data |
| Device or other IDs | Device or other IDs |
| Location | Approximate location, Precise location |

### Per Data Type Questions
For each selected type, Google asks:
1. Is this data **collected**, **shared**, or both?
2. Is this data **processed ephemerally**? (not stored beyond the immediate request)
3. Is this data **required** or can users opt out?
4. **Why** is this data collected/shared? (select all):
   - App functionality
   - Analytics
   - Developer communications
   - Advertising or marketing
   - Fraud prevention, security, compliance
   - Personalization
   - Account management

## Appendix B: IARC Content Rating — Full Questionnaire Reference

The IARC questionnaire used by Google Play. Each question maps to a `content_rating.*` config field.

### Section 1: Violence
1. Does the app depict violence or contain violent themes?
2. Is the violence realistic? (blood, injury detail)
3. Is violence directed at specific characters?
4. Can players engage in violence against other human characters?
5. Is the violence rewarded or shown without consequence?

### Section 2: Sexuality
6. Does the app contain sexual content, nudity, or sexual themes?
7. Is the sexual content graphic or explicit?

### Section 3: Language
8. Does the app contain profanity, crude humor, or sexual references in text/audio?
9. How frequent/intense is the language?

### Section 4: Controlled Substances
10. Does the app reference or depict tobacco, alcohol, or drugs?
11. Is the use depicted positively/neutrally or shown with consequences?

### Section 5: Interactive Elements
12. Do users interact with each other in any way? (chat, shared content, multiplayer)
13. Is user-generated content possible? (text, images, levels)
14. Is there real-money gambling or simulated gambling?
15. Can users make digital purchases within the app?
16. Does the app share personal information with third parties?
17. Does the app share the user's physical location with other users?
18. Does the app allow unrestricted web browsing?

### Section 6: Miscellaneous
19. Is the app primarily a game?
20. Does the app contain loot boxes or randomized paid items?

### Rating Outcomes
| Answers | Expected Rating |
|---------|----------------|
| All "No" + no interaction | Everyone (ESRB: E, PEGI: 3) |
| Mild interaction, no content | Everyone (ESRB: E, PEGI: 3) |
| Cartoon violence | Everyone 10+ (ESRB: E10+, PEGI: 7) |
| Mild language or suggestive themes | Teen (ESRB: T, PEGI: 12) |
| Intense violence, strong language | Mature (ESRB: M, PEGI: 16/18) |

## Appendix C: Dependency → Service/Capability Mapping

Used by the analysis engine to auto-detect app capabilities from `pubspec.yaml`.

| Dependency | Service | Config Impact |
|-----------|---------|---------------|
| `firebase_core` | Firebase | `firebase.services: [core]` |
| `firebase_auth` | Firebase Auth | `firebase.services: [auth]`, `data_collected: [email]` |
| `cloud_firestore` | Cloud Firestore | `firebase.services: [firestore]`, `data_collected: [app_activity]` |
| `firebase_storage` | Cloud Storage | `firebase.services: [storage]` |
| `firebase_analytics` | Analytics | `firebase.services: [analytics]`, `data_collected: [app_info, device_ids]` |
| `firebase_crashlytics` | Crashlytics | `firebase.services: [crashlytics]`, `data_collected: [crash_logs]` |
| `firebase_messaging` | FCM | `firebase.services: [messaging]`, `data_collected: [device_ids]` |
| `google_sign_in` | Google Sign-In | `firebase.auth_methods: [google]`, `data_collected: [name, email]` |
| `sign_in_with_apple` | Apple Sign-In | `firebase.auth_methods: [apple]` |
| `google_mobile_ads` | AdMob | `contains_ads: true`, `data_collected: [device_ids, app_info]` |
| `in_app_purchase` | Billing | `in_app_purchases: true`, `content_rating.digital_purchases: true` |
| `geolocator` | Location | `permissions: [location]`, `content_rating.shares_location: maybe` |
| `location` | Location | same as geolocator |
| `camera` | Camera | `permissions: [camera]` |
| `image_picker` | Photos/Camera | `permissions: [camera, photos]` |
| `shared_preferences` | Local Storage | (no play store impact) |
| `url_launcher` | Web browsing | `content_rating.unrestricted_web: maybe` |

## Appendix D: ProGuard Base Rules

Shared rules for Flutter release builds:

```proguard
# Flutter
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-dontwarn io.flutter.embedding.**

# Firebase
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.android.gms.**

# Gson (used by Firebase)
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.** { *; }
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# OkHttp / gRPC
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**
-dontwarn org.conscrypt.**
-keep class okhttp3.** { *; }
-keep class okio.** { *; }

# Play Core (split APKs)
-keep class com.google.android.play.core.** { *; }

# Keep source file/line info for crash reports
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
```
