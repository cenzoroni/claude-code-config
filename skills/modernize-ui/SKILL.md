---
name: modernize-ui
description: Plan and execute UI modernization for Flutter apps. Use when the user asks to make the UI look more modern.
disable-model-invocation: true
argument-hint: <optional: specific screen or component to modernize>
---

# Modernize UI Skill

Create and execute a plan to modernize the Flutter app's UI. Focus on:

1. **Audit current state**: Read the relevant screen/widget files. If `$ARGUMENTS` specifies a screen, focus there. Otherwise, survey the main screens.
2. **Plan changes** (present to user before executing):
   - Migrate to Material 3 (`useMaterial3: true`) if not already
   - Replace old widgets with modern equivalents (e.g., `ElevatedButton` over `RaisedButton`, `Card` with proper elevation/shape)
   - Improve spacing, padding, and visual hierarchy
   - Use consistent border radius, color scheme, and typography
   - Add subtle animations where appropriate (hero transitions, fade-ins)
3. **Execute**: Apply changes incrementally, one screen at a time.
4. **Verify**: Run `flutter analyze` after changes.

Do NOT change functionality — only visual presentation. Keep the existing state management and data flow intact.
