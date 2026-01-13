# Streaming TypeError Fix Analysis

## Issue Summary

When using Letta with OpenAI-compatible streaming endpoints (like cli-proxy-api), agents fail with:

```
TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'
```

## Root Cause

In `letta/interfaces/openai_streaming_interface.py`, at two locations (lines ~296 and ~788), the code assumes that if `chunk.usage` exists, then `chunk.usage.prompt_tokens` and `chunk.usage.completion_tokens` will be integers:

```python
# Original buggy code
if chunk.usage:
    self.input_tokens += chunk.usage.prompt_tokens
    self.output_tokens += chunk.usage.completion_tokens
```

However, OpenAI-compatible APIs may return a `usage` object where these fields are `None`. This is valid according to OpenAI's API spec since:
1. Intermediate streaming chunks may have `usage: {}` or `usage: {"prompt_tokens": null, ...}`
2. Some proxy implementations may populate `usage` with partial data

## Observed Behavior

1. Agent receives streaming request
2. Streaming interface processes chunks
3. A chunk contains `usage` object but with `None` token values
4. TypeError occurs when attempting `self.output_tokens += None`
5. Stream processing fails with "Received 0 events"

## The Fix

Added null checks before incrementing token counters:

```python
# Fixed code
if chunk.usage:
    if chunk.usage.prompt_tokens is not None:
        self.input_tokens += chunk.usage.prompt_tokens
    if chunk.usage.completion_tokens is not None:
        self.output_tokens += chunk.usage.completion_tokens
```

This is consistent with how other optional fields in the same function are handled (e.g., `cached_tokens`, `reasoning_tokens` use `is not None` checks).

## Files Modified

- `letta/interfaces/openai_streaming_interface.py` - Two locations (lines ~296 and ~788)

## Testing

### Before Fix
```
Letta.letta.interfaces.openai_streaming_interface - ERROR - Error processing stream: unsupported operand type(s) for +=: 'int' and 'NoneType'
```

### After Fix
Streaming should complete successfully, with token counts only accumulated when non-None values are present.

## Environment

- Letta version: 0.16.1 (forked from upstream)
- LLM Backend: cli-proxy-api (OpenAI-compatible streaming)
- Model: gemini-3-flash-preview via anthropic provider

## Similar Issues in Other Projects

This same pattern has been reported in:
- [langflow-ai/langflow#8215](https://github.com/langflow-ai/langflow/issues/8215) - Same TypeError with Anthropic models
- [BerriAI/litellm#9578](https://github.com/BerriAI/litellm/issues/9578) - Similar streaming handler issue

## PR Recommendation

This is a safe, minimal fix that:
1. Adds defensive null checks
2. Follows existing code patterns in the same file
3. Doesn't change behavior when values are present
4. Prevents crashes with non-standard OpenAI-compatible backends

Should be safe to submit as a PR to upstream letta-ai/letta.
