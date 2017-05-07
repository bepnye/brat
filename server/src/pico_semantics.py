from __future__ import print_function
import os
from glob import glob
from collections import defaultdict

import sys, random

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

TOP = '/home/ubuntu/pico/'
TASKS = ['participants', 'interventions', 'outcomes']

def parse_ann(fname, txt):
  with open(fname) as fp:
    lines = [l.strip() for l in fp.readlines()]
    char_map = defaultdict(bool)
    for l in lines:
      l = l.split()
      n, label, start, stop, span = l[0], l[1], l[2], l[3], ' '.join(l[4:])
      try:
        start = int(start)
        stop = int(stop)
        try:
          assert span == txt[start:stop]
        except AssertionError:
          print(fname, 'txt: %s... != %s...' %(span[:10], txt[start:stop][:10]))
          raise ValueError
        for i in range(start, stop+1):
          char_map[i] = True
      except ValueError:
        pass
    return char_map

def include_char(c, char_maps):
  return sum([m[c] for m in char_maps])/float(len(char_maps)) >= 0.3

def get_gold_ann(pmid, e):
  with open('%s/resources/txt/%d.txt' %(TOP, pmid)) as txt_fp:
    txt = txt_fp.read()

    input_anns = glob('%s/resources/ann/%s/%d.*.ann' %(TOP, e, pmid))
    char_maps = [parse_ann(ann, txt) for ann in input_anns]
    N = float(len(char_maps))
    spans = []
    MODE = 'idle'
    SPAN_i = 0
    for c in range(len(txt)+1):
      if include_char(c, char_maps):
        if MODE == 'idle':
          SPAN_i = c
          MODE = 'extend'
        elif MODE == 'extend':
          pass
      else: # if c_scores[i] < 0.5
        if MODE == 'extend':
          spans.append((SPAN_i, c-1))
          MODE = 'idle'
        elif MODE == 'idle':
          pass
  lines = ['T%d\tUnknown %d %d\t%s' \
      %(i+1, start, stop, txt[start:stop]) for i,(start,stop) in enumerate(spans)]
  return '\n'.join(lines)

def write_gold_ann(pmid, e):
  with open('%s/resources/ann/%s/%d.ann' %(TOP, e, pmid), 'w') as fp_out:
    fp_out.write(get_gold_ann(pmid, e))
  
def init_ann(doc_path, user):
  bid = os.path.split(doc_path.strip('/'))[1]
  eprint(doc_path + ' | ' + bid)
  user_ann = '%s/%s.%s.ann' %(doc_path, bid, user)
  if os.path.isfile(user_ann):
    eprint('Found existing ann for %s in %s (%s)' %(user, doc_path, user_ann))
  else:
    pmid = open('%s/pmid.info' %(doc_path)).read().strip()
    ann_file = '%s/resources/ann/participants/%s.ann' %(TOP, pmid)
    eprint('Creating new ann for %s in %s' %(user, doc_path))
    os.system('cp %s %s' %(ann_file, user_ann))

def init_doc(DOC_TOP, pmid, bid):
  eprint('Creating files for pmid %s (%s) in %s' %(pmid, bid, DOC_TOP))
  os.system('mkdir -p %s' %DOC_TOP)

  txt_file = '%s/resources/txt/%s.txt' %(TOP, pmid)
  os.system('cp %s %s/%s.txt' %(txt_file, DOC_TOP, bid))

  vis_file = '%s/resources/confs/visual.conf' %(TOP)
  os.system('cp %s %s' %(vis_file, DOC_TOP))

  os.system('echo %s >> %s/pmid.info' %(pmid, DOC_TOP))

  conf_out = '%s/annotation.conf' %(DOC_TOP)
  if not os.path.exists(conf_out):
    conf_file = '%s/resources/confs/%s.conf' %(TOP, 'participants')
    mesh_file = '%s/resources/mesh/%s.txt' %(TOP, pmid)
    os.system('cp %s %s' %(conf_file, conf_out))
    with open(mesh_file) as mesh_fp:
      with open(conf_out, 'a') as conf_fp:
        for m in mesh_fp.readlines():
          if m.strip() not in ['Male', 'Female', 'Humans', \
                'Infant', 'Child, Preschool', 'Child', 'Adolescent', 'Young Adult', \
                'Adult', 'Middle Aged', 'Aged', 'Aged, 80 and over']:
            conf_fp.write('%s Arg:<ENTITY>\n' %(m.strip().replace(' ', '_').replace(',', '')))

  init_ann(DOC_TOP, 'shared')

def read_pmid_hits():
  return [l.strip().split(',') for l in open('%s/resources/pmid_hits.txt' %TOP, 'r').readlines()]

def write_corefs(guid, coll, doc, corefs):
  eprint('Writing corefs for %s, %s' %(guid, doc))
  fout = '%s/%s.%s.coref' %(coll, doc, guid)
  fout = fout.replace('/pico', '/home/ubuntu/pico/brat_data')
  coref_txt = corefs.replace(',', '\n')
  with open(fout, 'w') as fp:
    fp.write(coref_txt)
  return {'output':corefs}

def get_next_doc(coll):
  eprint('Getting doc for %s', coll)
  return {'docName':'dummy'}

def init_all_collections(n = None):
  pmid_hits = read_pmid_hits()
  for h in pmid_hits[:n]:
    hit_name = '_'.join(h)
    HIT_TOP = '%s/brat_data/HITs/%s' %(TOP, hit_name)
    for pmid in h:
      DOC_TOP = '%s/%s/' %(HIT_TOP, pmid)
      init_doc(DOC_TOP, pmid, pmid)

def init_seq_collection(n = None):
  pmids = [l.strip() for l in open('%s/resources/pmids.txt' %TOP, 'r').readlines()]
  pmids = pmids[:n]
  SEQ_TOP = '%s/brat_data/seq/%d/' %(TOP, len(pmids))
  for i,pmid in enumerate(pmids):
    DOC_TOP = '%s/%d/' %(SEQ_TOP, i)
    init_doc(DOC_TOP, pmid, str(i))
