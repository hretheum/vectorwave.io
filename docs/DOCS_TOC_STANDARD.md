# Documentation ToC Standard

Standard conventions for README table of contents and anchors across services.

## ToC Rules
- Place ToC right after the title and short overview
- Use second-level headings (##) for main sections and third-level (###) for subsections
- Keep titles concise; prefer nouns or short noun phrases
- Include links to: Overview, Architecture, Quick Start, Configuration, API, Health/Monitoring, Testing, Troubleshooting, KPIs, References

## Anchors and Linking
- Use GitHub-compatible anchors (auto-generated from headings)
- For cross-doc references, prefer relative links (e.g., ../docs/FILE.md)
- For Obsidian, ensure headings map to internal links properly

## Section Order (Canonical)
1. Overview
2. Architecture
3. Quick Start
4. Configuration
5. API Endpoints
6. Health, Monitoring, Metrics
7. Data and Storage (if any)
8. Testing
9. Troubleshooting
10. KPIs and Validation
11. Roadmap and Status
12. References

## Checklist
- [ ] ToC present and matches section order
- [ ] All headings unique and descriptive
- [ ] All code blocks runnable/correct
- [ ] Links are relative and valid
- [ ] Environment variables documented with examples
