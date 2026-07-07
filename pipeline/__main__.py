#!/usr/bin/env python3
'''CLI entry point for the pricing pipeline.'''
try:
  from icecream import ic
except ImportError:
  ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa

import argparse
import datetime
import hashlib
import json
import os
import sys

from . import __version__
from . import price_api as api
from . import transform

SCHEMA = 'pipeline-pricing-1.0'

def parser_factory(color:bool = False) -> argparse.ArgumentParser:
  color = { 'color': color } if sys.version_info >= (3,14) else dict()
  cli = argparse.ArgumentParser(
    prog='pricing',
    description='T-Cloud pricing data pipeline',
    **color)
  cli.add_argument('--version','-V',
          action='version', version=f'%(prog)s {__version__}'
  )
  cli.add_argument('-v','--verbose',
                    action='store_true',
                    default=True,
                )
  cli.add_argument('-q','--quiet',
                    action='store_false',
                    dest='verbose',
                )

  cli.add_argument('--url',
                    help='Specify the API URL format',
                    default = api.EN_API_ENDPOINT,
                    type=str,
                )
  cli.add_argument('--load',
                    help='Load prices from a file',
                    type=str,
                    metavar = 'FILE',
                    dest='url',
                )
  cli.add_argument('--en',
                    help='Use the English end-point',
                    action = 'store_const',
                    const = api.EN_API_ENDPOINT,
                    dest = 'url',
                )
  cli.add_argument('--de',
                    help='Use the German end-point',
                    action = 'store_const',
                    const = api.DE_API_ENDPOINT,
                    dest = 'url',
                )
  cli.add_argument('--save',
                help = 'Save raw output',
                type = str,
                default = None,
              )
  cli.add_argument('--cksum',
                help = 'Calculate and save a checksum',
                type = str,
                default = None,
              )

  cli.add_argument('-o','--output',
                    help = 'Save output',
                    type = str,
                    default = None,
                    dest = 'output',
                  )

  cli.add_argument('params',
                    help='API query params',
                    nargs='*',
                )
  return cli

def main(argv=None):
  cli = parser_factory()
  args = cli.parse_args(argv)
  ic(args)

  params = dict()
  for i in args.params:
    if os.path.isfile(i):
      if i not in inclst: inclst.append(i)
    elif '=' in i:
      k,v = i.split('=',1)
      if ',' in v:
        params[f'{k}[]'] = [ i.strip() for i in v.split(',') ]
      else:
        params[k] = v
    else:
      params[i] = i

  if os.path.isfile(args.url):
    # Read things from a file
    with open(args.url) as fp:
      apidat = json.load(fp)
      if args.verbose:
        sys.stderr.write(f'Bytes read from {args.url}: {fp.tell():,}\n')
  else:
    api.VERBOSE = args.verbose
    apidat = {
      'schema': SCHEMA,
    }
    apidat = api.fetch_prices(args.url, apidat, **params)
    if args.save is not None:
      with open(args.save,'w') as fp:
        fp.write(json.dumps(apidat, indent=1))
        if args.verbose:
          sys.stderr.write(f'Bytes written to {args.save}: {fp.tell():,}\n')

  transform.apply(apidat)

  if args.cksum:
    hasher = hashlib.md5()
    hasher.update(json.dumps(apidat).encode())
    # OK, add the metadata (we do this after calculating checksum's)
    apidat['timestamp'] = datetime.datetime.now().timestamp()
    apidat['datetime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    apidat['cksum'] = hasher.hexdigest()
    apidat['generatedBy'] = f'pipeline v{__version__}'

    with open(args.cksum,'w') as fp:
      fp.write(f'{apidat["cksum"]} {apidat["datetime"]} {apidat["timestamp"]} {apidat['generatedBy']}\n')
    if args.verbose:
        sys.stderr.write(f'Checksum {apidat["cksum"]}\n')

  if args.output is None:
    if args.save is None: print(json.dumps(apidat, indent=1))
  else:
    with open(args.output,'w') as fp:
      fp.write(json.dumps(apidat, indent=1))
      if args.verbose:
        sys.stderr.write(f'Bytes written to {args.output}: {fp.tell():,}\n')

  # ~ with open(args.fixed_output,'w') as fp:
    # ~ fp.write(json.dumps(apidat, indent=1))
  # ~ ck = cksum.calc(apidat,'timestamp')
  # ~ print(ck, apidat['timestamp'])

if __name__ == '__main__':
  main()
