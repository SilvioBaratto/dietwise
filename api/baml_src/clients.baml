// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

// Using the new OpenAI Responses API for enhanced formatting
client<llm> OpenAI {
  provider openai
  options {
    model "gpt-5.2"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Gemini {
  provider google-ai
  options {
    model "gemini-3-pro-preview"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      maxOutputTokens 16000
    }
  }
}

// Claude Opus 4.5 - Most capable model (released Nov 2025)
client<llm> Anthropic {
  provider anthropic
  options {
    model "claude-opus-4-5-20251101"
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