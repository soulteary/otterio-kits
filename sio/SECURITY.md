# Security Policy

## Supported Versions

We actively support the following versions of `sio`:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

We recommend always using the latest version to ensure you have the most recent security updates.

## Reporting a Vulnerability

The otterio-kits maintainers takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Report vulnerabilities through the private reporting channel at
[soulteary/otterio-kits Security](https://github.com/soulteary/otterio-kits/security).
If private reporting is unavailable, open an issue requesting a private contact
without including vulnerability details. Do not send reports about this fork to the upstream team.

Include the following information in your report:

- Type of vulnerability (e.g., buffer overflow, authentication bypass, cryptographic weakness)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if available)
- Impact of the vulnerability, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: Maintainers will review reports as availability permits; no response deadline is promised.
- **Communication**: We will keep you informed of the progress toward a fix and public disclosure.
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous).
- **Timeline**: Fix and disclosure timing depends on the finding and maintainer availability.

## Security Best Practices

When using `sio`, follow these security best practices:

### Key Management

1. **Never reuse encryption keys**: Each data stream should use a unique key derived from a master key
2. **Use a KDF**: Derive per-stream keys using HKDF, BLAKE2X, or similar with unique context
3. **Secure key storage**: Store master keys in hardware security modules (HSMs) or key management services
4. **Key rotation**: Implement regular key rotation policies

### Implementation

1. **Verify authenticity**: Always check for sio.Error types which indicate authentication failures
2. **Handle errors**: Never ignore decryption errors or continue processing unauthenticated data
3. **Memory safety**: Be aware that decrypted data must be explicitly cleared from memory if needed
4. **Random sources**: Use crypto/rand.Reader for all random value generation
5. **Version pinning**: Pin specific versions in production and test updates before deployment

### Known Limitations

1. **Key reuse**: Reusing keys across different data streams allows package-level replay attacks
2. **Maximum size**: Single encrypted streams are limited to 256 TB
3. **Sequence numbers**: Limited to 2^32 packages per stream (~256 TB at 64KB packages)

## Cryptographic Design

### Algorithms

- **AES-256-GCM**: Authenticated encryption with 256-bit keys (when hardware acceleration available)
- **ChaCha20-Poly1305**: Authenticated encryption with 256-bit keys (software fallback)

### Security Properties

`sio` provides:

- **Confidentiality**: Data cannot be read without the correct key
- **Integrity**: Modifications to ciphertext are detected during decryption
- **Authenticity**: Data origin is verified through AEAD tags
- **Reorder protection**: Sequence numbers prevent package reordering

### Attack Resistance

`sio` is designed to resist:

- Chosen-plaintext attacks (CPA)
- Chosen-ciphertext attacks (CCA)
- Package reordering attacks
- Truncation attacks (V2.0 with final package flag)

### Not Protected Against

`sio` does NOT protect against:

- Key compromise
- Side-channel attacks (timing, power analysis) on the underlying cipher
- Replay attacks when keys are reused
- Attacks on the key derivation or storage mechanisms

## Audit History

The inherited documentation mentions upstream reviews and maintenance. Those
statements do not establish an independent audit of this fork. No independent
cryptographic audit of the otterio-kits module is claimed here.

## Security Updates

Security updates will be published as:

- GitHub Security Advisories
- Release notes with [SECURITY] tags
- Updates to this SECURITY.md file

Subscribe to repository releases to be notified of security updates.

## References

- [DARE Specification](DARE.md)
- [otterio-kits Security](https://github.com/soulteary/otterio-kits/security)
- [Go Cryptography Policy](https://golang.org/security)

## Hall of Fame

We appreciate security researchers who have responsibly disclosed vulnerabilities:

(No vulnerabilities disclosed yet)

---

Last updated: 2025-01-10
