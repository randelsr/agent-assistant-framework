#!/usr/bin/env bash
# transcribe.sh: local, offline speech-to-text for voice notes and call recordings.
# Audio never leaves the machine.
#
# Stack (deliberately lightweight; no torch, no ffmpeg):
#   - afconvert   : macOS built-in. Converts anything to 16kHz mono WAV.
#   - whisper-cli : `brew install whisper-cpp`. Metal accelerated on Apple Silicon.
#   - models      : ~/.local/share/whisper-models/ggml-{small,medium}.en.bin
#                   (fetched on first use from the whisper.cpp model repo)
#
# Usage:
#   scripts/transcribe.sh <audio-file> [small|medium] [output-prefix]
#
# Model guidance:
#   small.en  (465MB) ~15s for 5 min of audio. Fine for gist and casual notes.
#   medium.en (1.5GB) ~60s for 5 min of audio. Use this whenever names, numbers,
#             addresses or decisions matter; small.en garbles proper nouns.
#
# Emits .txt (plain) and .vtt (timestamped) at the output prefix. Transcripts
# are lossy: re-listen via the .vtt timestamps before quoting anything
# load-bearing. whisper does no speaker diarization, so "who said what" is
# inference and must be flagged as such.

set -euo pipefail

SRC="${1:?usage: transcribe.sh <audio-file> [small|medium] [output-prefix]}"
SIZE="${2:-medium}"
case "$SIZE" in small|medium|base|large-v3) ;; *) echo "ERROR: unknown model size: $SIZE" >&2; exit 1 ;; esac
MODELDIR="$HOME/.local/share/whisper-models"
MODEL="$MODELDIR/ggml-${SIZE}.en.bin"
[ "$SIZE" = "large-v3" ] && MODEL="$MODELDIR/ggml-large-v3.bin"

if [ ! -f "$SRC" ]; then
  echo "ERROR: no such file: $SRC" >&2
  exit 1
fi

if [ $# -ge 3 ]; then
  OUT="$3"
else
  OUT="${SRC%.*}"
fi

command -v whisper-cli >/dev/null 2>&1 || {
  echo "ERROR: whisper-cli not found. Run: brew install whisper-cpp" >&2
  exit 1
}

if [ ! -f "$MODEL" ]; then
  echo "Model $SIZE not present, downloading to $MODEL ..." >&2
  mkdir -p "$MODELDIR"
  curl -L --fail --progress-bar -o "$MODEL.part" \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$(basename "$MODEL")"
  mv "$MODEL.part" "$MODEL"
fi

WAV="$(mktemp -t transcribe).wav"
trap 'rm -f "$WAV"' EXIT

echo "converting to 16kHz mono WAV (afconvert)" >&2
afconvert -f WAVE -d LEI16@16000 -c 1 "$SRC" "$WAV"

DUR="$(afinfo "$WAV" 2>/dev/null | awk '/estimated duration/{printf "%.0f", $3}')"
echo "${DUR}s of audio, model: $SIZE" >&2

echo "transcribing" >&2
whisper-cli -m "$MODEL" -f "$WAV" -otxt -ovtt -of "$OUT" 2>/dev/null

echo "wrote: ${OUT}.txt" >&2
echo "wrote: ${OUT}.vtt  (timestamped)" >&2
wc -w "${OUT}.txt" >&2
