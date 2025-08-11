"""
Kolegium CLI Playbooks

Run crews from the command line, returning JSON to stdout.

Examples:
  python -m kolegium.playbooks.style --draft "text" --platform linkedin
  python -m kolegium.playbooks.audience --topic "AI agents" --platform linkedin \
    --research-summary "..." --editorial-recs "..."
  python -m kolegium.playbooks.writer --topic "AI agents" --platform LinkedIn \
    --audience-insights "technical" --research-summary "..." --depth 2
  python -m kolegium.playbooks.quality --draft "..." --platform linkedin --content-type article
  python -m kolegium.playbooks.research --topic "AI agents" --sources-path content/README.md --context "..."
"""
