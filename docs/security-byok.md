# Security and BYOK

## Current implementation

The foundation implements the local mock only. No provider key entry, storage,
external provider calls, or credential configuration is implemented.
Context and summary routes require explicit IDs; summary requires a confirmation
flag. Responses identify the mock model and return suggestions without writes.
The API has no authentication and is intended for loopback local use.
The remaining BYOK and hosted controls below describe future requirements.

DeeDee is an educational project. Treat CRM records and provider keys as sensitive, even when using fictional demo data.

## Default: local mock mode

The app should run with a deterministic mock provider and no network access, API key, or paid service. This is the safe default for learning, tests, and demos.

## Optional BYOK mode

The user may configure a provider API key to enable model-backed actions. The key belongs to the user and is sent only to the chosen provider when the user initiates an AI action.

For the first local version:

- Accept the key at runtime and keep it in process memory only; do not write it to SQLite.
- Never put a key in source code, a committed `.env`, browser local storage, URLs, logs, error messages, screenshots, or exports.
- Use a local `.env` only for developer testing; commit `.env.example` with placeholder values and ignore real `.env` files.
- Redact authorization headers and provider request metadata in error reporting.
- Provide a clear way to clear or replace the key.

For a hosted multi-user version, do not treat process memory or an application database as a complete secret-management design. Require authenticated sessions, tenant isolation, encryption backed by a managed key service, rotation, access auditing, and a documented retention policy before offering saved keys.

## CRM context sent to a provider

A provider may receive selected CRM context when a user confirms an AI action. Make the provider and intended action visible. Before sending:

1. Show which records and fields will be included.
2. Exclude unrelated records and unnecessary personal data.
3. Make user consent specific to the action.
4. Respect configured model/provider policy and context-size limits.

Never upload the full CRM database for a single-record request.

## Model output boundaries

- Treat record notes and model responses as untrusted text.
- Do not let instructions inside a CRM note change provider configuration, permissions, or system rules.
- Validate JSON/schema outputs, lengths, and referenced record IDs.
- Display sources for extracted facts when possible.
- Require a human to approve every proposed CRM write.
- Never send a message, change deal status, or alter a record automatically in the MVP.

## Audit and cost controls

Audit metadata such as action, provider/model label, timestamp, result status, and usage counters when returned. Avoid retaining raw prompt contents or record text by default. Make usage limits and provider errors visible; do not retry indefinitely.

## Before opening a pull request

- Confirm no key, private customer record, access token, or real contact data is staged.
- Check logs and test fixtures for secrets.
- Keep the no-network mock path covered by tests.
- Document any new outbound data flow.
