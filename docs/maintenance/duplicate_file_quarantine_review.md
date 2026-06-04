# Duplicate file quarantine review

This note records the review of the duplicate desktop-file quarantine created by
`OSW-MAINT-002_POST_PUBLIC_RELEASE_DUPLICATE_FILE_HYGIENE`.

Related work:

- OSW-MAINT-002
- GitHub Issue #1: Clean remaining local duplicate-file hygiene records

Quarantine path:

```text
artifacts/hygiene/duplicate_files_backup/OSW-MAINT-002/
```

## Summary

The OSW-MAINT-002 manifest was present and readable. It records 19 moved
duplicate desktop files. The quarantine archive itself remains under ignored
`artifacts/` paths and was not staged.

| Classification | Count |
| --- | ---: |
| Total reviewed | 19 |
| Exact duplicates | 0 |
| Divergent duplicates | 19 |
| Orphan duplicates | 0 |
| Unknown | 0 |
| High-risk secrets found | 0 |

All 19 quarantined files still have a current canonical path in the repository,
and all 19 still differ from their current canonical file content. The archive
therefore remains useful as historical review evidence rather than something to
restore automatically.

## Decision

- Quarantine retained.
- No files restored.
- No files permanently deleted.
- Archive remains ignored and local-only.
- Source, tests, docs, examples, tools, and workflow files remain free of
  tracked duplicate desktop files.

## Maintainer Action

Maintainers may keep the archive as local evidence, manually inspect it, or run a
later explicitly authorized permanent-delete gate. Do not restore duplicate
desktop files without a new issue that identifies the exact file, reason, and
review outcome.

## Safety Notes

- `git clean -fd` was not used.
- `git reset --hard` was not used.
- The public release, release assets, branch refs, and tags were not touched by
  this review.
- The lightweight sensitive-pattern scan found no high-risk private keys,
  GitHub tokens, OpenAI-style keys, or credential assignments. Generic words
  such as `token` or `secret` appear only in code/docs contexts and were not
  treated as credentials.

## Known Limitations

- Divergent files are preserved for historical review and are not part of the
  public release.
- The artifact archive is local and ignored. It may be absent in a fresh clone
  unless the local `artifacts/` directory is preserved.
- Ignored generated packaging metadata can still exist in local editable
  installs; it is runtime/build output and is not part of the tracked source
  duplicate-file hygiene decision.

## Next Options

- Keep the archive until maintainers no longer need local review evidence.
- Manually inspect the archive if a specific file appears valuable.
- Run a later authorized permanent-delete gate if maintainers decide the archive
  is no longer needed.
