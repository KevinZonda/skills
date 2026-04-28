# Alice Skills

Claude Code skills managed in this repository.

## Skills

| Skill | Description |
|-------|-------------|
| [academic-paper-writing](./academic-paper-writing/) | Guide and draft academic papers following rigorous section structure (ML focus) |
| [academic-reference-search](./academic-reference-search/) | Search academic papers via open scholarly APIs |
| [academic-slides](./academic-slides/) | Create/revise academic slide decks (.pptx) |
| [chinese-polish](./chinese-polish/) | Chinese text polishing & multi-language translation via DeepSeek API |

## Installation

Skills are installed as symlinks in `~/.agents/skills/`:

```bash
ln -sf $(pwd)/<skill-name> ~/.agents/skills/<skill-name>
```

## Adding a New Skill

1. Create a directory with `SKILL.md` and optional `scripts/`
2. Add a symlink in `~/.agents/skills/`
3. Commit and push
