# Maintainer publication transport

`tools/sync_mirror.py` publishes official packages directly to the self-hosted
A origin through `tools/publication_transport.py`. C provides the stable
`mgu.walle.pw` download entry. Skill installation choices and public URLs remain
independent of this maintenance transport.

The private configuration is `~/.config/mgu-mirror/publication-transport.json`,
overridable with `MGU_PUBLICATION_TRANSPORT`. It must have mode `0600`:

```json
{
  "schema": 1,
  "mode": "self-hosted",
  "driver": "/absolute/private/path/self-hosted/driver.py",
  "lock": "/absolute/private/path/publication.lock",
  "result": "/absolute/private/path/self-hosted/latest-success.json"
}
```

Use the same configuration and lock for the CN publisher. No OSS executable,
credentials, inventory or download endpoint participates in this mode. The
legacy `sync_oss.py` command refuses publication while this mode is enabled.

The driver pins C's active snapshot and obtains that exact verified file plan
from A, or from B when B already has it. The publisher stages changes locally and preserves all unmodified and
historical files. Official synchronization cannot write CN paths. New bytes
transfer directly to A over SSH. A verifies the complete snapshot before C
selects it. Publication then triggers A's replication service; a persistent
five-minute timer retries missed or failed triggers. C's process lock serializes
cooperating writers across maintenance hosts. A stale baseline stops activation.

A uses a dedicated, restricted SSH key and rsync to send only missing content
to B's private inbox. B verifies file size and SHA-256, assembles a complete
snapshot, validates its origin configuration and atomically advances its ready
pointer. Historical files remain available. C reads that pointer when falling
back to B, so a partial transfer is never exposed as a complete release.

The owner accepts eventual consistency: A publication does not wait for B.
While B is behind, it serves its last complete snapshot. If A fails before B
receives a newly advertised package, that new download can temporarily fail.
The public receipt's `replication` field and the service status distinguish
publication from backup convergence; `public_verified` alone does not certify
that B has caught up. Record persistent replication failures or lag over
30 minutes as maintenance issues; ordinary short pending states are expected.

After activation, verify public file metadata, root hashes and normal DNS/TLS.
Acceptance must contain `backend: self-hosted`, `oss_used: false`,
`public_verified: true`, this `transaction_id` and the exact triggering hash in
`manifests`. Only then advance the success pointer. A failed preparation keeps
the public entry; failed public acceptance restores the prior entry. An
incomplete run records `self-hosted-pending` and details in `edge.log`.

For recovery, inspect C's active snapshot and the immutable plans and full files
on A/B. Retry the reviewed publisher from that baseline; do not reuse a stale
transaction or use frozen OSS data as the current release. Preserve historic
snapshots and private operations backups. C remains a single entry node; an
entry outage requires restoring its configuration/certificate or separately
preparing a replacement entry. A/B failover covers origin failures only.

This transport does not delete OSS files, change DNS or channel versions,
access a vehicle, or expand official synchronization into CN releases.
