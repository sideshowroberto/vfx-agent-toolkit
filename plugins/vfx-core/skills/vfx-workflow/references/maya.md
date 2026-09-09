# Maya

Provenance: audited 2026-09 in the vfx-agent-toolkit-codex repository; its docs/,
codex/tests/ and codex/recipes/ hold the evidence records and probes named below.

Discover available operations from the actual bridge. The bundled implementation
loads mayatools; legacy agent tool names are not a callable interface contract.
Its commandPort uses MEL python wrappers, not a Python-mode port.

Connector setup describes environment precedence,
manual Maya startup, buffer limits and timeouts. The installer does not create
userSetup.mel. The repaired transport's NUL response framing is a candidate for
native verification. Unknown completion is not a reason to repeat scene changes.

Use returned node names when connecting/assigning shading groups, especially
when names collide. Query active color configuration and preserve selection and
export scope. A cmds preference can avoid an optional dependency; PyMEL is not
universally dead or deprecated.

Evidence: M1-M2 and
offline repairs. Native Maya and Windows installer
checks remain pending; do not describe the connector as production-verified.
