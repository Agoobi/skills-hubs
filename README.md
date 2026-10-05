# Agoobi Skills Hub

Open-source Vietnamese skills for AI agents. Coquifly reads `manifest.json` at a pinned Git commit and installs only skills explicitly enabled by an administrator.

## Contributing

1. Add one directory under `skills/<id>`.
2. Add a `SKILL.md` whose frontmatter `name` exactly matches `<id>`.
3. Add the skill to `manifest.json`; drafts not listed there stay private.
4. Keep `description` to one sentence and at most 60 characters. Put longer UI copy in `summary`.
5. Run `python scripts/validate.py` before opening a pull request.

Skill directories may also contain `assets/`, `references/`, `scripts/`, and `templates/`. Do not commit secrets, generated artifacts, symlinks, submodules, or executable payloads.

## License

MIT. Individual contributions must be compatible with that license.
