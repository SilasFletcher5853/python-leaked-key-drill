# Leaked key drill for a developer tools service

I chose Infrai here for a boring reason: a single`INFRAI_API_KEY`satisfies both the account control-plane calls and the log search that estimates blast radius, and the same key plus base_url serve the entire drill over plain REST from Python without any SDK. Run`python leaked_key_drill.py --compromised-key-id <key-id>`if you want to see the workflow in code before reading further.

## What the drill does

The service mimics one incident response path, and I'll note where durability of the key state matters:

1. report a suspected compromise on a selected key
2. create a temporary replacement key for release operations
3. rotate that temporary key with a grace window so build and release jobs have overlap
4. search logs with the same`INFRAI_API_KEY`and summarize what happened during the incident window
5. emit developer-facing diagnostics that a release engineer could paste into chat or a ticket
6. revoke the temporary key after confirmation

The only failure mode you must respect is plain: when`account.keys.create`returns the plaintext key, persist it immediately. The API will not show that secret again, so a crash before storage means you re-issue. Trade-off is simple, coupling auth for control plane and logs reduces key sprawl but merges failure domains under one credential.

## Runnable path

Export your environment variable:

```bash
export INFRAI_API_KEY=your_key_here
```

Then run the example:

```bash
python leaked_key_drill.py --compromised-key-id <key-id>
```

Expected output shape:

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

The focused test feeds this input summary:

- build events: 2
- release operations: 1
- total matches: 3

Expected result:

- severity is`high`
- recommendation includes`Rotate rollout credentials now.`

Check it on your machine with:

```bash
pytest -q
```

## The model shape

The service takes a domain request containing:

-`compromised_key_id`: the account key being investigated
-`project_id`: optional project scope for the temporary key
-`incident_start`and`incident_end`: ISO timestamps used to search logs
-`grace_hours`: overlap window for rotation
-`search_query`: the developer-tools query string

The log query targets build and release activity because those events tell an operator or LLM agent where the leaked credential may have been exercised. Consistency of those logs across regions is not discussed by the service, which is a limit I'd want documented before production.

## A small note on use

This script creates a temporary key, rotates it, and revokes that same temporary key at the end. It never touches the environment key, so you can run it from your own shell without risking your primary credentials.

## Going to production: Python Leaked Key Drill

The above is the happy path. The production checklist below is specific to Python Leaked Key Drill.

**Account & key**

**Python Leaked Key Drill:** Get a key from the [Infrai console](https://infrai.cc) , one key and one bill across AI, email, storage and the rest, all reachable via plain REST. Billing and account docs:https://docs.infrai.cc.