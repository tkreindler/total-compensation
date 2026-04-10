#!/usr/bin/env bash

# Install symlinks that are needed on every re-connection to the development container

mkdir -p /home/vscode/.claude/
ln -sf /home/vscode/claude-persistent/.claude.json /home/vscode/.claude.json
ln -sf /home/vscode/claude-persistent/.claude/settings.json /home/vscode/.claude/settings.json
