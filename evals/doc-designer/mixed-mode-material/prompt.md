Hey — need a doc written for `shipit`, our internal deploy tool. Can you draft it, or at least tell
me how you'd structure it?

Background: `shipit` is a CLI the platform team built. Everyone in engineering uses it, about 40
people. It wraps our Kubernetes rollouts so nobody has to touch `kubectl` directly.

Three things it has to cover, because these are the three things people actually ask in Slack:

1. **New joiners can't get through their first deploy.** They don't know the order of operations —
   you have to `shipit auth`, then `shipit target staging`, then `shipit release --wait`, and if you
   skip the target step it silently deploys to whatever you targeted last, which has bitten three
   people. We want someone on day two to be able to do a staging deploy on their own without
   pinging anyone.

2. **Nobody can remember the flags.** There are 31 of them across 6 subcommands. `--wait`,
   `--wait-timeout`, `--canary-percent`, `--skip-preflight`, `--rollback-on`, and so on. People
   guess and get it wrong. We need the complete list with what each one does and its default.

3. **People keep asking why we do blue-green instead of rolling updates.** It comes up in every
   architecture review. The honest answer is that our session store isn't shared across pods so a
   rolling update drops sessions, and blue-green was cheaper than fixing the session store. I want
   that written down so I stop explaining it.

**Please keep it to one page.** I know that sounds like a lot for one page but I'm serious — the
last time the platform team documented something they split it into four separate pages and nobody
could ever find the thing they needed. Engineers will read one page. They will not read four.

Just give me the doc, or the outline if you'd rather start there.
