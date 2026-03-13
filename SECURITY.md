# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in abovepy, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email **chris.lyons@ky.gov** with details
3. Include steps to reproduce, if possible
4. You will receive acknowledgment within 48 hours

## Scope

abovepy accesses publicly available geospatial data from the KyFromAbove S3 bucket. It does not handle authentication, store credentials, or process sensitive user data.

Potential security concerns include:
- URL injection in STAC API queries or TiTiler URL generation
- Path traversal in download file naming
- Dependency vulnerabilities

## Dependencies

abovepy pins minimum versions for its dependencies. We recommend keeping dependencies updated:

```bash
pip install --upgrade abovepy
```
