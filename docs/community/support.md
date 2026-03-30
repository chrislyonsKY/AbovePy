# Support

abovepy is an open-source project maintained on a best-effort basis. Clear,
reproducible, well-scoped reports are much easier to triage and resolve quickly.

## Bug Reports

Open a [GitHub Issue](https://github.com/chrislyonsKY/AbovePy/issues) with:

- abovepy version (`python -c "import abovepy; print(abovepy.__version__)"`)
- Python version and operating system
- Minimal code to reproduce the problem
- Full traceback or error output
- The product key and bounding box used, if applicable

## Feature Requests

Open a [GitHub Issue](https://github.com/chrislyonsKY/AbovePy/issues) describing:

- The use case or problem you are trying to solve
- How you would expect the API to work
- Any relevant KyFromAbove data products or workflows

Features should relate to KyFromAbove data access or Kentucky geospatial
workflows. See [GOVERNANCE.md](GOVERNANCE.md) for project scope.

## Security Vulnerabilities

**Do not** open a public issue. Email **chris.lyons@ky.gov** with details.
See [SECURITY.md](SECURITY.md) for the full disclosure policy.

## Data Quality Concerns

Issues with the underlying LiDAR, DEM, or orthoimagery data are managed by the
KyFromAbove program, not this library. If you suspect a data quality problem:

1. Note the product key, bounding box, and approximate area affected
2. Describe the issue (missing tiles, incorrect elevations, visual artifacts)
3. Check the [KyFromAbove website](https://kyfromabove.ky.gov) for known issues
4. If the problem appears to be in how abovepy retrieves or processes the data,
   open a GitHub Issue

## Code of Conduct

Community conduct concerns should be reported to **chris.lyons@ky.gov**.
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Response Times

This project is maintained alongside other responsibilities at the Kentucky
Division of Geographic Information. Response times vary, but you can generally
expect acknowledgment within one week for bug reports and security issues.
