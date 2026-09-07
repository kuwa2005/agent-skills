# Host paths (portable skills from oimo)

Use the paths for the agent host you are on. oimo paths are listed for reference when the same skill runs inside Open Mimo Code.

| Artifact | Cursor | OpenCode | oimo |
|----------|--------|----------|------|
| Personal skills | `~/.cursor/skills/` | `~/.config/opencode/skills/` | `~/.config/oimo/skills/` |
| Project skills | `.cursor/skills/` | `.opencode/skills/` | `.oimo/skills/` |
| Evolve / briefs dir | `~/.cursor/evolve/<project>/` or project `.cursor/evolve/` | `~/.config/opencode/evolve/<project>/` | `~/.oimo/evolve/<projectID>/` |
| Trajectory / session DB | — | — | `~/.local/share/oimo/oimo.db` (readonly SQL) |
| Project memory | `MEMORY.md` at repo root (convention) | same | same (+ oimo checkpoint files) |

When a skill mentions `.oimo/`, substitute your host's project skills directory unless you are on oimo.
