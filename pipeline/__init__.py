'''
# Pricing data pipeline

Fetches cloud pricing data from the T‑Cloud pricing API, merges
supplementary data from CSV/JSON files, applies fix‑up patches,
and normalises records for consumption by other tools such as
CatBrowser UI and Excel generator.
'''
import os
import subprocess
import sys

def _git_describe(default:str) -> str:
  # ~ version = os.getenv('GITHUB_REF_NAME')
  # ~ if version: return version

  script_dir = os.path.dirname(os.path.abspath(__file__))
  rc = subprocess.run(['git','describe','--always'],
                      capture_output = True,
                      text = True,
                      cwd = script_dir
                    )
  if rc.returncode != 0:
    sys.stderr.write(f'git describe: {rc.stderr}\n')
    return default
  return rc.stdout.strip()

__version__ = _git_describe('0.1.0-dev')

