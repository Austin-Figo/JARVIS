# Security Policy

## Credential handling

- Never commit API keys, access tokens, passwords, private keys, or populated local configuration.
- Provider credentials must be supplied through process environment variables: GEMINI_API_KEY or OPENAI_API_KEY.
- Provider/model selection can use AI_PROVIDER and AI_MODEL; Ollama uses OLLAMA_URL.
- The .env.example file documents variable names only. The application does not automatically load a .env file.
- Keep config/settings.json free of credentials and keep local databases and runtime logs out of Git.

## Historical credential exposure

A provider API credential was previously committed in an earlier version of config/settings.json. The repository owner reports that the exposed key has been deleted/revoked in Google AI Studio.

Revocation prevents use of that credential, but does not erase its text from Git history. The current audit branch removes the credential from the latest tracked settings file and changes provider loading to environment variables. The repository history still needs to be rewritten across every branch and tag that contains the old file. Review GitHub's cached pull-request references and contact GitHub Support if the sensitive object remains accessible after the rewrite.

Do not publish this repository until the history cleanup is complete and independently verified. Do not paste replacement credentials into issues, pull requests, or chat.

## Application security status

JARVIS can execute local Windows actions and should be treated as a personal desktop application. Do not expose its local API or desktop services to an untrusted network. Review permissions, confirmation flows, logging, and dependency vulnerabilities before production use.

## Reporting

Do not post secrets or sensitive personal data in public issues. Revoke exposed credentials first, then follow the repository history-cleanup procedure.
