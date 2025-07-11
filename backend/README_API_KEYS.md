# API Keys Setup Guide

## Required API Keys

To use DocuForge AI, you'll need to obtain API keys from the following providers:

### 1. OpenAI API Key
- **Website**: https://platform.openai.com/
- **Steps**:
  1. Sign up or log in to OpenAI
  2. Go to API Keys section
  3. Create a new API key
  4. Copy the key and add to `.env` file as `OPENAI_API_KEY`
- **Models**: GPT-4, GPT-3.5-turbo, GPT-4-turbo

### 2. Anthropic API Key (Claude)
- **Website**: https://console.anthropic.com/
- **Steps**:
  1. Sign up or log in to Anthropic Console
  2. Go to API Keys section
  3. Create a new API key
  4. Copy the key and add to `.env` file as `ANTHROPIC_API_KEY`
- **Models**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku

### 3. Google AI API Key
- **Website**: https://makersuite.google.com/app/apikey
- **Steps**:
  1. Sign up or log in to Google AI Studio
  2. Create a new API key
  3. Copy the key and add to `.env` file as `GOOGLE_AI_API_KEY`
  4. Also set your Google Cloud Project ID as `GOOGLE_CLOUD_PROJECT_ID`
- **Models**: Gemini-pro, Gemini-pro-vision

### 4. Ollama (Optional - Local LLM)
- **Website**: https://ollama.ai/
- **Steps**:
  1. Install Ollama locally
  2. Run `ollama serve` to start the server
  3. Pull models: `ollama pull llama2`, `ollama pull codellama`
  4. Set `OLLAMA_BASE_URL=http://localhost:11434` in `.env`
- **Models**: Llama2, CodeLlama, Mistral, Neural-chat

## Setup Instructions

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file**:
   ```bash
   nano .env
   ```

3. **Add your API keys**:
   ```env
   OPENAI_API_KEY=sk-your-actual-openai-key
   ANTHROPIC_API_KEY=your-actual-anthropic-key
   GOOGLE_AI_API_KEY=your-actual-google-key
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   ```

4. **Test the setup**:
   ```bash
   source venv/bin/activate
   python -c "from app.core.config import settings; print('API Keys loaded:', bool(settings.openai_api_key))"
   ```

## Provider Priority

The system will automatically detect which providers are available based on API keys:

1. **OpenAI** - Primary provider (most reliable)
2. **Claude** - High quality, good for writing
3. **Google AI** - Fast and efficient
4. **Ollama** - Local/private, no API costs

## Cost Considerations

- **OpenAI**: Pay per token (GPT-4: ~$0.03/1K tokens)
- **Anthropic**: Pay per token (Claude-3: ~$0.015/1K tokens)
- **Google AI**: Free tier available, then pay per token
- **Ollama**: Free (runs locally)

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage and costs
- Consider using API key restrictions/limits

## Testing API Keys

Once you've added your API keys, you can test them:

```bash
# Test OpenAI
curl -X POST "http://localhost:8000/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "openai"}'

# Test Claude
curl -X POST "http://localhost:8000/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "claude"}'

# Test Google AI
curl -X POST "http://localhost:8000/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "google"}'
```

## Troubleshooting

### Common Issues:

1. **API Key Not Found**: Check `.env` file exists and has correct key names
2. **Permission Denied**: Ensure API keys have correct permissions
3. **Rate Limits**: Some providers have rate limits for new accounts
4. **Invalid Project ID**: Google AI requires a valid Cloud Project ID

### Debug Commands:

```bash
# Check if environment variables are loaded
python -c "from app.core.config import settings; print(vars(settings))"

# Test AI service directly
python -c "from app.services.ai_service import AIService; service = AIService(); print(service.get_available_providers())"
```