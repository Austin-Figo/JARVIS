# Security Policy

## Credential handling
- Never commit API keys, access tokens, passwords, private keys, or populated local configuration.
- The provider reads credentials from process environment variables: `GEMINI_API_KEY` and `OPENAI_API_KEY`. Provider/model selection can use `AI_PROVIDER` and `AI_MODEL`; Ollama uses `OLLAMA_URL`.
- `.env.example` documents variable names only. The current application does not automatically load a `.env` file; set variables in the process environment before launching JARVIS.
- Keep `config/settings.json` free of credentials.

## Historical credential exposure
A provider credential was found in a previous committed version of `config/settings.json`. The current audit branch removes it from the latest tracked file, but does not erase the credential from Git history. Revoke/rotate the affected provider key immediately. Before publishing, rewrite history to remove the exposed value from every reachable ref and verify the cleaned repository. A file edit alone is not sufficient.

## Application security status
JARVIS can perform local Windows actions and should be treated as a personal desktop application. Do not expose its local API to an untrusted network. Review permissions, confirmation flows, logging, and dependency vulnerabilities before production use.

## Reporting
Do not post secrets or sensitive personal data in public issues. Rotate exposed credentials first.
