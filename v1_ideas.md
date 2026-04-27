# v1 ideas — parking lot

If a temptation to add something outside v0 scope appears during build, it goes here. v0 ships first.

Out of scope for v0 (do not build, capture ideas here):
- Code generation
- Claude Code subprocess orchestration
- Multiple artifact archetypes (only spec docs in v0)
- Cross-meeting memory beyond the user-authored `~/.instinct/context.md` (Amendment 4)
- Automatic context generation
- Agent-driven writes to `~/.instinct/context.md`
- Team learning
- Speaker fingerprinting beyond Deepgram defaults
- Linear / Slack / GitHub deployment
- Multi-user / team features
- Auth / accounts
- Web app or any non-macOS surface
- Calendar integration
- Pricing / billing
- Marketing site

## Ideas captured during build

- Tagger `references_prior` is unreliable on small fast models (gemma-3n-e2b-it). Few-shot examples taught the model to mimic id *shapes* (`u_a`, `u_08`) rather than copy from the rolling context verbatim. Mitigated by switching example ids to a clearly-illustrative form (`example_a01`) plus an explicit "do not reuse these ids" instruction. If the field stays unreliable in real-meeting fixtures, either remove it from `UtteranceTag` or post-process to validate the referenced `utterance_id` actually exists in the transcript before persisting.
