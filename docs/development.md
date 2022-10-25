Development Guide
==

> TBD flush out this doc before publicize the repo

[Digi setup guide](https://docs.google.com/document/d/1FRHhGNQhpXXiJHaSeAG42xxM-pstPW-tkiq3rNxPqlk/edit)

### Commit

Each commit should be signed with `git -s`.

Each commit message should have a commit tag with the following format: [TAG] Messsage. TAG should be one (or multiple) of:

- driver: Changes on the driver library.
- meta: Changes on the meta digis, e.g., lake, message brokers, space controllers.
- cli: Digi command line.
- doc: Documentation.
- api: Core APIs (`/api` and `/pkg` changes). 
- sidecar: Digi sidecar (e.g., neat, ctx).
- wip: Work-in-progress.

Or no tag: misc changes. In addition to the [common practice](https://www.kubernetes.dev/docs/guide/pull-requests/#commit-message-guidelines) of writing commit messages, note:

> The wip tag should always be placed at the end of all other tags in the same commit message.

> The first word of the commit message should be capitalized.

Example: `[doc][wip] Add development.md`.

