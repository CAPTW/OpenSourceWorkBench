# Report Asset Runtime Path Native Deferral

## Status

- Prior policy: `SELECT_CONTINUED_NATIVE_DEFERRAL`
- Closure outcome: `SELECT_NATIVE_DEFERRAL_CLOSURE_DOCUMENTATION_DESIGN`
- Lifecycle status: `DEFERRED_RETAINED`
- Canonical phrase: **Native resolution: `DEFERRED_RETAINED`.**
- Native implementation allowlist: empty
- Native-test allowlist: empty
- Selected next gate: `OSW-3D_WORKSPACE_REPORT_ASSET_RUNTIME_PATH_RESOLVER_FILESYSTEM_SERVICE_NATIVE_DEFERRAL_TRACKED_DOCUMENTATION_REVIEW_AND_COMMIT_READINESS`

`DEFERRED_RETAINED` means production native report-asset availability
resolution is unsupported and unscheduled. Accepted non-native contracts and
their evidence remain retained, and reopening requires a qualifying trigger
plus a separately authorized gate. It does not mean complete, supported,
validated, production-ready, temporarily broken, implementation pending, best
effort, safe local only, provider silent, sandboxed, or race-free.

## Canonical Product Claim

**Native resolution: `DEFERRED_RETAINED`.** OSW preserves typed report-asset path intent and performs schema round-trip, lexical validation, lexical classification, and path-private projection without filesystem access. Native report-asset availability resolution is unsupported. Typed `external_absolute` and `project_relative` references therefore remain unresolved and produce placeholders until the user explicitly relinks the record or a separately authorized resolver exists. “Unsupported” is not a finding that a referenced asset is missing, unreadable, unsafe, or nonexistent, and it is not a claim of locality, containment, link safety, provider silence, sandboxing, or race-free consumption. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

## User-Facing GUI And Report Status

**Native availability resolution is unsupported (`DEFERRED_RETAINED`); this reference was not checked.** It may or may not exist or be readable. The report will keep an unresolved placeholder. You may use “Relink selected screenshot…” to explicitly choose a replacement reference; relinking is an existing compatibility action, changes project metadata only after confirmation, and does not prove locality, containment, link safety, provider silence, sandboxing, or race-free consumption. Saving the Project remains separate and explicit. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

## Developer And Architecture Boundary

**`DEFERRED_RETAINED`: native report-asset availability resolution is unsupported and unscheduled.** `osw.core` may preserve typed intent, apply pure lexical rules, build lexical candidates from an explicitly supplied context, and emit path-private projections; it must not turn those results into filesystem facts. `effective_path` remains unavailable and canonical containment remains unknown without a separately authorized native service. The strict zero-provider-contact-before-attestation invariant, empty native implementation allowlist, and empty native-test allowlist remain in force. Unsupported does not mean missing, unreadable, unsafe, or nonexistent. Existing relink and legacy compatibility paths remain outside this typed-resolver native policy and are not certified provider-silent.

## Known Limitation

**Native report-asset availability resolution is unsupported (`DEFERRED_RETAINED`).** OSW can preserve and lexically validate a typed path reference without accessing the filesystem, but it cannot establish existence, regular-file status, readability, locality, containment, link/reparse safety, provider silence, sandboxing, or race-free consumption. Typed unresolved references remain visible as placeholders and can be explicitly relinked. This limitation does not mean the referenced asset is missing, unreadable, unsafe, or nonexistent. Legacy compatibility behavior is separate and is not certified provider-silent.

## Roadmap And Current-Cycle Status

**Native report-asset filesystem resolution is `DEFERRED_RETAINED`.** Production native resolution is unsupported, the strict zero-provider-contact-before-attestation invariant remains unchanged, and no implementation is scheduled. Accepted schema, lexical, privacy, stale-binding, relink, and unresolved-placeholder contracts and their evidence remain retained. The status is not an implementation failure or a native-support claim; reopening requires a qualifying trigger and a separately authorized policy/architecture gate. Branches, worktrees, and evidence remain retained until a separate cleanup decision. Legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

## Validation-Matrix Status

**`DEFERRED_RETAINED` / documented non-native evidence only.** Automated evidence covers schema round-trip, pure lexical behavior, safe projection, stale-target protection, explicit relink semantics, and deterministic unresolved placeholders. Native availability, locality, containment, readability, link/reparse safety, provider silence, sandboxing, and race-free consumption are unsupported and were not tested. A skipped or absent native test is not a pass, and unsupported is not a finding that an asset is missing, unreadable, unsafe, or nonexistent. Legacy compatibility paths are outside the typed-resolver policy and carry no provider-silence claim.

## Release-Note Entry

**Report-asset native resolution status — `DEFERRED_RETAINED`.** OSW retains typed report-asset path intent, lexical validation/classification, path-private status projections, explicit relink behavior, and unresolved report placeholders. Native availability resolution remains unsupported and no native resolver, service, adapter, fake adapter, broker, or native test matrix was added. This status does not remove an existing supported native feature and does not mean a referenced asset is missing, unreadable, unsafe, or nonexistent. It makes no locality, containment, link-safety, provider-silence, sandboxing, or race-free claim; legacy compatibility paths remain outside the typed-resolver policy and are not certified provider-silent.

## Reopening-Policy Statement

**`DEFERRED_RETAINED` may be reopened only by a separately authorized gate after a qualifying trigger supplies new evidence or explicitly changes policy.** Qualifying triggers are new official platform documentation or a documented primitive that materially addresses the blocked invariant; an explicit decision to change the invariant; an authorized trusted-authority architecture with an owner, lifecycle, deployment model, and evidence plan; an authorized relaxed provider-contact policy with revised privacy, consent, claim, and threat boundaries; or a material new product requirement. Heuristics, one-machine success, `DRIVE_FIXED`, device or volume identifiers, repeated metadata checks, fake adapters, undefined helper processes, user consent treated as locality proof, available implementation time, or dislike of the unsupported message are insufficient. Until reopening succeeds, lexical handling remains distinct from filesystem facts, native availability remains unsupported, unresolved placeholders and explicit relink remain available, and legacy paths carry no provider-silence claim.

## Legacy Compatibility Caveat

**Legacy compatibility paths are outside the typed-resolver `DEFERRED_RETAINED` native policy and are not certified provider-silent.** Their existing path checks or relink behavior may access the filesystem; lexical handling in the typed contract does not convert that behavior into proved filesystem facts. The absence of a new typed native resolver neither validates nor expands legacy behavior, and “unsupported” does not mean a legacy target is missing, unreadable, unsafe, or nonexistent. This closure neither removes nor expands legacy behavior. Any legacy-path security review requires its own authorized gate; explicit relink and unresolved-placeholder behavior remain available within their existing boundaries.

## Supported Non-Native Workflow Matrix

| Capability | Classification | Filesystem access | Native claim |
| --- | --- | --- | --- |
| Durable typed path intent | supported | none | no |
| Schema serialization/round-trip | supported | no target access | no |
| Pure lexical validation | supported | none | no |
| Pure lexical classification | supported | none | no |
| Path-private projections | supported | none | no |
| Existing stale-context/binding protection | supported | none for token/snapshot checks | no |
| Explicit relink | supported compatibility action | existing `Path.is_file()` checks; provider silence unproved | no |
| Unresolved placeholders | supported | none in pure bridge | no |
| Deterministic unresolved report behavior | supported | no native target access in bridge | no |
| Retained evidence inspection | evidence-only | repository evidence reads | no |
| Fake/simulated behavior | evidence-only, unimplemented | none implemented | no |

Fake or simulated behavior is not implemented product-native support.

## Unsupported Native-Fact Matrix

Every fact below is unsupported. For every row, unsupported is not a negative
observation about the target; the strict invariant blocks trustworthy native
observation; heuristic or one-machine behavior is insufficient; and reopening
requires authoritative, fact-specific evidence or an explicitly changed
policy.

| Native fact | Classification | Required reopening basis |
| --- | --- | --- |
| Existence | unsupported | authorized attestation and bounded native observation with explicit error mapping |
| Regular-file status | unsupported | attested handle-based type checks with link/reparse policy |
| Readability | unsupported | authorized post-attestation open policy with privacy and safe-error evidence |
| Stable readability | unsupported | retained-handle or lease-based consumption with identity/revalidation evidence |
| Canonical containment | unsupported | trusted root anchor, handle-relative walk, identity comparison, and adversarial evidence |
| Same-volume containment | unsupported | authoritative identity semantics atomically bound to root and target handles |
| Symlink safety | unsupported | platform-complete traversal policy, escape tests, and race analysis |
| Junction safety | unsupported | platform-complete traversal policy, escape tests, and race analysis |
| Reparse-point safety | unsupported | official primitive and fail-closed admitted-tag matrix with native evidence |
| Provider silence | unsupported | official provider-silent primitive or explicit invariant change |
| Network silence | unsupported | official no-network guarantee for the full observation sequence |
| Fixed-local storage | unsupported | authoritative fixed-local primitive covering virtual/provider-backed cases |
| Non-removability | unsupported | authoritative guarantee bound to the handle/device lifecycle |
| Cloud/HSM/recall exclusion | unsupported | provider/filter-complete exclusion or explicitly changed contact policy |
| Device stability | unsupported | atomic retained authority with revocation, expiry, replay, and replacement evidence |
| Mount stability | unsupported | atomic retained authority with revocation, expiry, replay, and replacement evidence |
| Sandboxing | unsupported | separately authorized isolation architecture and escape/threat evidence |
| Race-free consumption | unsupported | handle-relative atomic consumption or an explicitly bounded residual race |
| Content authenticity | unsupported | separate provenance/signature policy and verification evidence |
| Malware safety | unsupported | separate scanning/isolation policy and validation evidence |

## Claim Boundary

OSW may claim durable typed intent, schema round-trip, pure lexical validation
and classification, lexical candidate construction from explicit context,
path-private projections, stale-state protection, explicit compatibility
relink, and deterministic unresolved placeholders. An unresolved placeholder
is not successful native resolution.

OSW may not claim native existence, file type, readability, stable readability,
locality, canonical or same-volume containment, symlink/junction/reparse safety,
provider or network silence, fixed-local storage, non-removability,
cloud/HSM/recall exclusion, device or mount stability, sandboxing, race-free
consumption, content authenticity, malware safety, production readiness, or
certification.

## Retention And Evidence

- The runtime-contract branch/worktree is retained reference evidence, not
  active native implementation.
- The path-kind branch/worktree is retained reference evidence, not active
  native implementation.
- Both retained worktrees remain registered until a separate authorized cleanup
  decision inventories unique evidence and provenance.
- Local `.codex/reports/` evidence remains untracked, unstaged, local-only, and
  retained in place.
- Retained local evidence is not a backup, implementation, validation, or
  authorization claim.
- Retention does not authorize merging, pushing, deletion, archival, cleanup,
  probing, architecture work, implementation, or native validation.

The retained evidence chain is referenced by these local paths:

- `.codex/reports/planning/OSW-3D_WORKSPACE_REPORT_ASSET_RUNTIME_PATH_RESOLVER_FILESYSTEM_SERVICE_NATIVE_DEFERRAL_CLOSURE_AND_DOCUMENTATION_DESIGN.md`
- `.codex/reports/planning/OSW-3D_WORKSPACE_REPORT_ASSET_RUNTIME_PATH_RESOLVER_FILESYSTEM_SERVICE_NATIVE_DEFERRAL_CLOSURE_AND_DOCUMENTATION_DESIGN.json`
- `.codex/reports/project_sources/2026-07-04__PLAN__3D_WORKSPACE_REPORT_ASSET_RUNTIME_PATH_RESOLVER_FILESYSTEM_SERVICE_NATIVE_DEFERRAL_CLOSURE_AND_DOCUMENTATION_DESIGN.md`
- `.codex/reports/handoff/OSW-3D_WORKSPACE_REPORT_ASSET_RUNTIME_PATH_RESOLVER_FILESYSTEM_SERVICE_NATIVE_DEFERRAL_CLOSURE_AND_DOCUMENTATION_DESIGN_SELECTED_NEXT_GATE_PROMPT.md`

## Reopening Criteria

Acceptable reopening triggers are limited to:

1. Materially new official platform documentation or a documented primitive
   that addresses the blocked invariant.
2. A separately authorized decision explicitly changing the invariant.
3. A separately authorized trusted-authority architecture with a named owner,
   lifecycle, deployment model, and evidence plan.
4. A separately authorized relaxed provider-contact policy with revised claim,
   privacy, consent, logging, and threat boundaries.
5. A material new product requirement sufficient to justify reopening policy
   analysis.

Insufficient triggers include:

- observed success on one machine;
- `DRIVE_FIXED`;
- DOS-device target prefixes;
- volume GUIDs;
- device numbers;
- storage-bus classifications;
- removal-policy hints;
- repeated metadata or pathname checks;
- fake adapters;
- helper processes without a defined authority;
- user consent treated as locality proof;
- available implementation time;
- dislike of an unsupported-status message.

Documenting a trigger does not authorize architecture, implementation, probing,
or validation.
