# LLM Provider Connections

How Themis talks to language models, and the different kinds of backend you can point it at.

## The one idea that ties it all together

Themis speaks **one protocol**: the OpenAI HTTP contract. A server is *OpenAI-compatible* when it
implements the same wire format as OpenAI's API — the same endpoint path (`/v1/chat/completions`),
the same request shape (a `messages` array of `{role, content}` objects), and the same response
shape (`choices[0].message...`). Because the contract is identical, the official OpenAI SDK can talk
to that server unchanged; you only swap the `base_url`.

This is why a single `OpenAICompatibleClient` can reach vLLM, Groq, Gemini, and Anthropic alike.
It cares only about the contract, not about who runs the model behind it.

> One exception lives inside Themis itself: the dedicated `openai` provider uses OpenAI's newer,
> proprietary **Responses API** (`/v1/responses`), which only OpenAI implements. Every other provider
> routes through the **Chat Completions API**, which every compatible server exposes. That single API
> difference is the reason there are two client classes.

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
  provider: openai_compatible
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
  provider: openai_compatible
  model: qwen/qwen3-32b
  base_url: https://api.groq.com/openai/v1   # set LLM_API_TOKEN to your key
```

- **Auth:** always required (their API key).
- **Reachability:** public endpoint, reachable from any runner.

### 3. Closed cloud models (OpenAI, Gemini, Anthropic)

These models' weights are private — you **cannot** deploy them. The vendor runs them and offers an
API. OpenAI uses its own Responses API; Gemini and Anthropic additionally expose an OpenAI-compatible
endpoint as a convenience door.

```yaml
llm:
  provider: openai            # OpenAI's native Responses API

llm:
  provider: gemini            # or: anthropic
  model: gemini-2.5-flash-lite   # base_url defaults to the vendor's endpoint
```

For `gemini` and `anthropic`, Themis ships the vendor's OpenAI-compatible `base_url` as a default, so
you don't have to type it. You can still override `base_url` (e.g. to route through a proxy).

- **Auth:** always required (your vendor key).
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

| Backend | `provider` | `base_url` | `LLM_API_TOKEN` | API used |
|---|---|---|---|---|
| OpenAI | `openai` | — | required | Responses |
| Self-hosted (vLLM, …) | `openai_compatible` | **required** | optional | Chat Completions |
| Hosted OSS (Groq, …) | `openai_compatible` | **required** | required | Chat Completions |
| Gemini | `gemini` | default (overridable) | required | Chat Completions |
| Anthropic | `anthropic` | default (overridable) | required | Chat Completions |