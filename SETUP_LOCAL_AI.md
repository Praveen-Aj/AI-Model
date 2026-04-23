# Local AI Stack Setup Guide

Your AI development environment setup plan.

## ✅ Step 1: Start Ollama Service

**On Windows:** Ollama runs as a desktop app that listens on `http://localhost:11434`

```powershell
# Ollama should already be running. If not, start it from Windows Start Menu
# Or run: ollama serve
```

**Verify it's running:**
```powershell
curl http://localhost:11434
```

---

## 📥 Step 2: Pull Qwen2.5-Coder Model

This is the best model for your RTX 5050 + 24GB RAM setup.

```powershell
ollama pull qwen2.5-coder:14b
```

**Time:** ~5-10 minutes (8.2GB download)

After pulling, verify:
```powershell
ollama list
```

---

## 🤖 Step 3: Install Aider (Coding Agent)

Aider is your autonomous coding agent—like Windsurf but free and local.

```powershell
pip install aider-chat
```

**Test it:**
```powershell
aider --version
```

**Run in your project:**
```powershell
cd "c:\Users\Praveen\Downloads\Python Scripts\AI Model"
aider
```

---

## 💻 Step 4: Install Continue (Copilot Replacement)

This gives you inline autocomplete in VS Code.

**In VS Code:**
1. Install extension: **Continue.dev** (search in Extensions)
2. Open VS Code Settings (Ctrl+,)
3. Search for "Continue"
4. Configure:
   - Provider: `Ollama`
   - Model: `qwen2.5-coder:14b`
   - Base URL: `http://localhost:11434`

**Test:** Type a comment and watch autocomplete work!

---

## 🎯 Step 5: Terminal AI (Aider with Ollama)

Run this in your project terminal:

```powershell
aider --model ollama/qwen2.5-coder:14b
```

Now chat with AI in the terminal. Example:

```
add logging to all python files
```

Aider will edit everything automatically.

---

## 🚀 Step 6: Autonomous Mode (Windsurf-style)

Enable auto-commits for fully autonomous agent:

```powershell
aider --model ollama/qwen2.5-coder:14b --yes --auto-commits
```

Now you can type complex commands:

```
refactor this project to use async/await
install best practices for error handling
add type hints to all functions
```

The agent will:
- Plan changes
- Edit files
- Test
- Commit automatically
- Loop until done

---

## 📊 Performance Expectations

With your RTX 5050 + 24GB RAM:

- **Autocomplete:** Instant (~50ms)
- **Single file edit:** 1-3 seconds
- **Multi-file changes:** 5-15 seconds
- **Agent loops:** Smooth, continuous

---

## 📚 Quick Command Reference

| Task | Command |
|------|---------|
| Start Ollama | `ollama serve` |
| List models | `ollama list` |
| Pull Qwen | `ollama pull qwen2.5-coder:14b` |
| Run Aider | `aider` |
| Aider with model | `aider --model ollama/qwen2.5-coder:14b` |
| Auto mode | `aider --yes --auto-commits` |

---

## 🔧 Troubleshooting

**Ollama not responding?**
```powershell
# Check if service is running
Get-Process ollama

# Start it
ollama serve
```

**Model not found?**
```powershell
ollama pull qwen2.5-coder:14b
```

**Aider not working?**
```powershell
pip install --upgrade aider-chat
```

---

## 🎓 What You Now Have

✅ **Continue** - Copilot-style autocomplete  
✅ **Aider** - Windsurf-style agent  
✅ **Terminal AI** - Type commands, auto-edits files  
✅ **Local LLM** - No subscriptions, completely offline  

**Usage pattern:**
- Quick fix → Use autocomplete (Continue)
- Single file refactor → Use Continue chat
- Multi-file changes → Use Aider in terminal
- Complex project work → Use Aider with `--auto-commits`

---

## Next: Execute the Setup

Follow the steps above in order. Start with Step 1!
