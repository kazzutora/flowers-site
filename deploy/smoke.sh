#!/usr/bin/env sh
# What a deploy has to prove before anyone calls it done.
#
#   ./deploy/smoke.sh https://example.com
#
# Every check below is one the site would fail loudly on: a broken home page, a
# missing admin, an invalid sitemap, or - the one that matters most - an
# original photo reachable over HTTP.

set -eu

BASE="${1:-http://localhost}"
FAILURES=0

check() {
    label="$1"
    expected="$2"
    path="$3"
    # Redirects are not followed: a 302 from /admin/ is the answer, not a step.
    actual=$(curl -sS -o /dev/null -w '%{http_code}' "${BASE}${path}" || echo "000")
    if [ "$actual" = "$expected" ]; then
        printf 'ok    %-28s %s\n' "$label" "$actual"
    else
        printf 'FAIL  %-28s expected %s, got %s\n' "$label" "$expected" "$actual"
        FAILURES=$((FAILURES + 1))
    fi
}

check "home"            200 "/"
check "gallery"         200 "/galereya/"
check "admin"           302 "/admin/"
check "healthz"         200 "/healthz/"
check "robots"          200 "/robots.txt"
check "sitemap"         200 "/sitemap.xml"
check "404"             404 "/nemaye-takoyi-storinky/"

# The originals live in a volume nginx does not mount. Both spellings must miss.
check "private original" 404 "/media/private/works/2026/01/original.jpg"
check "private path"     404 "/media/works/2026/01/original.jpg"

echo "==> sitemap is well formed"
if curl -sS "${BASE}/sitemap.xml" | head -c 200 | grep -q "<?xml"; then
    echo "ok    sitemap xml"
else
    echo "FAIL  sitemap xml"
    FAILURES=$((FAILURES + 1))
fi

if [ "$FAILURES" -ne 0 ]; then
    echo "$FAILURES check(s) failed" >&2
    exit 1
fi
echo "all checks passed"
