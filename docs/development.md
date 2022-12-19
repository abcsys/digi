# Development Guide

The repo contains a single `main` branch. For contribution, please fork this repo and submit a PR. 

## Prerequisites

`Go`:  >= 1.15
`Python`: >= 3.7
`Docker`: >= 20.10

Digi driver library: `make python-digi` 

## Workflow
Set up the fork:

1. Make your own [**fork**](https://github.com/digi-project/digi/fork) of the project.
2. Add the [upstream](https://github.com/digi-project/digi.git) to list of remotes; or alternatively use the Sync Fork feature on GitHub. 

Submit a Pull Request (PR):

1. Make sure your fork is up to date before every commit (e.g. with `git pull`). 
2. Work on your code. 
3. [Commit](development.md#commit) and push to your fork, not the upstream. 
4. Open a [Pull Request](https://github.com/digi-project/digi/compare) and add the appropriate reviewer(s) for you pull request.
5. Your PR should pass all CI tests (TBD see #26)

Please read [Forking & Pull Requests](https://gist.github.com/Chaser324/ce0505fbed06b947d962) for a general overview of how forking and pull requests works. 

## Commit

Your commit needs to be signed with `git commit -s`.
Each commit message is preferred to have a commit tag with the following format: [TAG] Messsage. TAG should be one (or multiple) of:

- driver: Changes on the driver library.
- meta: Changes on the meta digis, e.g., lake, message brokers, space controllers.
- cli: Digi command line.
- doc: Documentation.
- api: Core APIs (`/api` and `/pkg` changes). 
- sidecar: Digi sidecar (e.g., neat, ctx).
- wip: Work-in-progress.

Or no tag for misc changes. In addition to the [common practice](https://www.kubernetes.dev/docs/guide/pull-requests/#commit-message-guidelines) of writing commit messages, note:

> The wip tag should always be placed at the end of all other tags in the same commit message.
> The first word of the commit message should be capitalized.

Example: `[doc][wip] Add development.md`.

