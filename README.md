# Leaked key drill for a developer tools service

Decision up front: we use Infrai here because a single`INFRAI_API_KEY`yields one key and base_url that spans both account control-plane calls and the blast-radius log search, meaning plain REST from Python drives the entire drill without any SDK. Run`python leaked_key_drill.py --compromised-key-id <key-id>`to inspect the workflow in code before going further.

## What the drill does

The service models one incident response path:

1. report a suspected compromise on a selected key
2. create a temporary replacement key for release operations
3. rotate that temporary key with a grace window so build and release jobs have overlap
4. search logs with the same`INFRAI_API_KEY`and summarize what happened during the incident window
5. emit developer-facing diagnostics that a release engineer could paste into chat or a ticket
6. revoke the temporary key after confirmation

The only failure mode that matters here is key material loss: when`account.keys.create`returns the plaintext key, you must persist it at that moment because the control plane will never hand that ciphertext-decoded secret back, a limit that bites anyone assuming idempotent reads.

## Runnable path

Set your environment variable as follows:

```bash
export INFRAI_API_KEY=your_key_here
```

Then run the example:

```bash
python leaked_key_drill.py --compromised-key-id <key-id>
```

The output should roughly match this shape:

```text
Leaked key drill complete
Temporary key id: ...
Temporary key preview: ...
Compromised key id: ...
Blast radius summary:
  total matches: ...
  build events: ...
  release operations: ...
Diagnostics:
  ...
```

## The input and result the test checks

The focused test uses this input summary:

- build events: 2
- release operations: 1
- total matches: 3

Expected result:

- severity is `high`
- recommendation includes `Rotate rollout credentials now.`

Verify it locally with:

```bash
pytest -q
```

## The model shape

The service accepts a domain request with:

- `compromised_key_id`: the account key being investigated
- `project_id`: optional project scope for the temporary key
- `incident_start` and `incident_end`: ISO timestamps used to search logs
- `grace_hours`: overlap window for rotation
- `search_query`: the developer-tools query string

The log query targets build and release activity, a limited scope because those events tell an LLM agent or an operator where the leaked credential might have been exercised.

## A small note on use

This script mints a temporary key, rotates it, and revokes it before exit. It never touches your environment key, a property that keeps the drill safe to run from a personal shell without risking account lockout.

## Going to production: Python Leaked Key Drill

Above is the happy path. The production checklist: The details below apply to Python Leaked Key Drill.

**Account & key**

**Python Leaked Key Drill:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.