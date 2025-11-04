#!/usr/bin/env python3
"""
MP-SENet Speech Enhancement - Direct Implementation
Uses the original MP-SENet code structure
"""

import os
import sys
import argparse
import json
import glob
import torch
import librosa
import soundfile as sf

# Configuration for the model
DEFAULT_CONFIG = {
    'sampling_rate': 16000,
    'n_fft': 400,
    'hop_size': 100,
    'win_size': 400,
    'compress_factor': 0.3,
    'dense_channel': 64,
    'num_tsconformers': 4,
    'beta': 2.0,
    'seed': 1234
}


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def mag_pha_stft(y, n_fft, hop_size, win_size, compress_factor=1.0, center=True):
    """Extract magnitude and phase from STFT"""
    hann_window = torch.hann_window(win_size).to(y.device)
    stft_spec = torch.stft(y, n_fft, hop_length=hop_size, win_length=win_size, 
                           window=hann_window, center=center, pad_mode='reflect', 
                           normalized=False, return_complex=True)
    stft_spec = torch.view_as_real(stft_spec)
    mag = torch.sqrt(stft_spec.pow(2).sum(-1) + (1e-9))
    pha = torch.atan2(stft_spec[:, :, :, 1] + (1e-10), stft_spec[:, :, :, 0] + (1e-5))
    
    # Magnitude Compression
    mag = torch.pow(mag, compress_factor)
    com = torch.stack((mag * torch.cos(pha), mag * torch.sin(pha)), dim=-1)
    
    return mag, pha, com


def mag_pha_istft(mag, pha, n_fft, hop_size, win_size, compress_factor=1.0, center=True):
    """Reconstruct audio from magnitude and phase"""
    # Magnitude Decompression
    mag = torch.pow(mag, (1.0 / compress_factor))
    com = torch.complex(mag * torch.cos(pha), mag * torch.sin(pha))
    hann_window = torch.hann_window(win_size).to(com.device)
    wav = torch.istft(com, n_fft, hop_length=hop_size, win_length=win_size, 
                     window=hann_window, center=center)
    
    return wav


def load_checkpoint(filepath, device):
    """Load model checkpoint"""
    if not os.path.isfile(filepath):
        print(f"Error: Checkpoint file not found: {filepath}")
        sys.exit(1)
    
    print(f"Loading checkpoint: {filepath}")
    checkpoint_dict = torch.load(filepath, map_location=device)
    print("Checkpoint loaded successfully!")
    return checkpoint_dict


def enhance_audio(checkpoint_file, input_file, output_file, device='cpu', config_file=None):
    """
    Enhance a single audio file using MP-SENet
    
    Args:
        checkpoint_file: Path to model checkpoint
        input_file: Path to noisy input audio
        output_file: Path to save enhanced audio
        device: 'cuda' or 'cpu'
        config_file: Optional path to config.json
    """
    # Load configuration
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            data = f.read()
        json_config = json.loads(data)
        h = AttrDict(json_config)
    else:
        print("Using default configuration...")
        h = AttrDict(DEFAULT_CONFIG)
    
    # Set device
    device = torch.device(device if torch.cuda.is_available() and device == 'cuda' else 'cpu')
    print(f"Using device: {device}")
    
    # Import and load model
    try:
        from models.model import MPNet
    except ImportError:
        print("\nError: Cannot import MPNet model.")
        print("Please make sure you have the MP-SENet repository files.")
        print("\nTo fix this:")
        print("1. Clone the repository: git clone https://github.com/yxlu-0102/MP-SENet.git")
        print("2. Run this script from the MP-SENet directory, OR")
        print("3. Add the MP-SENet directory to your Python path")
        sys.exit(1)
    
    print("\nLoading MP-SENet model...")
    model = MPNet(h).to(device)
    state_dict = load_checkpoint(checkpoint_file, device)
    model.load_state_dict(state_dict['generator'])
    model.eval()
    
    # Load and preprocess audio
    print(f"\nProcessing: {input_file}")
    print("-" * 60)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    noisy_wav, sr = librosa.load(input_file, sr=h.sampling_rate)
    print(f"Loaded audio: {len(noisy_wav)/sr:.2f} seconds @ {sr} Hz")
    
    # Convert to tensor and normalize
    noisy_wav = torch.FloatTensor(noisy_wav).to(device)
    norm_factor = torch.sqrt(len(noisy_wav) / torch.sum(noisy_wav ** 2.0)).to(device)
    noisy_wav = (noisy_wav * norm_factor).unsqueeze(0)
    
    # Perform speech enhancement
    print("Enhancing audio...")
    with torch.no_grad():
        noisy_amp, noisy_pha, noisy_com = mag_pha_stft(
            noisy_wav, h.n_fft, h.hop_size, h.win_size, h.compress_factor
        )
        amp_g, pha_g, com_g = model(noisy_amp, noisy_pha)
        audio_g = mag_pha_istft(
            amp_g, pha_g, h.n_fft, h.hop_size, h.win_size, h.compress_factor
        )
        audio_g = audio_g / norm_factor
    
    # Save enhanced audio
    output_audio = audio_g.squeeze().cpu().numpy()
    sf.write(output_file, output_audio, h.sampling_rate, 'PCM_16')
    
    print("-" * 60)
    print(f"✓ Enhanced audio saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='MP-SENet Speech Enhancement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using pretrained checkpoint from repository
  python enhance.py --checkpoint best_ckpt/g_best_vb --input noisy.wav --output clean.wav
  
  # Specify config file
  python enhance.py --checkpoint best_ckpt/g_best_vb --config config.json --input noisy.wav --output clean.wav
  
  # Use GPU
  python enhance.py --checkpoint best_ckpt/g_best_vb --input noisy.wav --output clean.wav --device cuda

Setup Instructions:
  1. Clone MP-SENet repository: git clone https://github.com/yxlu-0102/MP-SENet.git
  2. Install requirements: pip install torch librosa soundfile scipy einops
  3. Run this script from the MP-SENet directory, or copy it there
        """
    )
    
    parser.add_argument(
        '--checkpoint',
        required=True,
        help='Path to model checkpoint (e.g., best_ckpt/g_best_vb)'
    )
    parser.add_argument(
        '--config',
        default=None,
        help='Path to config.json (optional, will use defaults if not provided)'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input noisy audio file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output enhanced audio file'
    )
    parser.add_argument(
        '--device',
        default='cpu',
        choices=['cuda', 'cpu'],
        help='Device to use for inference (default: cpu)'
    )
    
    args = parser.parse_args()
    
    # Try to find config.json in checkpoint directory if not specified
    if args.config is None:
        checkpoint_dir = os.path.dirname(args.checkpoint)
        possible_config = os.path.join(checkpoint_dir, 'config.json')
        if os.path.exists(possible_config):
            args.config = possible_config
            print(f"Found config file: {args.config}")
    
    enhance_audio(args.checkpoint, args.input, args.output, args.device, args.config)


if __name__ == '__main__':
    main()

'''
# Using VoiceBank+DEMAND model

python enhance.py --model g_best_vb --input "/Users/calvin_kristianto/Music/10 Hours Dataset/indo/Press Con PJ 23 Apr 2025.mp3" --output "/Users/calvin_kristianto/Music/10 Hours Dataset/indo/enhanced_audio.wav"
'''