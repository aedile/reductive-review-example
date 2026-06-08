#!/usr/bin/env bash
# Audits the review trail's internal consistency. A repo whose whole claim is
# "auditable, graded, counted findings" should be able to audit its own counts.
#
# Checks:
#   1. RUN-LOG raw B/F/A per critic == graded entries actually in each round file,
#      with NO silent skips: exactly 24 critic files must exist, and every RUN-LOG
#      detail row must map to a file (orphans on either side fail).
#   2. README "descent at a glance" arbitrated B/F/A == each round-NNN.md count table.
#   3. Every §-citation in the rounds resolves to a heading in the design doc.
#   4. RUN-LOG arithmetic that is stated exactly: the run count (24) and the total
#      tool-call count both recomputed from the per-critic detail table.
#
# Exit 0 if everything reconciles, 1 otherwise. Deps: bash, awk, grep, comm (coreutils).
set -u
cd "$(dirname "$0")/.." || exit 2
ROUNDS=docs/reviews/rounds
DOC=docs/design/magic-link-auth.md
RUNLOG=docs/reviews/RUN-LOG.md
README=README.md
fail=0
note() { printf '%s\n' "$*"; }

# Count graded "### " entries under each "## BLOCKER/FINDING/ADVISORY" section.
graded() { awk '
  /^## BLOCKER/{s="B";next} /^## FINDING/{s="F";next} /^## ADVISORY/{s="A";next}
  /^## /{s="";next} /^### /{if(s=="B")b++;else if(s=="F")f++;else if(s=="A")a++}
  END{printf "%d/%d/%d",b+0,f+0,a+0}' "$1"; }

note "== 1. RUN-LOG raw counts vs round files (no silent skips) =="
checked=0
for n in 001 002 003 004 005 006; do
  for c in security systems product skeptic; do
    if [ ! -f "$ROUNDS/round-$n/$c.md" ]; then
      note "  FAIL missing file: round-$n/$c.md"; fail=1; continue
    fi
    checked=$((checked + 1))
    file=$(graded "$ROUNDS/round-$n/$c.md")
    case $c in
      security) name="Security Adversary";; systems) name="Systems Engineer";;
      product) name="Product / UX";; skeptic) name="Skeptical Generalist";;
    esac
    # trailing-pipe-anchored match so "Foo" can't prefix-match "Foo II"
    rl=$(grep -E "^\| $n \| $name *\|" "$RUNLOG" | awk -F'|' '{v=$(NF-1); gsub(/ /,"",v); print v}')
    if [ -z "$rl" ]; then
      note "  FAIL no RUN-LOG row for round-$n $c"; fail=1
    elif [ "$file" != "$rl" ]; then
      note "  FAIL round-$n $c: file=$file RUN-LOG=$rl"; fail=1
    fi
  done
done
# Assert the count is exactly 24 (a deleted file lowers `checked`, an added one raises it).
if [ "$checked" -ne 24 ]; then note "  FAIL expected 24 critic files, checked $checked"; fail=1; fi
# Orphan detection the other way: every RUN-LOG detail row must have been consumed.
rl_rows=$(grep -cE '^\| 00[1-6] \| (Security Adversary|Systems Engineer|Product / UX|Skeptical Generalist) *\|' "$RUNLOG")
if [ "$rl_rows" -ne 24 ]; then note "  FAIL RUN-LOG has $rl_rows detail rows, expected 24"; fail=1; fi
[ $fail -eq 0 ] && note "  ok (24 critic files == 24 RUN-LOG rows, all reconcile)"

note "== 2. README descent table vs round aggregate count tables =="
for n in 001 002 003 004 005 006; do
  b=$(grep -cE '^\| B[0-9]' "$ROUNDS/round-$n.md")
  f=$(grep -cE '^\| F[0-9]' "$ROUNDS/round-$n.md")
  a=$(grep -cE '^\| A[0-9]' "$ROUNDS/round-$n.md")
  rn=$(grep -E "^\| $n " "$README" | head -1 | awk -F'|' '{gsub(/ /,"",$4);gsub(/ /,"",$5);gsub(/ /,"",$6);print $4"/"$5"/"$6}')
  if [ "$b/$f/$a" != "$rn" ]; then
    note "  FAIL round-$n: aggregate=$b/$f/$a README=$rn"; fail=1
  fi
done
[ $fail -eq 0 ] && note "  ok (6 rounds)"

note "== 3. round §-citations resolve to a doc heading =="
anchors=$(grep -oE '^#+ §[0-9]+(\.[0-9]+)?' "$DOC" | grep -oE '§[0-9]+(\.[0-9]+)?' | sort -u)
# §0 is a critic's *suggestion* to add a section, not a reference to an existing one.
missing=$(comm -23 <(grep -rhoE '§[0-9]+(\.[0-9]+)?' "$ROUNDS" | sort -u) <(printf '%s\n' "$anchors") | grep -v '^§0$')
if [ -n "$missing" ]; then note "  FAIL unresolved citations: $missing"; fail=1; else note "  ok"; fi

note "== 4. RUN-LOG exact arithmetic (run count, tool-call total) =="
# Recompute from the per-critic detail table: column 2 = round, col 5 = tool calls.
runs=$(grep -cE '^\| 00[1-6] \|' "$RUNLOG")
tools=$(grep -E '^\| 00[1-6] \|' "$RUNLOG" | awk -F'|' '{t=$6; gsub(/ /,"",t); s+=t} END{print s}')
stated_runs=$(grep -oE '24 critic runs' "$RUNLOG" | head -1 | grep -oE '^[0-9]+')
stated_tools=$(grep -oE '[0-9]+ critic tool calls' "$RUNLOG" | head -1 | grep -oE '^[0-9]+')
if [ "$runs" != "${stated_runs:-x}" ]; then note "  FAIL run count: table=$runs stated=$stated_runs"; fail=1; fi
if [ "$tools" != "${stated_tools:-x}" ]; then note "  FAIL tool-call total: table sums to $tools, stated $stated_tools"; fail=1; fi
[ $fail -eq 0 ] && note "  ok (runs=$runs, tool-calls=$tools recomputed == stated)"

echo
if [ $fail -eq 0 ]; then echo "CONSISTENT — the trail reconciles."; else echo "INCONSISTENT — see FAILs above."; fi
exit $fail
