# Lilies module snapshot

This directory vendors the application source from
`/Users/zhonghaoyang/Code/agent/Lilies` on branch `refactor/lean-core`, based on
commit `dfc30ec` plus the tracked working-tree edits present when it was copied.

The UTOO-specific source adjustments are `basePath: '/lilies'` in the Next.js
configuration and the same prefix on the two direct `window.location`
navigations. Next's `Link` and router APIs apply the configured base path
automatically. The deployment build stages the Python package and the Next.js
standalone output under `backend/lilies`; UTOO then proxies `/lilies` and
`/api/platform` to the two loopback-only Lilies processes.
