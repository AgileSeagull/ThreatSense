# Shared Schemas

## Event schema

`event_schema.json` defines the unified activity event format used by:

- **Endpoint Agent**: when building and sending events
- **Detection Engine**: when validating and storing incoming events

### Normalization for command hashes (PSI)

Agent and engine must use the same normalization before hashing:

1. Strip leading/trailing whitespace
2. Collapse internal whitespace to a single space
3. Lowercase the string (or agree on a single case)

Then compute SHA-256 of the UTF-8 encoded string. Example (Python):

```python
import hashlib
def normalize_command(cmd: str) -> str:
    return " ".join(cmd.strip().lower().split())
def command_hash(cmd: str) -> str:
    return hashlib.sha256(normalize_command(cmd).encode()).hexdigest()
```
