#!/usr/bin/env bash
# SessionStart hook for Book Factory.
#
# Prints to stdout, which Claude Code adds to the session's context.
# Must never fail the session: always exits 0, even when a step fails.
set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$PROJECT_DIR" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." >/dev/null 2>&1 && pwd)"
fi

# --- 1. Install test requirements, only in web (remote) sessions ---
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
    if python3 -c "import pytest, bookfactory, weasyprint" >/dev/null 2>&1; then
        echo "Test requirements: already present"
    else
        LOG_FILE="$(mktemp /tmp/bookfactory-session-start-pip.XXXXXX.log 2>/dev/null || echo /tmp/bookfactory-session-start-pip.log)"
        if (cd "$PROJECT_DIR" && python3 -m pip install -q -e ".[dev]" >"$LOG_FILE" 2>&1); then
            echo "Test requirements: installed"
        else
            echo "Test requirements: install FAILED, see $LOG_FILE"
        fi
    fi
fi

# --- 2. Branch check ---
CURRENT_BRANCH="$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || true)"
if [ -z "$CURRENT_BRANCH" ] && git -C "$PROJECT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    echo "NOTE: this session is not on any branch (detached HEAD). Book Factory works on main (CLAUDE.md, Branch policy): switch to main yourself (fetch origin main, check out main matching origin/main) before changing files. Do not ask the operator."
elif [ -n "$CURRENT_BRANCH" ] && [ "$CURRENT_BRANCH" != "main" ]; then
    echo "NOTE: this session started on branch $CURRENT_BRANCH, which the session setup chose, not the operator. Book Factory works on main (CLAUDE.md, Branch policy): switch to main yourself (fetch origin main, check out main matching origin/main) before changing files. Do not ask the operator."
fi

# --- 3. "Start here" block from PLAN.md ---
PLAN_FILE="$PROJECT_DIR/PLAN.md"
echo "From PLAN.md:"
if [ -f "$PLAN_FILE" ]; then
    awk '
        /^## Start here/ { printing=1 }
        printing && /^---$/ { exit }
        printing { print }
    ' "$PLAN_FILE"
else
    echo "(PLAN.md not found at $PLAN_FILE)"
fi

exit 0
