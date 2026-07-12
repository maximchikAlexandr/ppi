## Description

<!-- Brief description of the change. -->

## Checklist

- [ ] Generated contract artifacts are fresh (`make check-generated` passes)
- [ ] Generated artifacts match committed copies (no stale files)
- [ ] Handwritten facades are the only import path for runtime code consuming generated artifacts
- [ ] No manual edits to generated files
- [ ] Tests pass (`uv run pytest`)
- [ ] Spec 011 scope freeze respected: no storage/generation, handler generation, or plugin loading
