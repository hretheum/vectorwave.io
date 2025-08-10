# LinkedIn Automation CLI Documentation

## 🚀 Overview

LinkedIn CLI to kompletne narzędzie do zarządzania automatyzacją LinkedIn z obsługą:
- Manual session creation dla różnych kont
- Automatyczna diagnostyka selektorów
- Multi-account support
- Error handling z auto-diagnostic

## 📦 Installation

```bash
npm install

# Make CLI executable
chmod +x scripts/linkedin-cli.js

# Optional: create global alias
alias linkedin-cli="node $(pwd)/scripts/linkedin-cli.js"
```

## 🔧 Quick Start

### 1. Create New Session (Production Setup)

```bash
# Create session for default account
node scripts/linkedin-cli.js session create

# Create session for specific account
node scripts/linkedin-cli.js session create --account production

# Create session for personal account
node scripts/linkedin-cli.js session create --account personal
```

**Process:**
1. Browser otworzy się automatycznie
2. Zaloguj się ręcznie do LinkedIn
3. Rozwiąż CAPTCHA/2FA jeśli potrzebne
4. Poczekaj aż zobaczysz swój feed
5. CLI automatycznie wykryje pomyślne logowanie
6. Session zostanie zapisany do wielokrotnego użytku

### 2. List Available Sessions

```bash
node scripts/linkedin-cli.js session list

# Output:
# ● ACTIVE default
#      Session ID: local-session-12345...
#      Created: 2025-08-04 10:30:00
#      Last used: 2025-08-04 11:00:00
#
#   production
#      Session ID: local-session-67890...
#      Created: 2025-08-03 14:00:00
#      Last used: 2025-08-03 15:30:00
```

### 3. Validate Session

```bash
# Validate current active session
node scripts/linkedin-cli.js session validate

# Validate specific account
node scripts/linkedin-cli.js session validate --account production
```

### 4. Switch Active Session

```bash
node scripts/linkedin-cli.js session switch
# Interactive prompt to select account
```

## 📊 Diagnostics

### Run Full Diagnostic

```bash
# Diagnose current session
node scripts/linkedin-cli.js diagnose

# Diagnose with auto-fix attempt
node scripts/linkedin-cli.js diagnose --fix

# Diagnose specific account
node scripts/linkedin-cli.js diagnose --account production
```

**Diagnostic checks:**
- ✅ Share box selector
- ✅ Composer selector
- ✅ Publish button selector
- ✅ Media upload selector
- ✅ Schedule button selector

### Automatic Diagnostics on Error

Gdy publikacja nie powiedzie się z powodu selektorów:
```bash
node scripts/linkedin-cli.js publish -c "Test post"

# If selectors fail:
# ❌ Selector error detected!
# LinkedIn may have updated their interface.
# 
# 🔧 Running automatic diagnostics...
# [diagnostic results]
# 
# 💡 After fixing selectors, try publishing again.
```

## 📤 Publishing Posts

### Immediate Post

```bash
# Simple text post
node scripts/linkedin-cli.js publish -c "Your post content here"

# With PDF attachment
node scripts/linkedin-cli.js publish -c "Check out this document" -p "/path/to/file.pdf"

# Using specific account
node scripts/linkedin-cli.js publish -c "Company update" -a production
```

### Scheduled Post

```bash
# Schedule for specific time
node scripts/linkedin-cli.js publish -c "Future post" -s "2025-08-05T14:30:00Z"

# Schedule with PDF
node scripts/linkedin-cli.js publish -c "Weekly report" -s "2025-08-05T09:00:00Z" -p "report.pdf"
```

## ⚙️ Configuration

### Configure CLI Settings

```bash
node scripts/linkedin-cli.js config

# Interactive prompts:
# - Enable automatic diagnostics on selector errors? (Y/n)
# - Enable verbose logging? (y/N)
# - Default schedule delay in minutes: (30)
```

### Config File Location
```
data/config.json
```

### Example Config
```json
{
  "activeAccount": "default",
  "autodiagnose": true,
  "verboseLogging": false,
  "defaultScheduleDelay": 30
}
```

## 🔐 Session Management

### Session Files Structure
```
data/sessions/
├── default_session.json      # Quick session info
├── default_context.json      # Full browser context
├── production_session.json
├── production_context.json
├── personal_session.json
└── personal_context.json
```

### Session Persistence
- Sessions są valid przez ~30 dni
- Cookies i localStorage są zachowane
- Auto-restoration przy każdym użyciu
- Multi-account isolation

## 🚨 Error Handling

### Common Errors and Solutions

#### 1. Session Expired
```
❌ Session validation failed: Session expired - login required

💡 Session expired. Create a new one:
   linkedin-cli session create --account default
```

#### 2. Selector Not Found
```
❌ Selector error detected!
LinkedIn may have updated their interface.

🔧 Running automatic diagnostics...
[diagnostic results show missing selectors]

💡 After fixing selectors, try publishing again.
```

#### 3. Network Error
```
❌ Publishing failed: Network timeout

💡 Network error. Check your connection and try again.
```

## 🛠️ Advanced Usage

### Programmatic Use

```javascript
const { LinkedInCLI } = require('./scripts/linkedin-cli');

// Use CLI programmatically
const cli = new LinkedInCLI();
await cli.createSession({ account: 'production' });
await cli.publishPost({
    content: 'Automated post',
    scheduleTime: '2025-08-05T10:00:00Z',
    account: 'production'
});
```

### Integration with CrewAI

```javascript
// When CrewAI sends future publication date
const scheduleTime = crewAiResponse.scheduledDate;

if (scheduleTime) {
    // Use CLI with schedule
    exec(`linkedin-cli publish -c "${content}" -s "${scheduleTime}"`);
} else {
    // Immediate publish
    exec(`linkedin-cli publish -c "${content}" --immediate`);
}
```

### Diagnostic Integration

```javascript
try {
    await publisher.publishPost(options);
} catch (error) {
    if (error.type === 'SELECTOR_ERROR') {
        // Auto-run diagnostics
        const diagnostic = new SelectorDiagnostic();
        const results = await diagnostic.runFullDiagnostic();
        
        // Apply selector updates
        if (results.shareBox?.found) {
            updateSelector('shareBox', results.shareBox.found);
        }
    }
}
```

## 📝 Maintenance

### Regular Tasks

1. **Weekly**: Validate all sessions
   ```bash
   for account in default production personal; do
     linkedin-cli session validate --account $account
   done
   ```

2. **Monthly**: Recreate sessions (LinkedIn security)
   ```bash
   linkedin-cli session create --account production
   ```

3. **On LinkedIn Updates**: Run diagnostics
   ```bash
   linkedin-cli diagnose --fix
   ```

### Backup Sessions

```bash
# Backup all sessions
cp -r data/sessions data/sessions.backup

# Restore sessions
cp -r data/sessions.backup/* data/sessions/
```

## 🎯 Best Practices

1. **Separate Accounts**: Use different accounts for dev/prod
2. **Regular Validation**: Check sessions weekly
3. **Error Monitoring**: Enable autodiagnose in config
4. **Scheduled Posts**: Use UTC times for consistency
5. **PDF Uploads**: Keep files under 10MB

## 🚀 Production Deployment Checklist

- [ ] Create production LinkedIn account
- [ ] Run `linkedin-cli session create --account production`
- [ ] Validate session: `linkedin-cli session validate --account production`
- [ ] Test publish: `linkedin-cli publish -c "Test" -a production`
- [ ] Run diagnostics: `linkedin-cli diagnose -a production`
- [ ] Configure auto-diagnostics: `linkedin-cli config`
- [ ] Set production as active: `linkedin-cli session switch`
- [ ] Update .env with production session ID
- [ ] Test scheduled post functionality
- [ ] Backup session files

---

**Note**: This CLI is designed for production use with automatic error recovery and multi-account support. Always test thoroughly with your production LinkedIn account before going live.