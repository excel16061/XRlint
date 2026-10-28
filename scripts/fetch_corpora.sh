#!/usr/bin/env bash
# Download the benign corpora used in the README, pinned to the commits that were scanned.
# Usage: bash scripts/fetch_corpora.sh   (creates data/corpora/, ignored by git)
set -euo pipefail
mkdir -p data/corpora
cd data/corpora

fetch() {  # repo full-commit folder
  if [ ! -d "$3" ]; then
    git init --quiet "$3"
    git -C "$3" remote add origin "https://github.com/$1.git"
  fi
  git -C "$3" fetch --quiet --depth 1 origin "$2"
  git -C "$3" checkout --quiet FETCH_HEAD
  echo "$1 @ $(git -C "$3" log -1 --format='%h %cs')"
}

fetch aframevr/aframe        022bcc5f6eef09ff60d3f2110604c78cae0cd5b1 aframe
fetch aframevr/a-painter     0deba1f3314ee4cd053bf2a2ae2854994014dd65 a-painter
fetch supermedium/moonrider  f756aa6928f3e91ce4bde4bc496a8b86f3edeb79 moonrider
fetch supermedium/superframe a46f0a4f1e2bb36ce3157272ce0bcc678bec2422 superframe
fetch c-frame/aframe-extras  676f3628bb477d646293f9743eda31aca556114a aframe-extras
