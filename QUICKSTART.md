# Quick Start Guide - Fix API Key Issue

## 🚨 If you're getting "401 Unauthorized" or "API key not configured" errors:

### Method 1: Use the Setup Script (Easiest)
```bash
python setup-api-key.py
```
Follow the prompts to enter your API key.

### Method 2: Set Environment Variable (Recommended)
```bash
# Replace with your actual API key from OpenAI
export OPENAI_API_KEY="sk-proj-your-actual-api-key-here"

# Make it permanent (add to ~/.bashrc)
echo 'export OPENAI_API_KEY="sk-proj-your-actual-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Method 3: Edit Config File Directly
Edit `config/config.json`:
```json
{
  "llm": {
    "provider": "openai",
    "api_key": "sk-proj-your-actual-api-key-here",
    "model": "gpt-4o",
    "max_tokens": 4096,
    "temperature": 0.7
  }
}
```

## 🔑 Getting API Keys

### OpenAI (Recommended)
1. Go to: https://platform.openai.com/account/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-proj-` or `sk-`)
4. Make sure you have credits in your account

### Anthropic (Alternative)
1. Go to: https://console.anthropic.com/
2. Create API key in Account Settings
3. Copy the key (starts with `sk-`)

## 🚀 Quick Test

After setting up your API key:

```bash
# Test the setup
python test-gui.py

# Start the application
python screenshot-llm-gui.py &
python screenshot-llm.py
```

## ✅ Valid Models

**OpenAI (with vision support):**
- `gpt-4o` (recommended)
- `gpt-4o-mini` (cheaper)
- `gpt-4-turbo`

**Anthropic:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-haiku-20240307` (faster/cheaper)

## 🐛 Still Having Issues?

1. **Check API key format**: Should start with `sk-`
2. **Check credits**: Make sure your OpenAI/Anthropic account has sufficient credits
3. **Test API key**: Use curl to test:
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```
4. **Check logs**: Look in `logs/` directory for detailed error messages
5. **Restart**: After changing config, restart both GUI and daemon

## 📱 Quick Commands

```bash
# Setup API key
python setup-api-key.py

# Test everything
python test-gui.py

# Start GUI (in one terminal)
python screenshot-llm-gui.py

# Start daemon (in another terminal)
python screenshot-llm.py

# Or start both in background
./run.sh
```

## 🖱️ Mouse Device Issues

If the system is detecting the wrong mouse device (like "Rival 3 Wireless Keyboard" instead of "Rival 3" mouse):

```bash
# Test which devices are detected
python test-mouse-devices.py

# Look for the correct mouse device in the output
# The system should now prefer actual mice over keyboards
```

The improved detection logic will:
1. **Prefer** actual "Rival 3" mouse devices (not wireless keyboard variants)
2. **Avoid** devices with "keyboard" in the name
3. **Prioritize** devices with standard mouse buttons (left, right, middle)
4. **Warn** if using a fallback device

If you still have issues, check the device list and ensure your Rival 3 mouse is connected and recognized by the system.

That's it! Press your mouse button 9 (side button) to take a screenshot and get AI analysis.