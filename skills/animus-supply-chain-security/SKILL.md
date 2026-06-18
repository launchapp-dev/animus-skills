---
name: animus-supply-chain-security
description: Animus plugin supply-chain security — sha256 checksums, cosign keyless signature verification, signature policy (strict/warn/disabled), trusted-signers allowlists, audited TOFU org trust with revocation, plugin lockfiles and fail-closed semantics, lock verify tamper detection, and CI verification gates. Use for questions about plugin security, lockfile integrity, signature verification, trusting or revoking orgs, or detecting tampered plugin binaries.
user_invocable: false
auto_invoke: true
animus_version: "0.5.21"   # animus CLI surface this skill targets
---

# Supply-Chain Security

Deep reference for the integrity controls on `animus plugin install` and
the post-install tamper surfaces. For install/update how-tos, see
animus-plugin-operations.

Threat model in brief: the sha256 checksum catches a corrupted or
substituted artifact; cosign keyless signature verification catches a
binary not published by a trusted publisher's release pipeline; the TOFU
org prompt forces an explicit operator decision on first contact with a
new GitHub org; the lockfile detects post-install tampering and drift on
already-installed binaries.

## The Install Integrity Pipeline

Every install — global or `--project` — runs the identical pipeline:

1. **sha256 checksum** — release installs verify the published checksum;
   `--url` installs REQUIRE `--sha256 <hex>`; `--path` installs may pass
   it optionally. Mismatch fails the install.
2. **Cosign signature policy** — keyless verification of the
   `<asset>.bundle` published next to the release asset (see below).
3. **Publisher TOFU** — release-source installs from an org not in
   `~/.animus/trusted-orgs.yaml` prompt at the TTY, or fail
   non-interactively (use `--allow-org <OWNER>` / `--yes`).
4. **Lockfile** — the install appends `sha256(artifact)` +
   `sha256(signature_bundle)` + version to the resolved `plugins.lock`;
   an unreadable lockfile fails the install closed first.

Two further refusal guards: a plugin whose `manifest.name` differs from
the repo basename is refused (anti-typosquat; `--force` overrides), and
a provider plugin claiming a built-in tool name (`claude`, `codex`,
`gemini`, `opencode`, `oai-runner`) is refused without
`--allow-shadow-builtin`.

## Signature Verification (cosign keyless)

No PEM keys. `launchapp-dev/animus-*` releases sign via GitHub Actions
OIDC + Sigstore Fulcio + the Rekor transparency log. Animus verifies
cryptographic validity (cert chain + Rekor entry), cert identity (SAN
must match the publisher's `identity_regex` — for `launchapp-dev`, the
standardized `release.yml` workflow under a `v*` tag), and the OIDC
issuer (`https://token.actions.githubusercontent.com`). Verification
shells out to the `cosign` binary; it must be on `$PATH` for `strict`.
The current workflow-runner default pin (v0.4.5) ships a cosign-signed
runner release — `animus plugin install` verifies it like any other.

Policy modes via `--signature-policy <MODE>`:

- `strict` — fail closed on missing, invalid, or untrusted-signer
  signatures (and on missing `cosign`). Recommended for production;
  legacy alias `--require-signature`.
- `warn` — **current default.** Verification still runs and the result
  is recorded, but failures log a stderr warning and the install
  proceeds. Alias `--allow-unsigned`.
- `disabled` — skip verification (local `--path` builds, air-gapped
  flows). Legacy alias `--skip-signature`.

```bash
animus plugin install --signature-policy strict launchapp-dev/animus-provider-claude
```

Every install records `signature_status` in the plugin registry
(`~/.animus/plugins.yaml`): `verified`, `unsigned`, `invalid`,
`untrusted_signer`, or `skipped`. Inspect it directly in `plugins.yaml` (it is
also in the `animus plugin info <NAME>` output); `animus plugin list`
does not render a signature column. Audit it periodically; anything other than
`verified` or an intentional `skipped` deserves investigation.

### trusted-signers.yaml

Optional allowlist at `~/.animus/trusted-signers.yaml` (override:
`--trusted-signers <PATH>`, or `$ANIMUS_TRUSTED_SIGNERS` per the
plugin-signing architecture doc):

```yaml
trusted_signers:
  - identity: "launchapp-dev/animus-*"
    issuer: "https://token.actions.githubusercontent.com"
```

`identity` is a glob matched against `<owner>/<repo>`. **Missing or
empty file = permissive**: any signature whose cert chain validates
against the install source's own repo identity is accepted. Populate it
to pin installs to a known publisher set.

## Audited TOFU Org Trust

`~/.animus/trusted-orgs.yaml` stores rich per-org records: `trusted_at`
(RFC3339), `decided_by` (`interactive-prompt` | `yes` | `allow-org` |
`built-in`), and `first_plugin` (the `owner/repo` that triggered the
prompt). Legacy bare-string entries still load and are rewritten in the
rich shape on the next grant. The changelog also documents an
`$ANIMUS_TRUSTED_ORGS` override for the store location (changelog-only;
not in the configuration reference).

```bash
animus plugin trust list           # current + revoked orgs, timestamps, decided_by
animus plugin trust list --json
animus plugin revoke-trust evil-org
```

Revocation stamps a `revoked_at` tombstone instead of deleting the
record — the audit trail survives and the next install from that org
re-prompts (a deleted record would silently re-trust under `--yes`).
Re-trusting clears the tombstone and stamps fresh `trusted_at` /
`decided_by`. Revoking emits a `trust_org_revoked` audit event. The
built-in `launchapp-dev` anchor cannot be revoked.

Successful release-source installs stamp an `org_trust` block (`org`,
`trusted_at`, `decided_by`) into the install JSON envelope and the
`plugin_install` audit line, so "when did we trust this org?" is
answerable from the install record itself.

TOFU is a convenience trust ledger, not a cryptographic anchor — cosign
verification is the authenticity control.

## Lockfiles

Two roots, each paired with an install dir and registry:

- Global: `~/.animus/plugins.lock` ↔ `~/.animus/plugins/`
- Project: `<project>/.animus/plugins.lock` ↔ `<project>/.animus/plugins/`
  (written by `animus plugin install --project`; preferred when
  `.animus/` exists)

Each entry pins `sha256(artifact)`, `sha256(signature_bundle)`, version,
and the `installed_kind`.

```bash
animus plugin lock list [--lockfile <PATH>] [--json]
animus plugin lock verify [--lockfile <PATH>] [--plugin-dir <PATH>] [--json]
```

`lock verify` re-hashes every installed binary. By default it sweeps
BOTH roots: global entries against the global dir, project entries
against the project dir with a global-dir fallback for legacy entries.
Each result carries `scope` (`global` / `project` / `explicit`);
`--lockfile <PATH>` restricts to one file. Any mismatch or missing
binary exits non-zero.

**Fail-closed:** `animus plugin install` and `install-defaults` REFUSE
when the resolved lockfile exists but cannot be parsed or has an
incompatible `schema_version`. Remediate by restoring the file from
version control/backup, or re-run with `--force-rewrite-lockfile` —
which discards the file and rebuilds from this install onward.
**Security caveat:** rewriting drops the recorded sha256 integrity
history, so tamper that predates the rewrite becomes undetectable; use
it only after confirming the damage was not tampering.

**Commit the project lockfile.** `animus init` and project installs
write a `.animus/.gitignore` covering `plugins/` so binaries stay out of
VCS, while the committed `.animus/plugins.lock` pins the repo's plugin
set for every clone.

## CI Tamper Gate

With the project lockfile committed, gate CI on integrity + drift:

```bash
animus plugin lock verify            # non-zero on any hash mismatch / missing binary
animus plugin outdated --exit-code   # non-zero when any plugin lags its pin
animus plugin outdated --exit-code --offline   # cached registry index, no network
```

Pre-populate `~/.animus/trusted-orgs.yaml` (or pass `--allow-org` /
`--yes`) so non-interactive installs never block on the TOFU prompt, and
pass `--signature-policy strict` on every CI install.

## Related Skills

- animus-plugin-operations — install, update, discovery, flavors, and troubleshooting how-tos.
- animus-configuration — project vs global plugin install scopes, env vars, and state layout.
