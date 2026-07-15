// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview
//
// These static clients are dev/test defaults. In production the BYOK
// BamlClientFactory overrides the primary client via ClientRegistry,
// so any model the user selects is injected at runtime.

client<llm> OpenAI {
  provider openai
  options {
    model "gpt-5.4-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Gemini {
  provider google-ai
  options {
    model "gemini-3.5-flash"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      maxOutputTokens 16000
    }
  }
}

client<llm> Anthropic {
  provider anthropic
  options {
    model "claude-sonnet-5"
    api_key env.ANTHROPIC_API_KEY
    max_tokens 16000
  }
}

client<llm> OpenAIResponses {
  provider openai-responses
  options {
    model "gpt-5.4-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> AzureOpenAI {
  provider azure-openai
  options {
    base_url env.AZURE_OPENAI_BASE_URL
    api_version env.AZURE_OPENAI_API_VERSION
    api_key env.AZURE_OPENAI_API_KEY
  }
}

client<llm> OpenAIGeneric {
  provider openai-generic
  options {
    base_url env.OPENAI_GENERIC_BASE_URL
    api_key env.OPENAI_GENERIC_API_KEY
    model "llama-3.3-70b-versatile"
  }
}

client<llm> MicrosoftFoundry {
  provider openai-generic
  options {
    base_url env.AZURE_AI_FOUNDRY_BASE_URL
    api_key env.AZURE_AI_FOUNDRY_API_KEY
    model "gpt-4o"
  }
}

client<llm> Ollama {
  provider openai-generic
  options {
    base_url env.OLLAMA_BASE_URL
    api_key env.OLLAMA_API_KEY
    model "llama3.3"
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