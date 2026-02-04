# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within SpeechCortex SDK, please send an email to team@speechcortex.com. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

When reporting a vulnerability, please include:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

## Response Timeline

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide a detailed response within 7 days indicating the next steps
- We will notify you when the vulnerability is fixed
- We will publicly disclose the vulnerability after a fix is released

## Security Best Practices

When using SpeechCortex SDK:

1. **Never commit API keys**: Store API keys in environment variables or secure vaults
2. **Use HTTPS**: Always use secure connections when communicating with SpeechCortex API
3. **Keep dependencies updated**: Regularly update SpeechCortex SDK and its dependencies
4. **Validate input**: Always validate and sanitize user input before processing
5. **Error handling**: Implement proper error handling to avoid exposing sensitive information

## Attribution

We appreciate responsible disclosure and will acknowledge security researchers who report vulnerabilities to us.
