#!/usr/bin/env bash
# Create symlinks so Claude Code discovers AGENTS.md and .agents/skills/.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

ln -sf AGENTS.md CLAUDE.md
mkdir -p .claude
ln -sfn ../.agents/skills .claude/skills

echo "Claude Code symlinks created: CLAUDE.md -> AGENTS.md, .claude/skills -> .agents/skills"
