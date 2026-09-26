# LLM Provider Connections

How Themis talks to language models, and the different kinds of backend you can point it at.

## The one idea that ties it all together

Themis speaks **one protocol**: the OpenAI HTTP contract. A server is *OpenAI-compatible* when it
implements the same wire format as OpenAI's API — the same endpoint path (`/v1/chat/completions`),
the same request shape (a `messages` array of `{role, content}` objects), and the same response
shape (`choices[0].message...`). Because the contract is identical, the official OpenAI SDK can talk
to that server unchanged; you only swap the `base_url`.

This is why a single `OpenAICompatibleClient` can reach OpenAI, vLLM, Groq, Gemini, and Anthropic
alike. It cares only about the contract, not about who runs the model behind it.

> **One client, one protocol.** Themis has exactly one LLM client and routes every provider —
> OpenAI included — through the **Chat Completions API** (`/v1/chat/completions`), which every
> compatible server exposes. There are no vendor shortcuts and no built-in default URLs: you always
> set `base_url` explicitly, and you tell Themis who runs the server with `deployment_type`.

## How the review's structure is enforced

Themis does **not** use the provider's native structured output (`response_format` with a JSON
schema), because providers honour it inconsistently — Anthropic's OpenAI-compatible endpoint, for
example, does not enforce the schema. Instead, the same mechanism is used for every backend:

1. **Prompt** — the system prompt embeds the JSON Schema generated from `CodeReviewResponseDTO`
   and asks for a bare JSON object; the user prompt ends with a reminder.
2. **Parsing** — `output_parser.py` extracts the object from the plain-text answer, tolerating
   code fences, surrounding prose and `<think>` blocks, then validates it with pydantic.
3. **Repair** — if parsing fails, the model is shown its answer plus the concrete error and asked
   once to correct it. A response truncated by the output token limit fails immediately with an
   actionable message instead.

## You configure exactly two things

A backend is fully described by two keys:

| Key | What it answers | Values |
|---|---|---|
| `base_url` | *Where* the OpenAI-compatible endpoint lives | any routable URL — **always required** |
| `deployment_type` | *Who* runs it (decides whether a token is required) | `cloud` or `self_hosted` |

- `deployment_type: cloud` — a vendor/hosted endpoint. An API key (`LLM_API_TOKEN`) is **always
  required**; Themis fails fast if it is missing.
- `deployment_type: self_hosted` — you run the server. A key is **optional** (see the keyless caveat).

## Two layers, kept separate

Every connection involves two independent gates. Conflating them is the usual source of confusion.

| Layer | What it is | In Themis |
|---|---|---|
| **Application auth** | The API key sent inside the HTTP request | `LLM_API_TOKEN` |
| **Network reachability** | Whether the runner can open a TCP connection to the host at all | `base_url` must be routable from the CI runner |

A keyless backend skips the **first** layer. It never skips the **second** — and for self-hosted
servers, the network layer is usually where the real access control lives.

## The three kinds of backend

### 1. Self-hosted open-weights model

You download an open model (Qwen, Llama, Mistral, DeepSeek) and run it yourself behind a server like
[vLLM](https://docs.vllm.ai/) or LM Studio, which exposes an OpenAI-compatible endpoint. You deploy
and own the whole thing.

```yaml
llm:
  deployment_type: self_hosted
  model: <model-name>
  base_url: http://your-host:8000/v1
```

- **Auth:** optional. A local server with no auth ignores the key entirely. Set `LLM_API_TOKEN`
  only if your server requires it.
- **Reachability:** the CI runner must be able to route to `base_url`. See the keyless caveat below.

### 2. Hosted provider serving open models

Providers like Groq, Together, Fireworks, and OpenRouter run open-weights models on their hardware
and give you an OpenAI-compatible endpoint. You deploy nothing — just point at their URL.

```yaml
llm:
  deployment_type: cloud
  model: qwen/qwen3-32b
  base_url: https://api.groq.com/openai/v1   # set LLM_API_TOKEN to your key
```

- **Auth:** always required (their API key).
- **Reachability:** public endpoint, reachable from any runner.

### 3. Closed cloud models (OpenAI, Gemini, Anthropic)

These models' weights are private — you **cannot** deploy them. The vendor runs them and offers an
OpenAI-compatible endpoint. Point `base_url` at that endpoint and mark it `cloud`:

```yaml
llm:
  deployment_type: cloud
  model: gpt-5-nano
  base_url: https://api.openai.com/v1
  # Gemini:    https://generativelanguage.googleapis.com/v1beta/openai/
  # Anthropic: https://api.anthropic.com/v1/
```

- **Auth:** always required (your vendor key). A `cloud` backend fails fast if `LLM_API_TOKEN` is
  unset — keyless is only allowed for a `self_hosted` deployment.
- **Reachability:** public endpoint, reachable from any runner.

## The keyless caveat (read this before going keyless)

"No auth" means the protection is the **network**, not a token. A keyless server is only safe if the
runner reaches it over a private/trusted network:

- **Self-hosted CI runner inside the company network** → the runner and the LLM server share a private
  subnet. Nothing outside can route to the server, so the firewall *is* the auth. This is the normal
  setup for keyless.
- **Shared/cloud runners** → cannot reach a private address at all. Making the server publicly routable
  *and* keyless means anyone who finds the IP can use your GPU. Don't.
- **Middle ground** → the runner joins your network over VPN / private peering, getting a route to the
  internal host without exposing it publicly.

> ⚠️ A keyless endpoint must never be publicly routable. Note also that vLLM binds to `0.0.0.0` by
> default (every interface), so "keyless but firewalled" is only safe if the firewall actually exists.

## Quick reference

Every row uses the same client and the same Chat Completions API; `base_url` is always required and
`deployment_type` differs only in whether a token is mandatory.

| Backend | `deployment_type` | `base_url` | `LLM_API_TOKEN` |
|---|---|---|---|
| OpenAI | `cloud` | **required** | required |
| Self-hosted (vLLM, …) | `self_hosted` | **required** | optional |
| Hosted OSS (Groq, …) | `cloud` | **required** | required |
| Gemini | `cloud` | **required** | required |
| Anthropic | `cloud` | **required** | required |