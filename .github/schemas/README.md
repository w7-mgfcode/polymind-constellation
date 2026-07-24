# Pinned GitHub issue schemas

These schemas are vendored from
[SchemaStore](https://github.com/SchemaStore/schemastore) at repository commit
`144ba338f6931f2678daa7267e1cec6f3b1f21b3`. SchemaStore is licensed under
Apache-2.0.

| Local file | Upstream path | Git blob | SHA-256 |
| --- | --- | --- | --- |
| `github-issue-forms.schema.json` | `src/schemas/json/github-issue-forms.json` | `08374ac76d24faaae2fcdb323fa7de547508a6ae` | `c2722dbf00334ce4fdeffa960b8c9047caf4f1cbb8f3809663f4d604b1d3ae76` |
| `github-issue-config.schema.json` | `src/schemas/json/github-issue-config.json` | `b46556bb04a5c975d0bcc09511a518607fbcb69a` | `899e718f4b8c965413b07ec63d8f089792a10c42409270db560b9a7ec0224a5a` |

`tests/test_repository_governance.py` checks these digests before using the
schemas. Update a schema only by reviewing a new immutable upstream blob,
recording its source and SHA-256 here, and updating the matching test constant.
