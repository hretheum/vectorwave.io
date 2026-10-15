# 📘 TECHNICAL CONTENT EDITORIAL STYLEBOOK
## Ready-to-Use Guide for AI & Tech Writing

---

## 🎯 QUICK REFERENCE CHECKLIST

Before publishing ANY content, verify:
- [ ] Zero corporate speak or LLM markers
- [ ] 2-3 key points developed deeply (rest mentioned briefly)
- [ ] Natural asymmetry in paragraph lengths
- [ ] Concrete metrics/examples, not abstractions
- [ ] Platform-appropriate adaptations
- [ ] AI compatibility structure (if relevant)
- [ ] Security review for code examples

---

## 📝 PART 1: WRITING RULES

### **ABSOLUTE BANS**
Never use:
- Name-dropping experience ("After 20 years...")
- Corporate speak (leverage, synergies, paradigm)
- Empty connectors ("It's worth noting", "Delving into")
- Compulsive lists (10+ items of 2-3 words each)
- Fake empathy ("You might be wondering...")

### **NATURAL WRITING PATTERNS**

#### **Asymmetry Rule**
Mix:
- 1-sentence paragraphs
- 10-sentence deep dives  
- 3-4 sentence bridges
- Varying sentence complexity

#### **Selective Focus Rule**
- Pick 2-3 core points → develop deeply
- Mention 3-4 secondary points → briefly
- Ignore everything else

#### **Evidence Hierarchy**
1. Your measured data (benchmarks, costs)
2. Industry reports with links
3. Code examples that work
4. User feedback/quotes
Never: Vague claims without proof

---

## 🤖 PART 2: AI-COMPATIBLE STRUCTURE

### **For AI-Readable Content**
```
Structure:
- H1: Main topic
- H2: Major sections (3-5)
- H3: Subsections (2-3 per H2)
- H4: Details (optional)
```

### **Language Adaptations**
- Repeat key terms (not pronouns)
- Define acronyms each section
- 5-10 FAQs at article end
- Context-rich explanations

### **Code Documentation Standards**
```python
# BAD: Quick example
print(data)

# GOOD: Complete, runnable
import json

def process_data(filepath):
    """Process JSON data with error handling."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "File not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

# Usage
result = process_data('config.json')
print(result)
```

---

## 📊 PART 3: FACT-CHECKING PROTOCOL

### **Pre-Publication Verification**

#### **Extract Claims**
```markdown
CLAIMS TO VERIFY:
1. Performance: X faster - Source: [benchmark.py]
2. Cost: $Y savings - Source: [invoice.pdf]
3. Users: Z adoption - Source: [analytics]
```

#### **Verification Levels**
- **Level 1**: Personal measurement (strongest)
- **Level 2**: Primary source (company blog/docs)
- **Level 3**: Reputable third party
- **Never cite**: Second-hand blogs, Reddit, Quora

#### **Code Security Check**
- [ ] No real API keys
- [ ] No production URLs
- [ ] No user PII
- [ ] Clear placeholder markers

---

## 📱 PART 4: PLATFORM ADAPTATIONS

### **Tech Blog/Substack (Long-form)**
- **Structure**: Progressive disclosure (overview → details → implementation)
- **Length**: 1500-3000 words
- **Code**: Full examples with explanations
- **Visuals**: Architecture diagrams, benchmarks
- **Voice**: Technical but accessible

### **LinkedIn (Professional)**
- **Structure**: Executive summary → 3 key points → CTA
- **Length**: 300-1300 characters optimal
- **Code**: Snippets or metrics only
- **Visuals**: Carousel for complex topics
- **Voice**: Business value focus

Example:
```
Cut AWS costs 73% with one architecture change.

The problem: Framework bloat (208MB for hello world)
The solution: Rebuild with core libraries (17MB)
The result: $6,692 annual savings

Full breakdown: [link]

What's your biggest infrastructure waste?
```

### **X/Twitter (Rapid-fire)**
- **Structure**: Hook → proof → thread if needed
- **Length**: <280 chars per tweet
- **Code**: Screenshots or key metrics
- **Voice**: Punchy, controversial OK

Example:
```
LangChain in 2025 = jQuery in 2015

Still useful. No longer differentiating.

The real skill: Building autonomous agents that actually work.

Thread on what to learn instead 🧵
```

---

## 📏 PART 5: QUALITY METRICS

### **Content Scoring**
Track per article:
- **Readability**: Grade 7-8 (Flesch-Kincaid)
- **Engagement**: >3 min average read time
- **Accuracy**: <1% correction rate
- **Conversion**: >2% CTA click-through

### **Performance Indicators**
- Bounce rate <40%
- Scroll depth >60%
- Comments quality (not quantity)
- Technical accuracy feedback

---

## 🔄 PART 6: REVIEW PROCESS

### **Self-Review (Before Submit)**
1. Run grammar check (Grammarly/Hemingway)
2. Verify all claims with sources
3. Test all code examples
4. Check platform-specific requirements

### **Peer Review Focus**
- Technical accuracy
- Security issues
- Brand voice consistency
- Accessibility (alt text, contrast)

### **Final Checks**
- [ ] Headlines: Clear value proposition
- [ ] Opening: Hook within 10 seconds
- [ ] Structure: Scannable with headers
- [ ] Conclusion: Clear next action

---

## 🚀 PART 7: CONTENT TEMPLATES

### **Technical Deep Dive Template**
```markdown
# [Problem-Focused Title]

[1-sentence problem statement with metric]

## The Real Cost

[Specific pain point with numbers]

## What I Tried First

[Failed approach - builds credibility]

## The Solution

[Core insight + implementation]

### Implementation Details
[Code with full context]

### Results
- Metric 1: [Before] → [After]
- Metric 2: [Before] → [After]

## Try It Yourself
[Clear next steps]
```

### **Tool Comparison Template**
```markdown
# [Tool A] vs [Tool B]: Measured Comparison

Tested both for [specific use case].

## Setup
[How tested, what metrics]

## Results Table
| Metric | Tool A | Tool B |
|--------|--------|--------|
| Speed  | Xms    | Yms    |
| Memory | XMB    | YMB    |
| Cost   | $X     | $Y     |

## When to Use Each
- Tool A: [Specific scenarios]
- Tool B: [Different scenarios]

## Implementation Examples
[Working code for both]
```

---

## ⚡ PART 8: RAPID DECISIONS

### **Title Selection**
- **Good**: "Cut AWS Costs 73% with This Architecture Change"
- **Bad**: "A Comprehensive Guide to Cloud Cost Optimization"

### **Opening Lines**
- **Good**: "LiteCrew uses 17MB. CrewAI uses 208MB. Here's why."
- **Bad**: "In today's rapidly evolving landscape..."

### **Evidence Presentation**
- **Good**: "Benchmark: 3.3s → 0.008s (code: github.com/...)"
- **Bad**: "Significantly faster performance"

### **Call-to-Action**
- **Good**: "Try the benchmark yourself: [repo link]"
- **Bad**: "Feel free to reach out if you have questions"

---

## 🎬 EMERGENCY FIXES

### **Too Corporate?**
Replace abstract nouns with concrete verbs:
- "Optimization" → "Make faster"
- "Leverage" → "Use"
- "Solution" → "Fix"

### **Too Symmetric?**
Break patterns:
- Add 1-sentence paragraph
- Remove transition sentence
- Jump directly to new topic

### **Too Generic?**
Add specifics:
- Company names
- Exact numbers
- Actual code
- Real screenshots

---

## 📋 FINAL REMINDERS

1. **You're not writing documentation, you're solving problems**
2. **Every claim needs proof you can defend**
3. **Platform determines depth, not quality**
4. **Readers want insights, not summaries**
5. **Code must work first time**

**When in doubt**: Would you read this if you didn't write it?

---

*Version 1.0 | Last updated: 2025*