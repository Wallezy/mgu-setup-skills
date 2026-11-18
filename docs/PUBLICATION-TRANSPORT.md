# Maintainer publication transport

`tools/sync_oss.py` supports a verified self-hosted download entry through
`tools/publication_transport.py`. It does not change Skill installation choices
or the public download domain.

The private configuration is `~/.config/mgu-mirror/publication-transport.json`,
overridable with `MGU_PUBLICATION_TRANSPORT`. It must have mode `0600`:

```json
{
  "schema": 1,
  "mode": "oss-with-edge",
  "driver": "/absolute/private/path/driver.py",
  "lock": "/absolute/private/path/publication.lock",
  "result": "/absolute/private/path/latest-success.json"
}
```

Use the same configuration and lock for the CN publisher. OSS is the
authoritative staging and rollback store; maintainer verification reads its
fixed HTTPS endpoint. All normal permission, dependency, immutable package,
hash, content type and cache checks remain required.

After OSS acceptance, the driver copies the published site to A and B, including
existing CN bytes without creating or promoting a CN release. Both origins must
hold the same verified immutable snapshot before C can activate it. The driver
verifies C using the production TLS name and records `public_verified: true`
plus `manifests`, a mapping from object paths to exact SHA-256 values.

The official publisher only succeeds when that acceptance contains its
`mgu/mirror-manifest.json` hash. Otherwise `result.json` records `edge-pending`
and `edge.log` contains the failure. The success pointer remains unchanged.
Inspect and repair the failed stage, then rerun the reviewed publication or
its bound driver. Do not roll OSS back behind a completed edge snapshot.

DNS remains an explicit owner operation. Neither transport enables vehicle
access, changes channel versions, deletes historical objects, nor widens the
official source synchronization scope.
