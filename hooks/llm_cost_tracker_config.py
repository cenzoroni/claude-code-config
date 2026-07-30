# Pricing per million tokens (USD)
# Update when Anthropic changes rates: https://www.anthropic.com/pricing
PRICING = {
    "claude-sonnet-4-6": {
        "input":       3.00,
        "cache_write": 3.75,
        "cache_read":  0.30,
        "output":     15.00,
    },
    "claude-sonnet-4-5": {
        "input":       3.00,
        "cache_write": 3.75,
        "cache_read":  0.30,
        "output":     15.00,
    },
    "claude-haiku-4-5": {
        "input":       0.80,
        "cache_write": 1.00,
        "cache_read":  0.08,
        "output":      4.00,
    },
    "claude-opus-4-6": {
        "input":      15.00,
        "cache_write":18.75,
        "cache_read":  1.50,
        "output":     75.00,
    },
    # Fallback for unknown/synthetic models
    "default": {
        "input":       3.00,
        "cache_write": 3.75,
        "cache_read":  0.30,
        "output":     15.00,
    },
}

# Map ~/.claude/projects/ directory names → friendly project names
# Directories not listed here will use the slug after stripping the base prefix
BASE_PREFIX = "-Users-vince-repos-"
PROJECT_NAMES = {
    "-Users-vince-repos-gofish":        "gofish",
    "-Users-vince-repos-stock-sandbox": "stock_sandbox",
    "-Users-vince-repos-Financials":    "Financials",
    "-Users-vince-repos-sandbox":       "sandbox",
    "-Users-vince-repos":               "(repos root)",
    "-Users-vince":                     "(home)",
}
