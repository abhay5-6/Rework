# Security Policy

The Rework maintainers take the security of our multi-tenant collaboration platform seriously. We appreciate responsible disclosure of security vulnerabilities.

---

## Supported Versions

Only the latest release branch (`workspace` / `main`) receives security patches.

| Version / Branch | Supported |
| :--- | :--- |
| `workspace` / `main` | :white_check_mark: Supported |
| Older releases | :x: Not supported |

---

## Reporting a Vulnerability

> [!IMPORTANT]
> **Do NOT create public GitHub issues for security vulnerabilities.**

If you discover a security vulnerability (such as cross-tenant authorization leaks, CSRF bypass, remote code execution, token exposure, or privilege escalation), please report it privately:

- **Primary Contact**: Email security disclosures to `security@rework.dev` (or open a confidential GitHub Security Advisory on the repository).
- **Required Details**:
  - Description of the vulnerability and impact.
  - Step-by-step reproduction steps or proof-of-concept (PoC).
  - Target branch and commit hash tested.

---

## Response Timeline

- **Acknowledgement**: Within 48 hours.
- **Triage & Impact Assessment**: Within 5 business days.
- **Fix Release**: Critical issues patched within 7 business days.

---

## Safe Harbor & Disclosure Guidelines

- Do not attempt to access or modify data belonging to other users or organizations during testing.
- Test against your own local development setup or isolated staging environments.
- Give us reasonable time to patch the issue before making any public disclosure.
