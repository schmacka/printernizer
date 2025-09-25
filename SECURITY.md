# Security Policy

## Supported Versions

We provide security updates for the following versions of Printernizer:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Printernizer, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security issues by sending an email to:
**sebastian@porcus3d.de**

Include the following information:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Investigation**: We will investigate and validate the issue within 5 business days
- **Response**: You will receive regular updates on our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days
- **Disclosure**: We will coordinate with you on responsible disclosure timing

### Security Measures in Printernizer

#### Network Security
- All printer communications use encrypted protocols where available
- API endpoints include input validation and sanitization
- CORS protection prevents unauthorized cross-origin requests
- Rate limiting protects against denial-of-service attacks

#### Data Protection
- Sensitive printer credentials are stored securely
- Database connections use parameterized queries to prevent SQL injection
- File uploads are validated and sandboxed
- GDPR compliance measures protect user data

#### Authentication & Authorization
- Secure session management
- Input validation on all user-provided data
- Protection against common web vulnerabilities (XSS, CSRF)

#### 3D Printer Security
- Printer API keys and credentials are encrypted at rest
- Network communications to printers are validated
- File downloads from printers are scanned and validated
- Access to printer functions is properly authorized

### Security Best Practices for Users

#### Installation Security
- Always download Printernizer from official sources
- Verify checksums when available
- Use virtual environments to isolate dependencies
- Keep your installation updated

#### Network Security
- Use strong passwords for printer access codes
- Secure your local network where printers are connected
- Consider network segmentation for 3D printers
- Monitor network traffic for suspicious activity

#### Configuration Security
- Store sensitive configuration in environment variables
- Use strong API keys for printer connections
- Regularly rotate printer access codes
- Limit access to the Printernizer interface

#### Operational Security
- Regularly backup your configuration and data
- Monitor logs for suspicious activity
- Keep printer firmware updated
- Review user access periodically

### Known Security Considerations

#### 3D Printer Networks
- Most 3D printers use unencrypted communication protocols
- Printer web interfaces may have limited security features
- Network isolation is recommended for printer communications

#### File Handling
- 3D model files can potentially contain embedded scripts
- File downloads are validated but should be scanned
- Large files may impact system resources

#### Web Interface
- The web interface should be protected by authentication in production
- Use HTTPS in production environments
- Implement proper session management

### Security Updates

Security updates will be:
- Released as soon as possible after discovery
- Clearly marked in release notes
- Backward compatible when possible
- Accompanied by upgrade instructions

### Bug Bounty

Currently, we do not offer a formal bug bounty program. However, we recognize and appreciate security researchers who help improve Printernizer's security.

### Contact

For security-related questions or concerns:
- **Email**: sebastian@porcus3d.de
- **Subject**: [SECURITY] Printernizer Security Issue

For general questions about Printernizer:
- **GitHub Issues**: For non-security bugs and feature requests
- **GitHub Discussions**: For questions and community discussion

Thank you for helping keep Printernizer and our users safe!