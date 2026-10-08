# Conflict Playbook

How to resolve a conflict that `integrate_branch.py rebase` stopped on (exit 2). The script tags each
conflicted file; you classify it; you resolve mechanical conflicts yourself and bring semantic ones
to your human partner.

## Read This First: Ours and Theirs Are Reversed

During a rebase the roles are the reverse of a merge:

| Name | During a rebase it means |
|------|--------------------------|
| `--ours`, `HEAD`, the `<<<<<<<` side | The base (`develop`) plus the branch commits already replayed |
| `--theirs`, the `>>>>>>>` side | The branch commit being replayed now |

So `git checkout --ours -- <file>` takes **develop's** version, not yours.

## Recorded Resolutions

The script enables `rerere`. When git prints `Resolved '<file>' using previous resolution`, it has
re-applied a resolution you recorded earlier. The file is still listed as conflicted: review it like
any other before `git add`.

## Classify Every Conflicted File

| Class | Examples | Handling |
|-------|----------|----------|
| `regenerate` (tagged by the script) | `*.g.dart`, `*.freezed.dart`, `*.mocks.dart`, `pubspec.lock`, `Podfile.lock`, `Package.resolved`, `gradle.lockfile` | Never hand-merge. See [Regenerate Files](#regenerate-files) |
| Mechanical (you resolve and record) | Imports; both sides appending distinct entries to a list, enum, DI module or route table; formatting-only or comment-only differences | Keep both sides. See [Mechanical Conflicts](#mechanical-conflicts) |
| Semantic (stop and ask) | The same function body changed on both sides; a signature, nullability or contract change; one side deleted what the other modified; configuration values and feature flags; security-sensitive files (crypto, auth, keychain, tokens, biometrics) | See [Semantic Conflicts](#semantic-conflicts) |

**Default rule:** when you cannot state the intent of either side in one sentence, the conflict is
semantic.

## Regenerate Files

During the rebase, take the base side and continue:

```bash
git checkout --ours -- <file>
git add <file>
```

After the rebase completes, regenerate once and commit:

| Platform | Regenerate with |
|----------|-----------------|
| Flutter | `d3nexus:melos_sync` (bootstrap, then code generation in order) |
| Android | `./gradlew dependencies --write-locks` for `gradle.lockfile` |
| iOS | `tuist install` for `Package.resolved` |

```bash
git add -A
git commit -m "[<SCOPE>] Regenerate after rebase onto <base>"
```

`verify-tier` reports `conflicts` after this commit. That is expected: regenerated code is a change
the earlier verification never saw.

## Mechanical Conflicts

Resolve so that both sides survive: keep both imports, both list entries, both registrations, in the
order the file already uses. Then:

```bash
git add <file>
```

Record each one as `<file> — <what was combined>` for the report you give after the rebase.

## Semantic Conflicts

Stop. Gather both intents before writing anything:

```bash
git log -1 --format='%h %s' REBASE_HEAD
git log --format='%h %s' "$(git merge-base REBASE_HEAD <base>)..<base>" -- <file>
```

The first line is the branch commit being replayed; find its task in `.devtool/features/` or
`.devtool/epic/<epic_dir>/` by the commit subject. The rest are the upstream commits that touched the
file; an upstream epic's merge commit names that epic.

Present this to your human partner and wait:

```text
Semantic conflict in <file>, hunk <n>

Upstream (<base>): <sha> <subject> (epic <epic_dir>, if any)
  Intent: <one sentence>
This branch: <sha> <subject> (task <task file>, "<task title>")
  Intent: <one sentence>

Proposed resolution:
<diff of the resolved hunk>

1. Accept the proposal
2. Take the upstream version
3. Take this branch's version
4. I will resolve it myself
5. Abort the rebase
```

Apply the choice, `git add <file>`, and continue. Choice 5 is
`python3 "$INTEGRATE" rebase --abort --base <base>`, which restores the branch to its backup.

## After the Rebase

Continue until the rebase completes:

```bash
python3 "$INTEGRATE" rebase --continue --base <base>
```

Then run `verify-tier` and report: the commits pulled in, the upstream epics, every mechanical
resolution you recorded, every semantic decision your human partner made, and the tier.
