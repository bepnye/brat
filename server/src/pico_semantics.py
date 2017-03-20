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
  
def init_doc(pmid, HIT_TOP):
  eprint('Creating files for hit = %s' %(str(pmid)))

  DOC_TOP = '%s/%s/' %(HIT_TOP, pmid)
  os.system('mkdir -p %s' %DOC_TOP)

  txt_file = '%s/resources/txt/%s.txt' %(TOP, pmid)
  os.system('cp %s %s' %(txt_file, DOC_TOP))

  vis_file = '%s/resources/confs/visual.conf' %(TOP)
  os.system('cp %s %s' %(vis_file, DOC_TOP))

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
            conf_fp.write('%s Arg:<ENTITY>\n' %(m.strip().replace(' ', '_')))

def read_pmid_hits():
  return [l.strip().split(',') for l in open('%s/resources/pmids.txt' %TOP, 'r').readlines()]

def init_collection(guid = None, pmid = None, pmid_hits = None):
  pmid_hits = pmid_hits or read_pmid_hits()
  if not pmid:
    random.seed()
    pmid_hit = random.choice(pmid_hits)
  else:
    eprint('initializing files for pmid = %s' %pmid)
    matching_hits = [hit for hit in pmid_hits if pmid in hit]
    eprint('found %d matching hits' %(len(matching_hits)))
    pmid_hit = matching_hits[0]

  coll_name = '_'.join(pmid_hit)
  HIT_TOP = '%s/brat_data/%s/' %(TOP, coll_name)

  if not os.path.exists(HIT_TOP):
    os.system('mkdir -p %s' %HIT_TOP)
    for pmid in pmid_hit:
      init_doc(pmid, HIT_TOP)

  if guid: # If we already have a target user, go ahead and add the .ann files
    for pmid in pmid_hit:
      DOC_TOP = '%s/%s/' %(HIT_TOP, pmid)
      ann_src = '%s/resources/ann/participants_hmm/%s.ann' %(TOP, pmid)
      ann_user = '%s/%s.%s.ann' %(DOC_TOP, pmid, guid)
      if not os.path.exists(ann_user):
        os.system('cp %s %s' %(ann_src, ann_user))

  return {'coll':coll_name, 'doc':pmid_hit[0]}

def write_corefs(guid, coll, doc, corefs):
  eprint('Writing corefs for %s, %s' %(guid, doc))
  fout = '%s/%s.%s.coref' %(coll, doc, guid)
  fout = fout.replace('/pico', '/home/ubuntu/pico/brat_data')
  coref_txt = corefs.replace(',', '\n')
  with open(fout, 'w') as fp:
    fp.write(coref_txt)
  return {'output':corefs}

def init_all_collections(n = None):
  pmid_hits = read_pmid_hits()
  for h in pmid_hits[:n]:
    init_collection(guid = None, pmid = h[0], pmid_hits = pmid_hits)
