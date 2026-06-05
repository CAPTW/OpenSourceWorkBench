# v0.1.3rc2 code signing / installer strategy closure evidence

Date: 2026-06-05

Related issue: #16, "Evaluate code signing and installer strategy"

Repo state:

- Head before closure evidence commit: `8aaae80cdcadd0793f2ce06e14adf430c3378e61`
- Head after closure evidence commit: the commit that adds this evidence note
- Timeout stabilization commit: `2884793660bf42fd4085e21bf725fdd8dec95e64`
- Strategy commit: `8aaae80cdcadd0793f2ce06e14adf430c3378e61`

Release identity:

- Public release: `v0.1.3-rc1`
- Release tag target: `a6e8d3a8211e02359841d10e1947e16ab847b132`
- Active development version: `0.1.3rc2.dev0`

## Strategy evidence

- Code signing strategy doc exists:
  `docs/release/code_signing_installer_strategy.md`
- Release trust docs tests exist:
  `tests/unit/test_release_trust_docs.py`
- The strategy doc records the current trust state.
- The strategy doc compares portable ZIP, checksum/manifest, GitHub artifact
  attestation, Authenticode signing, MSI, MSIX, Microsoft Store, OV/Azure
  signing, and self-signed internal testing paths.
- The strategy doc distinguishes file integrity, provenance, publisher identity,
  installer packaging, and engineering correctness.
- Release, install, roadmap, validation, and public README docs link to the
  strategy note.
- Public docs QA includes the strategy note in the required docs set.
- Security scan found no signing secrets, private keys, PFX files, certificates,
  or signing-token patterns outside ignored local reports.

## Current trust state

- Windows distribution is an unsigned portable ZIP.
- No MSI installer currently exists.
- No MSIX installer currently exists.
- No Authenticode code signing currently exists.
- External solvers are optional and not bundled.
- `SHA256SUMS.txt` and `release_asset_manifest.json` are available for the
  public prerelease assets.
- Release asset smoke tooling is available for fixture and release-download
  verification.

## Recommendation

v0.1.3rc2:

- Keep the unsigned portable ZIP.
- Keep warnings visible for prerelease status, unsigned ZIP, no MSI/MSIX, no
  code signing, and no bundled external solvers.
- Keep checksums, manifest, and release asset smoke tooling.

v0.1.4:

- Prototype MSI/MSIX or artifact-attestation work without making it the default
  public distribution path.
- Keep prototype packaging separate from any signing claim.

Later:

- Pursue public signing only after maintainer identity, budget, provider
  availability, protected secret handling, and release asset retention decisions.

## Known limitations

- The current release remains a prerelease.
- The portable ZIP remains unsigned.
- There is no MSI installer.
- There is no MSIX installer.
- There is no code signing.
- No signing provider has been selected.
- No maintainer legal identity or budget decision has been made.
- External solvers remain optional local dependencies and are not bundled.
- Code signing would not validate engineering correctness.

## Decision

Issue #16 is eligible for closure if the local QA gate passes and the GitHub
release/tag state remains unchanged. Closing #16 records completion of strategy
documentation only; it does not claim signing, MSI/MSIX packaging, Microsoft
Store distribution, or release asset replacement.

## Next recommended action

- `OSW-PACK-001_MSI_PROTOTYPE_NO_SIGN`, or
- #12 v0.1.4 feature selection planning.

