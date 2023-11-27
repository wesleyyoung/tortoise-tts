import json
import os
import torchaudio
from tortoise.api import TextToSpeech, MODELS_DIR
from tortoise.utils.audio import load_voices

DEFAULT_RESULT_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'tortoise', 'results')
RESULT_DIR = os.environ.get('RESULT_DIR', DEFAULT_RESULT_DIR)


def do_tts(uid, voice, text, candidates, preset, seed, cvvp_amount):
    tts = TextToSpeech(models_dir=MODELS_DIR)
    voice_samples, conditioning_latents = load_voices([voice])

    gen, (deterministic_seed) = \
        tts.tts_with_preset(text, k=candidates, voice_samples=voice_samples,
                            conditioning_latents=conditioning_latents,
                            preset=preset, use_deterministic_seed=seed,
                            return_deterministic_state=True, cvvp_amount=cvvp_amount)

    output_path = os.path.join(RESULT_DIR, uid)
    os.makedirs(output_path, exist_ok=True)

    save_metadata(output_path, uid, voice, text, candidates,
                  preset, deterministic_seed, cvvp_amount)

    if isinstance(gen, list):
        for j, g in enumerate(gen):
            torchaudio.save(os.path.join(output_path, f'{voice}_{j}.wav'), g.squeeze(0).cpu(), 24000)
    else:
        torchaudio.save(os.path.join(output_path, f'{voice}.wav'), gen.squeeze(0).cpu(), 24000)


def save_metadata(output_path, uid, voice, text,
                  candidates, preset, deterministic_seed, cvvp_amount):
    metadata = {
        'seed': deterministic_seed.numpy().tolist(),
        'uid': uid,
        'voice': voice,
        'text': text,
        'candidates': candidates,
        'preset': preset,
        'cvvp_amount': cvvp_amount,
    }

    with open(os.path.join(output_path, 'metadata.json'), 'w') as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
