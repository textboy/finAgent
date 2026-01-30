#!/bin/bash

# configure your workspace
cd /app/workspace/finAgent/results && latestmd=$(ls -t | grep "\.md$" | head -n 1) && [ -n "$latestmd" ] && glow "$latestmd" || echo "No .md files found."