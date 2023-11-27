#!/bin/bash

echo "Setting up the environment..."

DEFAULT_MODELS_CACHE_DIR="$HOME/.cache/tortoise/tmp"
MODELS_DIR="${TORTOISE_MODELS_DIR:-$HOME/.cache/tortoise/models}"

declare -A MODELS
MODELS=(
    ["autoregressive.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/autoregressive.pth"
    ["classifier.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/classifier.pth"
    ["clvp2.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/clvp2.pth"
    ["cvvp.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/cvvp.pth"
    ["diffusion_decoder.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/diffusion_decoder.pth"
    ["vocoder.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/vocoder.pth"
    ["rlg_auto.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/rlg_auto.pth"
    ["rlg_diffuser.pth"]="https://huggingface.co/jbetker/tortoise-tts-v2/resolve/main/.models/rlg_diffuser.pth"
)

function download_models() {
    mkdir -p "$MODELS_DIR"
    mkdir -p "$DEFAULT_MODELS_CACHE_DIR"

    for model_name in "${!MODELS[@]}"; do
        model_cache_path="$DEFAULT_MODELS_CACHE_DIR/$model_name"
        model_path="$MODELS_DIR/$model_name"
        url="${MODELS[$model_name]}"

        if [[ -e "$model_path" ]]; then
          echo "$model_name already installed"
          continue
        fi

        echo "Downloading $model_name from $url"
        wget --trust-server-names --show-progress --progress=bar:force -O "$model_cache_path" "$url"
        echo "Moving from $model_cache_path to $model_path"
        mv "$model_cache_path" "$model_path"
        echo "Done."
    done


}

download_models

echo "Starting Flask Server..."

python app.py