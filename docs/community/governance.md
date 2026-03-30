# Governance

## Project Scope

abovepy is a **Kentucky-specific geospatial workbench** for accessing and
analyzing LiDAR, DEM, and orthoimagery data from the KyFromAbove program. It is
not a generic STAC client framework.

## What Gets Accepted

Contributions that align with the following are welcome:

- Workflows for accessing and processing KyFromAbove data products
- Improvements to Kentucky GIS analysis capabilities
- Better support for KyFromAbove STAC collections and metadata
- Performance, reliability, or usability enhancements to existing features
- Documentation, tutorials, and examples using Kentucky data
- Bug fixes and test coverage improvements

## What Gets Rejected

The following types of changes fall outside project scope:

- General-purpose STAC client features unrelated to KyFromAbove
- Support for non-Kentucky data sources or catalogs
- Surveillance, tracking, or monitoring capabilities targeting individuals
- Features requiring authentication or private data access
- Changes that compromise the library's simplicity or public-data-only model

Maintainers will close out-of-scope proposals with an explanation. If you are
unsure whether an idea fits, open a discussion issue before investing time in
implementation.

## Decision-Making

- Routine contributions (bug fixes, docs, small features) are decided by
  maintainer review on the pull request
- Significant API changes, new modules, or architectural decisions are discussed
  in a GitHub Issue before implementation
- Governance, security policy, and responsible-use changes are maintainer-only
  decisions

## Maintainer Authority

Maintainers have final authority over:

- Accepting or rejecting contributions
- Release timing and versioning
- Enforcing the [Code of Conduct](CODE_OF_CONDUCT.md)
- Modifying governance and policy documents

See [MAINTAINERS.md](MAINTAINERS.md) for the current maintainer roster.
