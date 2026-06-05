# Code Signing And Installer Strategy

## Purpose

This page records the release-trust and installer strategy for OpenSolver
Workbench after the public `v0.1.3-rc1` prerelease. It is a planning document,
not evidence that signing, MSI, MSIX, Store distribution, or certificate
provisioning already exists.

OpenSolver Workbench remains educational/research software. Code signing and
installer packaging can improve publisher identity and installation experience,
but they do not validate engineering correctness or convert OSW into an
industrial-certified solver platform.

## Current v0.1.3-rc1 State

- Release state: public prerelease.
- Windows asset: unsigned portable ZIP.
- MSI installer: none.
- MSIX installer: none.
- Microsoft Store distribution: none.
- Authenticode code signing: none.
- Code-signing certificate: none configured.
- External solvers: optional and not bundled.
- Integrity assets: `SHA256SUMS.txt` and `release_asset_manifest.json`.
- Release smoke: local tooling and read-only GitHub Actions smoke are present.
- Artifact attestation: not yet part of the release workflow.

The current trust model is source-first and checksum-backed. Users can inspect
source, verify release asset checksums, review the manifest, and run release
asset smoke tooling. That is useful integrity evidence, but it is not a Windows
publisher identity.

## Definitions

| Mechanism | Meaning |
| --- | --- |
| SHA256 checksum | A cryptographic digest for one file. It detects accidental or malicious file changes only when the checksum itself is trusted. |
| Release asset manifest | A structured inventory of release assets, sizes, hashes, version, tag, source commit, platform, and limitations. |
| GitHub artifact attestation | Provenance metadata that can connect an artifact to a GitHub Actions workflow run and source repository. |
| Authenticode code signing | Windows publisher identity signing for executables, DLLs, MSI packages, and related files. |
| Timestamping | A signing-time proof that can let a signature remain valid after the certificate expires, when the signature was valid at signing time. |
| Portable ZIP | A zip archive users extract and run without a system installer. |
| MSI | Traditional Windows installer package. |
| MSIX | Modern Windows app package format, often used with Store or enterprise deployment flows. |
| Microsoft Store | Store distribution path with certification, policy, packaging, and update rules. |

## What Each Mechanism Does And Does Not Prove

Checksums and `release_asset_manifest.json`:

- Do detect whether downloaded files match the published release evidence.
- Do support repeatable asset smoke and archive safety checks.
- Do not identify a Windows publisher.
- Do not prevent SmartScreen or enterprise policy prompts.
- Do not validate engineering results.

GitHub artifact attestations:

- Can connect a release artifact to a GitHub workflow, repository, ref, and
  build provenance.
- Can strengthen integrity and supply-chain evidence.
- Do not replace Authenticode code signing.
- Do not create a Windows trusted publisher identity.
- Do not validate solver correctness.

Authenticode code signing:

- Can identify the publisher for Windows trust decisions.
- Can reduce friction for some Windows and enterprise environments when the
  certificate and reputation are established.
- Does not guarantee SmartScreen acceptance.
- Does not prove the software is correct or safe for engineering decisions.
- Requires protected certificate and signing-secret handling.

Installer packaging:

- Can improve installation, uninstall, Start Menu, and update workflows.
- Does not itself establish publisher identity unless signed.
- Does not bundle external solvers unless a separate, explicit bundling policy
  and license review are completed.

Microsoft Store distribution:

- Can provide a managed distribution path and Store certification flow.
- May include Microsoft-managed signing after Store certification.
- Requires MSIX packaging and Store policy decisions.
- Is not currently configured for OSW.

## Windows User Trust And SmartScreen Expectations

Unsigned public executables and installers may trigger Windows SmartScreen,
antivirus, enterprise application control, or browser download warnings. That is
expected for the current portable ZIP.

OSW must not claim that signing automatically avoids SmartScreen prompts. Even
a signed installer can need publisher reputation, policy allowances, and time.
EV certificates should not be treated as an instant Windows trust solution.

## Option Comparison

| Option | Benefits | Costs / risks | Fit |
| --- | --- | --- | --- |
| Stay portable ZIP only | Transparent, simple, no installer maintenance, easy smoke. | Unsigned warning remains; manual extraction; weaker Windows trust UX. | Good for `v0.1.3rc2` maintenance. |
| Portable ZIP + checksums + attestation | Adds provenance evidence without changing installer UX. | Requires GitHub Actions attestation workflow design; still not Authenticode signing. | Good research target before signing. |
| MSI without signing | Better install/uninstall UX. | Still unsigned; may create more warning friction than portable ZIP; extra maintenance. | Prototype only, not default public asset. |
| MSI with Azure Artifact Signing | Managed signing path for non-Store distribution where available. | Availability, onboarding, policy, cost, and CI secret handling must be decided. | Candidate for later release trust work. |
| MSI with OV certificate | Traditional CA route with publisher identity. | Legal identity, cost, renewal, private key protection, and reputation ramp-up. | Possible later if maintainers choose direct distribution. |
| MSIX / Microsoft Store | Store/enterprise-friendly packaging and possible Store-managed signing. | MSIX packaging work, Store account/policy, certification, update workflow. | Feasibility study for v0.1.4 or later. |
| Self-signed internal testing only | Useful for local signing pipeline tests. | Not trusted for public distribution; can mislead users if presented as public trust. | Internal CI/dev only. |

## Recommended Path

### v0.1.3rc2

- Keep the current unsigned Windows portable ZIP policy.
- Keep warnings visible: prerelease, unsigned, no MSI, no MSIX, no code
  signing, and no bundled external solvers.
- Keep publishing checksums, `release_asset_manifest.json`, and release asset
  smoke evidence.
- Research GitHub artifact attestations as a non-mutating provenance addition.
- Do not overwrite published release assets without a separate clobber gate.

### v0.1.4

- Prototype MSI or MSIX packaging in CI without making it the default public
  release asset.
- Keep unsigned prototype installers clearly labeled as prototypes.
- Evaluate GitHub artifact attestations for wheel, sdist, and portable ZIP
  artifacts.
- Decide whether installer work improves real user onboarding enough to justify
  maintenance cost.

### v0.2+

- Pursue public code signing only after maintainer identity, budget,
  certificate provider, geography, and secret-handling policy are decided.
- Prefer protected CI signing over local developer signing for release assets.
- Consider Azure Artifact Signing, OV certificate signing, or a Microsoft Store
  path based on maintainer constraints.

## Decision Prerequisites

- Maintainer legal identity and publisher name.
- Budget for certificate, Store account, or managed signing.
- Geography and provider availability.
- CI platform and protected environment policy.
- Secret storage and rotation plan.
- Release asset retention and rollback policy.
- Maintainer approval for any asset overwrite or signed replacement.

## Security Rules

- Do not commit certificates, private keys, PFX files, tokens, or signing
  credentials.
- Do not print signing secrets in logs.
- Do not keep public release signing credentials in a developer checkout.
- Perform signing only in a protected CI environment or explicitly controlled
  maintainer environment.
- Do not use `gh release upload --clobber` for signed replacements without an
  explicit clobber gate.
- Do not claim code signing until signing was actually performed and verified.
- Do not claim MSI, MSIX, or Store distribution until those packages are
  actually built and tested.

## Known Limitations

- There is no immediate SmartScreen guarantee.
- Code signing does not validate engineering correctness.
- Installer packaging does not validate solver correctness.
- External solvers remain optional and separate user-installed dependencies.
- Public docs on `develop` may be newer than the tagged `v0.1.3-rc1` source.

## Future Gates

- `OSW-MAINT-014_SIGNING_ATTESTATION_RESEARCH`
- `OSW-PACK-001_MSI_PROTOTYPE_NO_SIGN`
- `OSW-PACK-002_MSIX_FEASIBILITY`
- `OSW-PACK-003_SIGNED_INSTALLER_GATE`

Related docs:

- [Windows Portable ZIP](windows_portable_zip.md)
- [Release Asset Download Smoke](release_asset_download_smoke.md)
- [Windows Install](../install/windows.md)
- [Post-Public Release Checklist](post_public_release_checklist.md)
