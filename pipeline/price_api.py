#!/usr/bin/env python3
'''Fetch Price data via API

Based on: https://docs.otc.t-systems.com/price-calculator/api-ref/
'''

try:
  from icecream import ic
except ImportError:  # Graceful fallback if IceCream isn't installed.
  ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa

import datetime
import json
import requests
import sys

VERBOSE = False
DE_API_ENDPOINT = 'https://calculator.otc-service.com/de/open-telekom-price-api/'
EN_API_ENDPOINT = 'https://calculator.otc-service.com/en/open-telekom-price-api/'

def _fetch(url:str, **params) -> dict:
  '''Fetch API results

  :param url: URL for API end-point format
  :param params: kwargs to be passed as HTTP query
  :returns: A dict containing the parsed JSON response
  '''
  res = requests.get(url,
                      params = params)
  res.raise_for_status()

  js = json.loads(res.text)
  if js['response']['httpCode'] != 200:
    raise requests.exceptions.HTTPError(f'JSON HTTP Error, httpCode: {js["response"]["httpCode"]}')
  return js['response']


def fetch_prices(url:str, res:dict|None = None, **params) -> dict:
  '''Fetch API results

  Handles pagination and initial data normalization

  The results is a dict with the following elements:

  - `columns` : Column names and their decriptions
  - `services` : Service names and their descriptions
  - `count` : number of records found
  - `records` : A dict containing price records.  Each key of the
     dict is the service key (from the `services` dict.).  Each
     value in the dict is a list of records.

  :param url: URL for API end-point format
  :param params: kwargs to be passed as HTTP query
  :returns: A dict containing results.
  '''
  if res is None: res = dict()

  res['params'] = params

  if VERBOSE: sys.stderr.write('Querying API..')
  r = _fetch(url, limitMax=1, **params)
  if VERBOSE: sys.stderr.write(f'..OK\nRecord count: {r["stats"]["count"]}\n')

  res['columns'] = r['columns']
  if r['services']['records']: res['services'] = r['services']['records']
  res['count'] = r['stats']['count']
  res['records'] = {}

  limit_max = 499
  offset = 0
  while True:
    if VERBOSE: sys.stderr.write(f'Query offset {offset}..')
    r = _fetch(url, limitMax=limit_max,limitFrom=offset, **params)
    if VERBOSE: sys.stderr.write('Ok\n')

    if len(r['result']) == 0: break
    for k,v in r['result'].items():
      if k in res['records']:
        res['records'][k].extend(v)
      else:
        res['records'][k] = v
    if r['stats']['currentPage'] > r['stats']['maxPages']: break
    offset += limit_max
    # if offset > 2000: break # TODO: TESTING

  return res

