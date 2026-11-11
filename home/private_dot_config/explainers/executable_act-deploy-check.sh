#!/usr/bin/env bash
# Exit 0 when every prod service an act commit touches runs an image containing it, 1 when
# not yet. Prod images are pinned in gitops clusters/prod/env.global.yaml as `<app>: tag: prod-<sha>`.
# A commit touching no app (libs only) is judged by the image most services run.
set -uo pipefail
SHA="${1:?usage: act-deploy-check.sh <merge sha>}"
ACT="${ACT_REPO:-$HOME/git/act-security/act}"; GITOPS="${GITOPS_REPO:-$HOME/git/act-security/gitops}"
git -C "$GITOPS" fetch -q origin main && git -C "$ACT" fetch -q origin main || exit 2
ENV_FILE="$(git -C "$GITOPS" show origin/main:clusters/prod/env.global.yaml)" || exit 2
APPS="$(git -C "$ACT" show --name-only --format= "$SHA" | awk -F/ '$1 == "apps" { print $2 }' | sort -u)"
TAGS=""
for app in $APPS; do
  TAGS="$TAGS $(printf '%s\n' "$ENV_FILE" | awk -v key="  $app:" '$0 == key { getline; print $2 }')"
done
[ -n "${TAGS// }" ] || TAGS="$(printf '%s\n' "$ENV_FILE" | awk '/tag: prod-/ { print $2 }' | sort | uniq -c | sort -rn | awk 'NR == 1 { print $2 }')"
for tag in $TAGS; do
  git -C "$ACT" merge-base --is-ancestor "$SHA" "${tag#prod-}" 2>/dev/null || exit 1
done
