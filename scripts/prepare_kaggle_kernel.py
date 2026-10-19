"""Prepare a private, self-contained Kaggle notebook. Never uploads or trains locally."""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from package_neural_job import FILES


def prepare(root, output):
    payload = {
        name: base64.b64encode((root / name).read_bytes()).decode("ascii")
        for name in FILES
    }
    hashes = {
        name: hashlib.sha256(base64.b64decode(value)).hexdigest()
        for name, value in payload.items()
    }
    source = '''# Private ResearchProof compute job; no credentials or dataset rows embedded.
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PAYLOAD = __PAYLOAD__
HASHES = __HASHES__

def main():
    if not Path('/kaggle/working').is_dir():
        raise RuntimeError('This job must run on Kaggle, not a local laptop.')
    # Some runtime images omit this optional utility; torch checks CUDA below.
    if shutil.which('nvidia-smi'):
        subprocess.run(['nvidia-smi'], check=True)
    print('GPU device nodes:', list(Path('/dev').glob('nvidia*')), flush=True)
    if not list(Path('/dev').glob('nvidia*')):
        raise RuntimeError('Kaggle did not expose an NVIDIA GPU. Check accelerator availability in notebook settings.')
    root = Path('/kaggle/working/researchproof')
    root.mkdir(exist_ok=False)
    for name, encoded in PAYLOAD.items():
        raw = base64.b64decode(encoded)
        if hashlib.sha256(raw).hexdigest() != HASHES[name]:
            raise ValueError('Source integrity failure: ' + name)
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (root / 'source_hashes.json').write_text(json.dumps(HASHES, indent=2))
    # Keep dependency/model caches out of saved research outputs.
    runtime = Path('/tmp/researchproof_runtime')
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(runtime)], check=True)
    python = str(runtime / 'bin/python')
    env = dict(os.environ, PYTHONPATH=str(root / 'src'),
               HF_HOME='/tmp/researchproof_hf', PYTHONUNBUFFERED='1')
    def run(args):
        subprocess.run([python] + args, cwd=root, env=env, check=True)
    subprocess.run([sys.executable, '-m', 'pip', '--python', python,
                    'install', '--no-cache-dir', 'pip', '-r', 'requirements-neural.txt'],
                   cwd=root, env=env, check=True)
    run(['-c', 'import torch; assert torch.cuda.is_available(), "CUDA required"; print(torch.cuda.get_device_name(0))'])
    freeze = subprocess.check_output([python, '-m', 'pip', 'freeze'], text=True)
    (root / 'environment.txt').write_text(freeze)
    run(['scripts/fetch_peerj_materials.py'])
    run(['-m', 'pytest', 'neural_tests', '-q'])
    run(['scripts/train_codebert.py', '--smoke', '--device', 'cuda',
         '--output', 'artifacts/gpu_session_smoke'])
    run(['scripts/run_codebert_seeds.py', '--device', 'cuda', '--micro-batch', '2',
         '--output', 'artifacts/full_codebert'])
    for seed in (0, 1, 2):
        run(['scripts/summarize_codebert.py', f'artifacts/full_codebert/seed{seed}',
             '--output', f'artifacts/seed{seed}_summary.json'])
    print('Three seeds completed; scientific analysis and human review remain required.')

if __name__ == '__main__':
    main()
'''.replace('__PAYLOAD__', repr(payload)).replace('__HASHES__', repr(hashes))
    compile(source, 'job.py', 'exec')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'job.py').write_text(source)
    notebook = {
        'nbformat': 4, 'nbformat_minor': 5,
        'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}},
        'cells': [{'cell_type': 'code', 'id': 'researchproof-training', 'metadata': {},
                   'execution_count': None, 'outputs': [], 'source': source}],
    }
    (output / 'job.ipynb').write_text(json.dumps(notebook))
    metadata = {
        'id': 'bibekthakur1/researchproof-codebert-20261020',
        'title': 'ResearchProof CodeBERT 20261020',
        'code_file': 'job.ipynb', 'language': 'python', 'kernel_type': 'notebook',
        'is_private': True, 'enable_gpu': True, 'enable_tpu': False,
        'enable_internet': True,
        'machine_shape': 'NvidiaTeslaT4',
        'dataset_sources': [], 'competition_sources': [], 'kernel_sources': [],
    }
    (output / 'kernel-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return hashes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    hashes = prepare(Path(__file__).resolve().parents[1], args.output)
    print(f'Prepared {len(hashes)} allowlisted files in {args.output}; nothing uploaded.')
