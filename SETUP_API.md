# API Setup Guide

## ⚠️ IMPORTANT: Add Your Gemini API Key

Before running the multi-agent system, you need to add your Gemini API key.

### Step 1: Get Your API Key

You mentioned you have Gemini API tokens from the hackathon. If you need to get/verify your key:

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the API key

### Step 2: Add to .env File

Edit the `.env` file in the project root:

```bash
# Open the .env file
nano .env

# Or use any text editor
code .env
```

Replace this line:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

With your actual key:
```
GEMINI_API_KEY=AIza...your_actual_key_here
```

### Step 3: Verify Setup

Test that the API is working:

```bash
source venv/bin/activate
python src/agents/gemini_wrapper.py
```

You should see:
```
✓ Gemini LLM initialized: gemini-1.5-flash
API Key found: AIza...
✓ Gemini wrapper tests passed!
```

---

## Model Options

You can choose between two Gemini models in `.env`:

**gemini-1.5-flash** (Default - Recommended):
- Faster responses (~1-2 seconds)
- Lower cost (free tier: 15 RPM, 1M TPM)
- Good for hackathon/development
- Sufficient for agent reasoning

**gemini-1.5-pro**:
- More capable reasoning
- Slower (~3-5 seconds)
- Higher cost (free tier: 2 RPM, 32K TPM)
- Use if you need maximum quality

For the hackathon, **gemini-1.5-flash is perfect**!

---

## Rate Limits (Free Tier)

**Gemini 1.5 Flash**:
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

**Gemini 1.5 Pro**:
- 2 requests per minute
- 32,000 tokens per minute
- 50 requests per day

**Our System**:
- 7 agents run every 15 minutes
- ~7 LLM calls per decision cycle
- With 900x speedup: ~0.5 seconds real-time per cycle
- Well within limits!

---

## Troubleshooting

### Error: "API key not found"
- Check that `.env` file exists in project root
- Check that `GEMINI_API_KEY` is set correctly
- No quotes needed around the key value

### Error: "Invalid API key"
- Verify key is correct (starts with "AIza")
- Check key is enabled at https://makersuite.google.com
- Ensure Gemini API is enabled for your project

### Error: "Quota exceeded"
- You've hit rate limits
- Wait 1 minute and try again
- Consider switching to gemini-1.5-flash (higher limits)

---

## Once Setup is Complete

Run the full multi-agent system:

```bash
# Start OPC UA server
./run_simulation.sh

# In another terminal: Run agents
source venv/bin/activate
python src/agents/run_multi_agent.py

# In another terminal: Visualize
source venv/bin/activate
python src/simulation/opcua_visualizer.py
```

---

**Ready to add your API key? Edit `.env` file now!** 🚀
