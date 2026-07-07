#!/usr/bin/env python3
'''Manipulate records so we remove redundant text'''
try:
  from icecream import ic
except ImportError:
  ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa


def apply(apidat:dict) -> None:
  '''Flatten the API data so it is a bit more compact

  :param apidat: input data, data is modify in place
  '''
  # Define new field name
  def _newfld(k:str, v:str|None, idx:dict[str,int], keys:list[str], cols:list[str]) -> None:
    idx[k] = len(keys)
    keys.append(k)
    cols.append(v)

  ic(apidat.keys())
  # Convert...
  keys = list()
  idx = dict()
  cols = list()
  for k,v in apidat['columns'].items():
    _newfld(k,v,idx,keys,cols)
  _newfld('_apiGrp',None,idx,keys,cols)

  frecs = list()
  for grp in apidat['records']:
    for rec in apidat['records'][grp]:
      flat = [None]*len(keys)
      for k,v in rec.items():
        if not k in idx:
          _newfld(k,None,idx,keys,cols)
          flat.append(None)
          # Retroactively define fields...
          for i in range(len(frecs)): frecs[i].append(None)
        flat[idx[k]] = v
      frecs.append(flat)

  apidat['columns'] = cols
  apidat['keys'] = keys
  apidat['records'] = frecs
  # ~ ic(apidat['count'],len(frecs))



if __name__ == '__main__':
  main()
