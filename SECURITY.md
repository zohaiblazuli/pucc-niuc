# Security Guidelines for PCC-NIUC

## API Key Protection

This project uses API keys for various LLM providers. **NEVER commit API keys to version control.**

### Setup Instructions

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   # Edit .env file with your actual keys
   OPENAI_API_KEY=sk-your_actual_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENROUTER_API_KEY=your_openrouter_key
   ```

3. **Verify `.env` is in `.gitignore`:**
   The `.env` file is automatically excluded from version control.

### Windows PowerShell Setup (Alternative)

You can also set environment variables directly:

```powershell
# Temporary (current session)
$env:OPENAI_API_KEY="your_key_here"

# Permanent (all sessions)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_key_here", "User")
```

### Supported APIs

- **OpenAI**: GPT-3.5, GPT-4 models
- **Anthropic**: Claude 3 models  
- **OpenRouter**: Various open-source models
- **Google**: Gemini models

### Security Best Practices

1. ✅ **Use environment variables** - Never hardcode API keys
2. ✅ **Use `.env` files** - Keep keys out of source code
3. ✅ **Rotate keys regularly** - Generate new keys periodically
4. ✅ **Limit key permissions** - Use least-privilege access
5. ✅ **Monitor usage** - Watch for unexpected API calls

### What's Protected

- All `.env*` files (except `.env.example`)
- Virtual environment directories (`venv/`, `env/`)
- Python cache files (`__pycache__/`)
- Model files and temporary data
- IDE settings and personal configs

### Reporting Security Issues

If you discover a security vulnerability, please email the maintainers rather than creating a public issue.

## Model Testing Without API Keys

You can test the system without any API keys using the mock model:

```bash
python demo/demo_cli.py --model mock
```

This is perfect for development and testing the NIUC security features.
