# Contributing to DeeDee

Thanks for helping make DeeDee a practical CRM and AI-safety learning project.

## Start here

1. Fork the repository.
2. Read [the module guide](docs/modules.md), [architecture](docs/architecture.md), and [roadmap](docs/roadmap.md).
3. Choose one small module or documentation improvement.
4. Open an issue or pull request that describes the behavior and how you verified it.

## Contribution guidelines

- Keep domain rules independent of the web framework, database, and AI provider.
- Preserve the no-key, deterministic mock path.
- Add tests for behavior and failure paths.
- Keep changes small enough for a learner to follow.
- Use fictional data only. Never commit API keys, customer records, tokens, or private exports.
- For AI features, document which context is sent and how the user approves the result.
- Do not add automatic outbound messaging or unreviewed CRM writes.

## License

The repository owner has not selected a project license yet. Please do not assume a license that is not present.