---
name: animus-supply-chain-security
description: Animus plugin supply-chain security — sha256 checksums, cosign keyless signature verification, signature policy (strict/warn/disabled), trusted-signers allowlists, audited TOFU org trust with revocation, plugin lockfiles and fail-closed semantics, lock verify tamper detection, and CI verification gates. Use for questions about plugin security, lockfile integrity, signature verification, trusting or revoking orgs, or detecting tampered plugin binaries.
user_invocable: false
auto_invoke: true
animus_version: "0.7.0-rc.18"   # animus CLI surface this skill targets
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
3. **Publisher TOFU (fail-closed since v0.7.0-rc.1)** — release-source
   installs from an org not in `~/.animus/trusted-orgs.yaml` prompt at the
   TTY. Non-interactively — and always with `ANIMUS_SERVER=1` — the install
   fails: `--yes`/`--force` do NOT auto-trust an unknown org; `--allow-org
   <OWNER>` is the explicit escape hatch (on `animus install`, `plugin
   install`, and the MCP install tool). The release-source gate runs BEFORE
   any download or `--manifest` probe.
4. **Lockfile (schema 2.0, v0.6.7)** — the install records per-target-triple
   integrity for EVERY published platform from the release's
   `SHA256SUMS.txt`: `targets: {triple → {archive_sha256,
   signature_bundle_sha256, installed_binary_sha256}}`, plus version and
   `installed_kind`, into the resolved `plugins.lock`; an unreadable lockfile
   fails the install closed first. A lock generated on one machine drives a
   verified `animus install --locked` on another platform.

Two further refusal guards: a plugin whose `manifest.name` differs from
the repo basename is refused (anti-typosquat; `--force` overrides), and
the reserved provider names (`claude`, `codex`, `gemini`, `opencode`,
`oai`, `oai-agent`, `oai-runner`) are an anti-squat guard: a canonical
`animus-provider-<reserved>` from the built-in trusted publisher
`launchapp-dev` installs with **no flag** (v0.6.10+); untrusted orgs and
`--path`/`--url` installs (owner unknown) are refused without
`--allow-shadow-builtin`. The guard also covers secondary-role providers
and the effective installed name (v0.7.0-rc.9).

## Signature Verification (cosign keyless)

No PEM keys. `launchapp-dev/animus-*` releases sign via GitHub Actions
OIDC + Sigstore Fulcio + the Rekor transparency log. Animus verifies
cryptographic validity (cert chain + Rekor entry), cert identity (SAN
must match the publisher's `identity_regex` — for `launchapp-dev`, the
standardized `release.yml` workflow under a `v*` tag), and the OIDC
issuer (`https://token.actions.githubusercontent.com`). Verification
shells out to the `cosign` binary; it must be on `$PATH` for `strict`.
The workflow-runner default releases are cosign-signed like any other
first-party plugin — `animus plugin install` verifies them identically
(pins advance; check the current one with `animus plugin outdated`).

Policy resolution is context-aware (v0.7.0-rc.1) — precedence: per-call
`--signature-policy` flag > `ANIMUS_PLUGIN_SIGNATURE_POLICY` env
(`strict`/`warn`/`skip`) > `plugins.signature_policy` global config >
`warn` default.

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

Every install records `signature_status`: `verified`, `unsigned`,
`invalid`, `untrusted_signer`, or `skipped`. Read it from
`animus plugin info <NAME>` (it also appears in `plugins.yaml`, but that
registry is a lock-derived projection regenerated on every mutating op —
treat the lock + `plugin info` as the audit surface, not the yaml);
`animus plugin list` does not render a signature column. Audit it
periodically; anything other than `verified` or an intentional `skipped`
deserves investigation.

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

Each entry pins version, `installed_kind`, and (schema 2.0, v0.6.7) a
`targets` map of per-platform integrity —
`{triple → {archive_sha256, signature_bundle_sha256,
installed_binary_sha256}}` — recorded for every published platform at
install time. Schema-1.0 entries (single artifact + bundle hash) migrate
with empty targets; re-install to upgrade them to full cross-platform
coverage.

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

**Commit `animus.toml` and the project lockfile.** `animus init` and
project installs write a `.animus/.gitignore` covering `plugins/` so
binaries stay out of VCS, while the committed `.animus/plugins.lock` —
the source of truth the derived `plugins.yaml` is regenerated from — pins
the repo's plugin set for every clone. `git clone && animus install
--locked` reproduces it exactly.

## CI Tamper Gate

With the manifest + lockfile committed, gate CI on integrity + drift:

```bash
animus install --locked              # reproduce the committed lock exactly; fails on manifest↔lock drift
animus plugin lock verify            # non-zero on any hash mismatch / missing binary
animus plugin outdated --exit-code   # non-zero when any plugin lags its pin
animus plugin outdated --exit-code --offline   # cached registry index, no network
```

Pre-populate `~/.animus/trusted-orgs.yaml` (or pass `--allow-org` — on
non-TTY/`ANIMUS_SERVER=1` runs `--yes` alone will NOT auto-trust an
unknown org) so non-interactive installs never block on the TOFU gate, and
set `ANIMUS_PLUGIN_SIGNATURE_POLICY=strict` (or pass `--signature-policy
strict`) on every CI install.

## Related Skills

- animus-plugin-operations — install, update, discovery, flavors, and troubleshooting how-tos.
- animus-configuration — project vs global plugin install scopes, env vars, and state layout.
