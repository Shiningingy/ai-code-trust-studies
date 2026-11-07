#!/bin/bash
# Installed as /go/bin/go (ahead of the real go in PATH) for repos with nested Go modules.
# stage1 runs `go test ./path/to/pkg` from /work; Go refuses packages that belong to another module,
# so for build/test/vet/list this shim runs the real go inside the module that owns each ./pkg argument,
# with the argument rewritten relative to that module (what a developer would do with `cd module`).
# Anything else is passed through unchanged.
REAL=/usr/local/go/bin/go
case "$1" in test|build|vet|list) ;; *) exec "$REAL" "$@" ;; esac
modroot() {  # nearest directory at or above $1 holding a go.mod
  local d="$1"
  while [ "$d" != "/" ] && [ ! -f "$d/go.mod" ]; do d=$(dirname "$d"); done
  [ -f "$d/go.mod" ] && echo "$d" || echo ""
}
# A package directory the PR deleted does not exist at the merge commit: `go test` would stop with
# "directory not found" and report nothing for the other packages, so such arguments are dropped.
kept=(); dropped=0; haspkg=0
for a in "$@"; do
  case "$a" in
    ./*) p="${a%/...}"; if [ -d "$p" ]; then kept+=("$a"); haspkg=1; else dropped=1; fi ;;
    *) kept+=("$a") ;;
  esac
done
[ $dropped -eq 1 ] && [ $haspkg -eq 0 ] && exit 0
set -- "${kept[@]}"
declare -A group
order=()
args=("$@")
kind=()
for i in "${!args[@]}"; do
  a="${args[$i]}"
  kind[$i]=""
  case "$a" in
    ./*|.)
      p="${a%/...}"
      abs=$(realpath -m "$PWD/$p")
      m=$(modroot "$abs")
      [ -z "$m" ] && m="$PWD"
      kind[$i]="$m"
      [ -z "${group[$m]}" ] && { group[$m]=1; order+=("$m"); }
      ;;
  esac
done
if [ ${#order[@]} -eq 0 ] || { [ ${#order[@]} -eq 1 ] && [ "${order[0]}" = "$(modroot "$PWD")" ]; }; then
  exec "$REAL" "$@"
fi
rc=0
for m in "${order[@]}"; do
  new=()
  for i in "${!args[@]}"; do
    a="${args[$i]}"
    if [ -z "${kind[$i]}" ]; then new+=("$a")
    elif [ "${kind[$i]}" = "$m" ]; then
      suffix=""; p="$a"
      case "$a" in */...) suffix="/..."; p="${a%/...}";; esac
      abs=$(realpath -m "$PWD/$p")
      if [ "$abs" = "$m" ]; then rel="."; else rel="./${abs#$m/}"; fi
      new+=("$rel$suffix")
    fi
  done
  (cd "$m" && "$REAL" "${new[@]}") || rc=$?
done
exit $rc
