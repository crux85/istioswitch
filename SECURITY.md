# Security Policy

## Supported Versions

The following versions of `istioswitch` are currently supported with security updates. We strongly recommend always running the latest minor release of the latest major version.

| Version | Supported          |
| ------- | ------------------ |
| >= 0.2.x| :white_check_mark: |
| < 0.2.x | :x:                |

## Reporting a Vulnerability

We take the security of `istioswitch` seriously. If you discover a security vulnerability, please do not report it through public issues or pull requests.

Instead, please report it privately:

1. **Email:** Send your report to [carlo.cruciani@gmail.com](mailto:carlo.cruciani@gmail.com) (assuming standard handle, please adjust if needed).
2. **Details:** Include a clear description of the vulnerability, steps to reproduce, and any potential impact. Proof-of-concept code is highly appreciated.

We will try to acknowledge receipt of the vulnerability within 48 hours and provide an estimated timeline for a fix. Once the issue is resolved, we will publish a security advisory and credit you for the discovery (if desired).

## Out of Scope

The following issues are generally considered out of scope unless they demonstrate a significant impact on user security:

- Vulnerabilities in the downloaded `istioctl` binaries themselves (these should be reported directly to the Istio project).
- Issues that require an attacker to already have physical or remote shell access to the user's machine.
