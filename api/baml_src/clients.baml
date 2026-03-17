// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview
//
// These static clients are dev/test defaults. In production the BYOK
// BamlClientFactory overrides the primary client via ClientRegistry,
// so any model the user selects is injected at runtime.

client<llm> OpenAI {
  provider openai
  options {
    model "gpt-4.1-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Gemini {
  provider google-ai
  options {
    model "gemini-2.5-flash"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      maxOutputTokens 16000
    }
  }
}

client<llm> Anthropic {
  provider anthropic
  options {
    model "claude-sonnet-4-6"
    api_key env.ANTHROPIC_API_KEY
    max_tokens 16000
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}