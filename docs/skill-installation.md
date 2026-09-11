# Install the Basilisk Skill

The canonical skill lives at `skills/basilisk/`. Codex and Claude Code use the
same files; link or copy that directory into the discovery path for the tool you
use.

## Codex

Codex discovers repository skills under `.agents/skills/`:

```bash
mkdir -p .agents/skills
ln -s ../../skills/basilisk .agents/skills/basilisk
```

From Codex CLI or the IDE extension, explicitly invoke it with `$basilisk`, or
ask naturally for help building, verifying, or debugging a Basilisk simulation
to allow implicit selection. Run `/skills` to confirm discovery. Restart Codex
if a newly added skill does not appear.

## Claude Code

Claude Code discovers repository skills under `.claude/skills/`:

```bash
mkdir -p .claude/skills
ln -s ../../skills/basilisk .claude/skills/basilisk
```

Invoke it explicitly with `/basilisk`, or ask naturally for help with a Basilisk
scenario to allow automatic selection. Claude Code watches existing skill
directories for changes; restart it when adding the top-level skills directory
for the first time.

## Personal installation

For use across repositories, link the canonical directory into
`~/.agents/skills/basilisk` for Codex or `~/.claude/skills/basilisk` for Claude
Code. Use an absolute link target when the skill repository and working project
are different repositories.

Keep only one editable copy of the skill so references and behavior cannot drift.

## Sources

- [OpenAI: Build skills](https://developers.openai.com/codex/skills/)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Agent Skills specification](https://agentskills.io/specification)
