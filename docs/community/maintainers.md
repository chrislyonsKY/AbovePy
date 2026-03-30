# Maintainers

## Current Maintainers

| Name | Role | Contact |
|------|------|---------|
| Chris Lyons | Lead maintainer | chris.lyons@ky.gov |

## Responsibilities

Maintainers are responsible for:

- Reviewing and merging pull requests
- Triaging issues and feature requests
- Cutting releases and publishing to PyPI
- Enforcing the [Code of Conduct](CODE_OF_CONDUCT.md)
- Ensuring changes align with [project governance](GOVERNANCE.md)

## Review Policy

- All pull requests require at least one maintainer review before merge
- CI must pass (lint, type check, and test matrix across ubuntu/macos/windows
  on Python 3.11--3.13)
- Changes affecting public API require documentation updates
- Security-sensitive changes receive extra scrutiny

## Release Process

1. Update `CHANGELOG.md` with the release notes
2. Bump the version in `pyproject.toml`
3. Commit with message: `vX.Y.Z`
4. Tag the commit: `git tag vX.Y.Z`
5. Push the tag: `git push origin vX.Y.Z`
6. GitHub Actions builds and publishes to PyPI automatically
7. Create a GitHub Release from the tag with changelog excerpt

## Becoming a Maintainer

Maintainer status is granted to contributors who demonstrate:

- Sustained, high-quality contributions over multiple releases
- Understanding of KyFromAbove data products and Kentucky GIS workflows
- Familiarity with the codebase architecture and design decisions
- Alignment with the project's scope and governance principles

If you are interested, start by contributing through issues and pull requests.
Maintainer invitations are extended at the discretion of existing maintainers.
