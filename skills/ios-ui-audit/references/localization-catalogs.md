# iOS Localization — Catalog Audit Criteria

`UI-IOS-05` in `SKILL.md` audits **`.swift` views** — it catches raw string literals and missing
typed accessors. These criteria audit the **`.xcstrings` catalogs themselves**, which that rule
never looks at. Apply them whenever a diff touches a `Localizable.xcstrings`.

The authoring-side statement of these conventions lives in the consuming project as
`.agents/rules/LOCALIZATION_RULES.md`; what follows is how to *detect* violations after the fact.

## 1. Catalog ownership

Strings belong to the module that owns them:

- Feature → `Features/<Feature>/Sources/<Feature>/Resources/Localizable.xcstrings`
- Shell → `Packages/Shell/Sources/Shell/Resources/Localizable.xcstrings`

🔴 **Finding** — the diff adds or edits a string in `App/Resources/Localizable.xcstrings` or
`Packages/Platform/Resources/Localizable.xcstrings`. Those are auto-generated destinations; the
edit will be silently overwritten on the next sync, so it looks applied and then disappears.

## 2. Key naming

Every segment must match `^[a-z][a-zA-Z0-9]*$`. Mason brick templates under
`__brick__/` hold `{{placeholder}}` keys and are not real catalogs — both scripts below skip them.

```bash
# keys whose segments are not camelCase
python3 - <<'PY'
import json, re, sys, pathlib
seg = re.compile(r'^[a-z][a-zA-Z0-9]*$')
for f in pathlib.Path('.').rglob('Localizable.xcstrings'):
    if any(x in str(f) for x in ('__brick__', '.worktrees', '.git')):
        continue   # templates and other checkouts are not real catalogs
    for key in json.loads(f.read_text()).get('strings', {}):
        parts = key.split('.')
        if len(parts) < 2 or not all(seg.match(p) for p in parts):
            print(f'{f}: {key}')
PY
```

🔴 **Finding** — `snake_case`, `kebab-case`, `PascalCase`, or a bare unprefixed key (`title`,
`logout`) with fewer than two segments.

## 3. Hierarchy depth and module prefix

- 2 segments `<feature>.<key>` — screen root title, buttons, feature-wide messages.
- 3 segments `<feature>.<subfeature>.<key>` — sub-screens under `Presentation/<Subfeature>/`,
  section cards, bottom sheets.

🔴 **Finding** — the `<feature>` prefix does not match the owning module: a key in
`Features/Settings` that does not begin with `settings.`.

## 4. Leaf / branch collision

A key must never be a prefix of another key.

```bash
# a key that is also a parent of other keys
python3 - <<'PY'
import json, pathlib
for f in pathlib.Path('.').rglob('Localizable.xcstrings'):
    if any(x in str(f) for x in ('__brick__', '.worktrees', '.git')):
        continue   # templates and other checkouts are not real catalogs
    keys = set(json.loads(f.read_text()).get('strings', {}))
    for k in sorted(keys):
        if any(o.startswith(k + '.') for o in keys):
            print(f'{f}: {k} is a leaf and a branch')
PY
```

🔴 **Finding** — e.g. `settings.account` as a string while `settings.account.profile` exists.
The fix is `settings.account.title`.

## 5. Static vs OTA languages

Only `en` and `vi` are bundled in the binary. Everything else loads over the air.

🔴 **Finding** — `ja`, `ko`, or any other locale appearing in a module `.xcstrings`.

## 6. Re-sync evidence

Any catalog edit must be followed by `python3 scripts/merge_localizations.py` (or an Xcode
build), which validates the catalogs, syncs the masters, regenerates
`Translations.generated.swift`, and exports `App/Resources/backend_translations/`.

🔴 **Finding** — the diff changes a `.xcstrings` but `Translations.generated.swift` and the
backend JSON are untouched. The catalog and the generated accessors are then out of step, and
the typed accessor a view expects may not exist.

✅ A clean run reports `🛡️ All module catalogs passed DOs & DON'Ts validation rules`.
