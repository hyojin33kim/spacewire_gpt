# Generated Artifacts

Everything under this directory must be reproducible from version-controlled source artifacts and tools.

```text
generated/
├─ requirement_matrix/
├─ coverage_reports/
├─ interface_docs/
└─ diagrams/
```

## Rule

- Safe to delete and regenerate.
- Never use generated output as the only location of an engineering decision.
- Do not manually patch generated files to change protocol semantics or implementation contracts.
- If a generated artifact needs hand-maintained content, move that content to its authoritative source directory and regenerate the derived view.
