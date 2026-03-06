#!/bin/bash
# Show a notification with context about what just finished

payload=$(cat)
transcript_path=$(echo "$payload" | jq -r '.transcript_path // empty')

if [[ -z "$transcript_path" ]] || [[ ! -f "$transcript_path" ]]; then
    exit 0
fi

# Get last user message preview
last_user_msg=$(tac "$transcript_path" 2>/dev/null | grep -m1 '"type": "user"' | jq -r '.message.content // empty' 2>/dev/null | sed 's/"/\\"/g' | head -c 50)

# Build notification text
if [[ -n "$last_user_msg" ]]; then
    text="$last_user_msg..."
else
    text="Response ready"
fi

# Show notification with sound (properly escaped for osascript)
osascript <<EOF
display notification "$text" with title "Claude Code" sound name "Glass"
EOF
