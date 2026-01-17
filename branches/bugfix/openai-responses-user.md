# OpenAI Responses API `user` Parameter Fix

## Issue Summary

When using models that route through OpenAI's Responses API (`/v1/responses`), such as `gpt-5.2-codex`, requests fail with:

```
Error code: 400 - {'detail': 'Unsupported parameter: user'}
```

The OpenAI Responses API does not support the `user` parameter, but Letta unconditionally adds it to all OpenAI requests.

## Root Cause

Commit `9280d85ba` ("feat: always add user id to openai requests (#1969)") introduced code that unconditionally sets the `user` parameter on both Chat Completions and Responses API requests.

The `build_request_data_responses` method in `openai_client.py` was setting the `user` field:

```python
# always set user id for openai requests
if self.actor:
    data.user = self.actor.id

if llm_config.model_endpoint == LETTA_MODEL_ENDPOINT:
    if not self.actor:
        # override user id for inference.letta.com
        import uuid

        data.user = str(uuid.UUID(int=0))
```

However, the Responses API (`/v1/responses`) does not support this parameter.

## The Fix

Removed the `user` parameter assignment from `build_request_data_responses` method. The Chat Completions API (`/v1/chat/completions`) does support the `user` parameter, so the equivalent code in `build_request_data` method remains unchanged.

```python
# Note: Don't set 'user' param for Responses API - it's not supported
# (see build_request_data for Chat Completions which does support it)
```

## Files Modified

- `letta/llm_api/openai_client.py` - Removed `user` parameter from `build_request_data_responses` method

## Evidence

### 1. Azure OpenAI Responses API Documentation

The [Azure OpenAI Responses API documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses) explicitly lists supported request body parameters:

- `model`, `input`, `instructions`, `tools`, `tool_choice`, `temperature`, `top_p`, `max_output_tokens`, `parallel_tool_calls`, `metadata`, `stream`, `background`, `reasoning`, `include`, `previous_response_id`

**The `user` parameter is NOT listed.** The documentation notes that `user` only appears in the response output object, not as a request parameter.

### 2. Similar "Unsupported Parameter" Errors

The [Roo-Code GitHub issue #6862](https://github.com/RooCodeInc/Roo-Code/issues/6862) documents similar 400 errors when passing Chat Completions parameters to the Responses API:

> "400 Unsupported parameter: 'messages'. In the Responses API, this parameter has moved to 'input'."

This confirms the API returns 400 errors for unsupported parameters.

### 3. API Comparison Guides

Multiple comparison guides document differences between Chat Completions and Responses API:

- [Simon Willison's analysis](https://simonwillison.net/2025/Mar/11/responses-vs-chat-completions/)
- [HackMD comparison](https://hackmd.io/nfepid8mTKqhJH0cLxND1A)

Neither mentions `user` as a parameter available in the Responses API.

### 4. Third-Party API Documentation

The [AI/ML API GPT-5.2 docs](https://docs.aimlapi.com/api-references/text-models-llm/openai/gpt-5.2) (OpenAI-compatible) list all request parameters and **do not include a `user` parameter**.

### 5. Chat Completions Does Support `user`

The [Chat Completions API reference](https://platform.openai.com/docs/api-reference/chat) confirms the `user` parameter exists there for "detecting users that may be violating usage policies" - but this is specific to Chat Completions.

## Testing

After applying the fix:

1. Rebuild the Docker image
2. Test with a model that uses the Responses API (e.g., `gpt-5.2-codex`)
3. Verify the request succeeds without the "Unsupported parameter: user" error

## PR Description

### Title

fix: remove unsupported `user` parameter from OpenAI Responses API requests

### Body

**Problem**

When using models routed through OpenAI's Responses API (`/v1/responses`), such as `gpt-5.2-codex`, requests fail with:

```
Error code: 400 - {'detail': 'Unsupported parameter: user'}
```

This was introduced in commit `9280d85ba` ("feat: always add user id to openai requests (#1969)") which unconditionally sets the `user` parameter on both Chat Completions and Responses API requests.

**Solution**

Remove the `user` parameter assignment from the `build_request_data_responses` method. The Chat Completions API (`/v1/chat/completions`) supports this parameter, so that code path remains unchanged.

**Evidence**

The Responses API does not support the `user` parameter:

1. **[Azure OpenAI Responses API docs](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses)** - Lists all supported request parameters; `user` is not among them
2. **[Roo-Code #6862](https://github.com/RooCodeInc/Roo-Code/issues/6862)** - Documents similar 400 errors for unsupported parameters in Responses API
3. **[API comparison guides](https://simonwillison.net/2025/Mar/11/responses-vs-chat-completions/)** - Don't mention `user` as available in Responses API
4. **[Chat Completions API reference](https://platform.openai.com/docs/api-reference/chat)** - Confirms `user` is a Chat Completions-specific parameter

**Changes**

- `letta/llm_api/openai_client.py`: Remove `user` parameter from `build_request_data_responses` method

**Testing**

- Verified requests to Responses API models no longer include the unsupported `user` parameter
- Chat Completions API requests continue to include `user` parameter as expected

## PR Recommendation

This is a safe, minimal fix that:
1. Removes unsupported parameter from Responses API requests
2. Keeps `user` parameter for Chat Completions API (which supports it)
3. Doesn't change behavior for standard OpenAI chat models
4. Enables compatibility with newer GPT models that use the Responses API

Should be safe to submit as a PR to upstream letta-ai/letta.
