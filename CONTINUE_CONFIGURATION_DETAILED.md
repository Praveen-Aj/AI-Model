# 🔧 CONTINUE EXTENSION - DETAILED CONFIGURATION GUIDE

## What is Continue?

Continue is a VS Code extension that connects to AI models. We need to tell it:
- ✅ **Where is the AI model?** → `http://localhost:11434` (Ollama)
- ✅ **What model to use?** → `qwen2.5-coder:14b`
- ✅ **What features to enable?** → Autocomplete, Chat, Edits

---

## Step 1: Open Continue Configuration Panel

**In VS Code, do this:**

```
1. Look for the Continue icon on the LEFT sidebar
   (It looks like a curved arrow or "C" symbol)
   
2. Click on it
   
3. You should see a "Settings" option at the bottom
   (or look for a gear/settings icon)
   
4. Click on "Settings"
```

**Visual Guide:**
```
VS Code Left Sidebar
├── Explorer (file icon)
├── Search (magnifying glass)
├── Source Control (git icon)
├── Run and Debug
├── Extensions
└── Continue ← CLICK HERE
    └── Settings (gear icon) ← THEN CLICK HERE
```

---

## Step 2: Locate the Configuration Section

Once you open Continue Settings, you should see sections like:

```
┌─────────────────────────────────────────┐
│ Continue Settings Panel                 │
├─────────────────────────────────────────┤
│                                         │
│ 🔑 Models                               │
│    ├─ Chat Model                        │
│    ├─ Fast Edit Model                   │
│    └─ Embedding Model                   │
│                                         │
│ 🔗 Providers                            │
│    ├─ OpenAI                            │
│    ├─ Ollama                            │
│    └─ Other Providers                   │
│                                         │
│ ⚙️  Advanced Settings                    │
│                                         │
└─────────────────────────────────────────┘
```

---

## Step 3A: Via Continue UI (EASIEST)

**If you see "Ollama" option in the Providers section:**

```
1. Find "Providers" or "Models" section
2. Look for "Ollama" option
3. Click on it or toggle it
4. You should see fields like:
   - Base URL: [______________________]
   - Model: [______________________]
   
5. Fill in:
   - Base URL: http://localhost:11434
   - Model: qwen2.5-coder:14b
   
6. Test connection (should be a "Test" button)
```

---

## Step 3B: Via VS Code Settings (MANUAL)

**If Continue settings panel doesn't have Ollama config:**

```
1. Press Ctrl+, (Settings)
2. In VS Code Settings, search: "continue"
3. Look for "Continue: Model" or similar
4. You might see settings like:
   - continue.modelProvider
   - continue.modelName
   - continue.ollama
   
5. Configure what you find
```

---

## Step 3C: Via config.json (MOST DIRECT)

**Continue stores config in a JSON file. To edit directly:**

**On Windows, the file is usually at:**
```
C:\Users\Praveen\AppData\Local\Continue\config.json
```

**Do this:**

```
1. Press Ctrl+P in VS Code
2. Type: config.json
3. Look for Continue's config.json file
4. Open it
5. Find the "models" section
6. Add or modify the Qwen model entry
```

**What it should look like:**
```json
{
  "models": [
    {
      "title": "Qwen2.5-Coder",
      "provider": "ollama",
      "model": "qwen2.5-coder:14b",
      "apiBase": "http://localhost:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Qwen2.5-Coder",
    "provider": "ollama",
    "model": "qwen2.5-coder:14b",
    "apiBase": "http://localhost:11434"
  }
}
```

---

## ❌ Common Mistakes to Avoid

**❌ WRONG:**
```
- URL: localhost:11434 (missing http://)
- URL: http://localhost:11434/ (extra trailing slash)
- Model: qwen2.5-coder:latest (use 14b version)
- Model: qwen (use full name)
```

**✅ CORRECT:**
```
- URL: http://localhost:11434
- Model: qwen2.5-coder:14b
```

---

## Step 4: Test the Connection

**After configuring:**

```
1. In Continue settings, look for "Test Connection" button
2. Click it
3. Wait 3-5 seconds
4. You should see: "✅ Connection successful"
```

**If it fails:**
- Make sure Ollama is running: `ollama serve`
- Make sure the URL is exactly: `http://localhost:11434`
- Restart VS Code

---

## Step 5: Test Autocomplete

**Once configured:**

```
1. Create new Python file
2. Type: def hello(
3. Wait 1-2 seconds
4. You should see autocomplete suggestion
5. Press Tab to accept
6. Done! ✅
```

---

## The Settings Structure (Technical)

If you're editing JSON directly, here's the complete structure:

```json
{
  "models": [
    {
      "title": "Qwen2.5-Coder",
      "provider": "ollama",
      "model": "qwen2.5-coder:14b",
      "apiBase": "http://localhost:11434",
      "contextLength": 8000,
      "completionOptions": {
        "maxTokens": 1024
      }
    }
  ],
  
  "tabAutocompleteModel": {
    "title": "Qwen2.5-Coder",
    "provider": "ollama",
    "model": "qwen2.5-coder:14b",
    "apiBase": "http://localhost:11434"
  },
  
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "apiBase": "http://localhost:11434"
  }
}
```

**What each field means:**
- `title` — Display name in VS Code
- `provider` — Which service (ollama)
- `model` — Model name as shown in `ollama list`
- `apiBase` — Where Ollama is running
- `contextLength` — How much code it remembers
- `maxTokens` — Max length of suggestions
- `tabAutocompleteModel` — Which model for autocomplete
- `embeddingsProvider` — For code search features

---

## Quick Verification Checklist

After setup, verify:

- [ ] Continue extension installed in VS Code
- [ ] Ollama running (`ollama serve` in terminal)
- [ ] Model configured in Continue
- [ ] Base URL is: `http://localhost:11434`
- [ ] Model name is: `qwen2.5-coder:14b`
- [ ] Test connection shows ✅
- [ ] Type code and see autocomplete appear

---

## Troubleshooting

### "Connection failed"
```
1. Check Ollama is running:
   ollama serve
   
2. Verify URL in settings:
   Should be: http://localhost:11434
   
3. Restart VS Code (Ctrl+Shift+P → Developer: Reload Window)
```

### "Model not found"
```
1. Check installed models:
   ollama list
   
2. Should show: qwen2.5-coder:14b
   
3. If not, pull it:
   ollama pull qwen2.5-coder:14b
```

### "Autocomplete is slow"
```
1. Ollama might be loading model for first time
2. Wait 5 seconds before trying again
3. After first load, should be fast (~1 second)
4. If still slow, check if other apps are using GPU
5. Close Chrome, Discord, etc.
```

### "Settings don't seem to save"
```
1. Make sure you're editing the right file:
   C:\Users\Praveen\AppData\Local\Continue\config.json
   
2. After editing, restart VS Code:
   Ctrl+Shift+P → Developer: Reload Window
   
3. Check for JSON syntax errors (missing commas, brackets)
```

---

## Configuration Hierarchy (Priority Order)

Continue looks for config in this order:

```
1. VS Code Continue Extension Settings (UI)
   └─ If found, use this
   
2. config.json in Continue directory
   └─ If found, use this
   
3. Default settings
   └─ Fallback
```

**Best practice:** Use the UI if available, otherwise edit config.json

---

## What Happens After Setup

Once configured correctly:

```
You type code
    ↓
Continue watches (every keystroke)
    ↓
Sends to Ollama (http://localhost:11434)
    ↓
Qwen model generates suggestion
    ↓
Continue shows inline suggestion
    ↓
You press Tab or Escape
```

**Entire flow:** Usually 1-2 seconds

---

## Next Steps

1. ✅ Open Continue Settings
2. ✅ Configure Ollama provider
3. ✅ Set model to qwen2.5-coder:14b
4. ✅ Set base URL to http://localhost:11434
5. ✅ Test connection
6. ✅ Test autocomplete in a Python file

**Then you're good to code!** 🚀

---

## Additional Models (Optional)

If you want to add more models later:

```json
"models": [
  {
    "title": "Qwen2.5-Coder",
    "provider": "ollama",
    "model": "qwen2.5-coder:14b",
    "apiBase": "http://localhost:11434"
  },
  {
    "title": "DeepSeek-Coder",
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b",
    "apiBase": "http://localhost:11434"
  }
]
```

Then you can switch between them in VS Code! 🎯

---

**That's it! You've configured Continue to use your local AI model.** 🎉
