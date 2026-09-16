# Arm B (baseline, no skill) — raw reply

Hey — yes, one page, one URL. Draft below.

One honest note before you read it. I don't think "one page" is really about word count for you — the complaint is that last time nobody could find the thing they needed. So I've optimised for *one file, scroll instead of click*, with a three-link jump list at the top. That does mean the page is long-ish, because a complete table of 31 flags is long no matter how it's formatted. That's fine: nobody reads a flag table, they Ctrl-F it. The rule I'd hold us to is "never more than one URL," not "never more than 600 words." If you meant it literally, tell me and I'll cut the flag descriptions down to four words each.

Second: I couldn't fill the flag table in. I have five flag names from your message and no defaults. I'm not going to invent the other 26 or guess defaults — a reference doc that's confidently wrong about `--rollback-on` is worse than no doc. Send me `shipit <subcommand> --help` for all six and I'll have it filled in same day. Everywhere I'm guessing or need you to confirm, it's marked **[confirm]** in the text.

---

# shipit

`shipit` deploys our services to Kubernetes. It wraps `kubectl` so you don't have to use `kubectl` directly. Owned by the platform team — ask in #platform.

**Jump to:** [Your first deploy](#your-first-deploy-staging) · [Flag reference](#flag-reference) · [Why blue-green, not rolling updates](#why-blue-green-not-rolling-updates)

## Your first deploy (staging)

Three commands, in this order. The order matters.

**1. Authenticate**
```
shipit auth
```
Opens SSO in your browser and stores a token. **[confirm: where, and how long does it last?]** You'll need to repeat this when it expires.

**2. Choose where you're deploying**
```
shipit target staging
```
Sets the target cluster. **This setting is sticky** — it persists across terminal sessions and across days until you change it.

**3. Release**
```
shipit release --wait
```
Deploys the current commit to the target from step 2. `--wait` blocks until the rollout finishes and fails loudly if it doesn't. Without it, the command returns immediately and you won't learn about a failed rollout from `shipit`.

> ### Read this before your first release
> Step 2 is silently optional. If you skip it, `shipit release` does not stop and ask — it deploys to **whatever you targeted last**, which may be production. Three people have done this.
>
> Before every release, print your current target:
> ```
> shipit target
> ```
> **[confirm: does bare `shipit target` print the current target? If not, what does?]**

That's the whole day-two flow. Everything below is variations on step 3.

## Flag reference

Every flag, what it does, and what happens if you don't pass it.

### `shipit release`

| Flag | What it does | Default |
|---|---|---|
| `--wait` | Blocks until the rollout completes; exits non-zero if it fails. | off — **[confirm]** |
| `--wait-timeout` | How long `--wait` waits before giving up. What happens on timeout: **[confirm — does it roll back, or just stop watching?]** | **[?]** |
| `--canary-percent` | **[confirm — see my note below, this one needs explaining given we do blue-green]** | **[?]** |
| `--skip-preflight` | Skips the pre-deploy checks. **[confirm: which checks, and when is skipping them legitimate?]** | off — **[confirm]** |
| `--rollback-on` | **[confirm: takes what values?]** | **[?]** |

### `shipit auth`
**[flags needed]**

### `shipit target`
**[flags needed]**

### `shipit <4th subcommand>`
**[name + flags needed]**

### `shipit <5th subcommand>`
**[name + flags needed]**

### `shipit <6th subcommand>`
**[name + flags needed]**

## Why blue-green, not rolling updates

Because our session store isn't shared across pods.

A rolling update replaces pods one at a time underneath live traffic. Since each pod holds its own sessions, every session on a replaced pod is dropped — users get logged out mid-flow, every deploy. Blue-green brings up a complete second set of pods, then moves traffic at the load balancer in a single switch, so a session isn't stranded by a pod disappearing out from under it.

The alternative was to make the session store shared, which would make rolling updates safe. We compared the two. **Blue-green was cheaper to build and cheaper to operate than migrating the session store, and it solved the problem we actually had.** That's the entire reason. It wasn't chosen for progressive delivery, canary safety, or anything else people sometimes assume.

What it costs us: roughly double capacity for the duration of a release, and no gradual traffic shift — the switch is all-or-nothing.

**When to revisit:** if the session store moves off the pods for any other reason, rolling updates become viable and the capacity cost of blue-green stops being worth paying. Until that happens, this is the answer.

## Getting help

**[confirm: #platform? an on-call rotation? a runbook link for failed rollouts?]**

---

Two things I need from you:

1. `shipit <subcommand> --help` for all six, and the two behaviour questions marked in the quickstart.
2. A sanity check on `--canary-percent`. If we do blue-green with an all-or-nothing traffic switch, a canary percentage looks contradictory — and that's exactly the question this doc will now generate in every architecture review it was meant to end. Either there's a nuance I should write into the blue-green section, or that flag is vestigial and should be deleted from the tool.

One suggestion, take it or leave it: a hand-maintained table of 31 flags will be wrong within two months, and a wrong reference is the reason people go back to asking in Slack. If `shipit` can dump its own `--help` as text, have CI regenerate the flag section between two comment markers on each release. Then the section you most want to be trustworthy is the one nobody has to remember to update.

And separately from the doc: the silent-target behaviour is a bug, not a documentation gap. Documenting it means 40 people have to remember a warning forever. Making `shipit release` print its target and require confirmation — or require an explicit target when the last one was production — means nobody has to. I'll write the warning either way, but it's worth an hour of someone's time.
