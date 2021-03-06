from __future__ import print_function
import os
from glob import glob
from collections import defaultdict

import sys, random

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

CURRENT_TASK = 'outcomes'

TOP = '/home/ubuntu/pico/'
LINK = 'http://ec2-34-230-42-186.compute-1.amazonaws.com:8001/index_01.xhtml#/pico/PICO'

NEXT_PMID_MAP = {}
PREV_PMID_MAP = {}
PMIDS = [l.strip() for l in open('%s/resources/pmids.txt' %TOP).readlines()]
HIT_SIZE = 3
PMID_HITS = [PMIDS[i:i+HIT_SIZE] for i in range(0, len(PMIDS), HIT_SIZE)]
for pmids in PMID_HITS:
  for i in range(len(pmids)):
    NEXT_PMID_MAP[pmids[i]] = pmids[min(i+1, len(pmids)-1)]
    PREV_PMID_MAP[pmids[i]] = pmids[max(i-1, 0)]

def shuffled(l):
  return random.sample(l, len(l))

def get_base_ann_fname(pmid, task):
  ann_dir_name = { 'interventions': 'Treatment',
                   'participants': 'Participants',
                   'outcomes': 'Outcomes', }[task]
  return '%s/resources/ann/%s/%s.ann' %(TOP, ann_dir_name, pmid)

def init_ann(doc_path, user, task = CURRENT_TASK):
  path, bid = os.path.split(doc_path)
  eprint(doc_path + ' | ' + bid)
  user_ann = '%s/%s.%s.ann' %(path, bid, user)
  if os.path.isfile(user_ann):
    eprint('Found existing ann for %s in %s (%s)' %(user, doc_path, user_ann))
  else:
    pmid_file = '%s/pmid.info' %(path)
    if os.path.isfile(pmid_file):
      pmid = open(pmid_file).read().strip()
    else:
      pmid = bid
    ann_file = get_base_ann_fname(pmid, task)
    eprint('Ann file = ' + ann_file)
    #eprint('Creating new ann for %s in %s' %(user, doc_path))
    os.system('cp %s %s' %(ann_file, user_ann))

def init_doc(DOC_TOP, pmid, bid, task = CURRENT_TASK):
  #eprint('Creating files for pmid %s (%s) in %s' %(pmid, bid, DOC_TOP))
  os.system('mkdir -p %s' %DOC_TOP)

  txt_file = '%s/resources/txt/%s.txt' %(TOP, pmid)
  os.system('cp %s %s/%s.txt' %(txt_file, DOC_TOP, bid))

  vis_file = '%s/resources/confs/visual.conf' %(TOP)
  os.system('cp %s %s' %(vis_file, DOC_TOP))

  os.system('rm -f %s/pmid.info' %(DOC_TOP))
  os.system('echo %s >> %s/pmid.info' %(pmid, DOC_TOP))

  conf_out = '%s/annotation.conf' %(DOC_TOP)
  if not os.path.exists(conf_out):
    conf_file = '%s/resources/confs/%s.conf' %(TOP, task)
    eprint(conf_file)
    mesh_file = '%s/resources/mesh/%s.txt' %(TOP, pmid)
    os.system('cp %s %s' %(conf_file, conf_out))
    with open(mesh_file) as mesh_fp:
      with open(conf_out, 'a') as conf_fp:
        for m in shuffled(mesh_fp.readlines()):
          if m.strip() not in ['Male', 'Female', 'Humans', \
                'Infant', 'Child, Preschool', 'Child', 'Adolescent', 'Young Adult', \
                'Adult', 'Middle Aged', 'Aged', 'Aged, 80 and over']:
            conf_fp.write('%s Arg:MeSH\n' %(m.strip().replace(' ', '_').replace(',', '')))

  init_ann(DOC_TOP, 'shared', task)

def read_pmid_hits():
  return [l.strip().split(',') for l in open('%s/resources/pmid_hits.txt' %TOP, 'r').readlines()]

def write_user_file(guid, coll, doc, string, suffix):
  eprint('Writing %s file for %s, %s' %(suffix, guid, doc))
  fout = '%s/%s.%s.%s' %(coll, doc, guid, suffix)
  fout = fout.replace('/pico', TOP+'/brat_data')
  txt = string.replace(',', '\n')
  with open(fout, 'w') as fp:
    fp.write(txt)
  return {'output':string}

def write_corefs(guid, coll, doc, corefs):
  return write_user_file(guid, coll, doc, corefs, 'corefs')

def write_mesh(guid, coll, doc, mesh):
  return write_user_file(guid, coll, doc, mesh, 'mesh')

def get_next_doc(doc, direction):
  if direction == '1':
    new_doc = NEXT_PMID_MAP[doc]
  elif direction == '-1':
    new_doc = PREV_PMID_MAP[doc]
  else:
    new_doc = doc
  eprint('Found next doc for %s = %s' %(doc, new_doc))
  return {'docName': new_doc}

def init_all_collections(i = 0, n = None):
  pmid_hits = read_pmid_hits()
  os.system('mkdir -p %s/brat_data/HITs/' %(TOP))
  links_fname = '%s/brat_data/HITs/links.txt' %(TOP)
  with open(links_fname, 'w') as links_fout:
    if i:
      pmid_hits = pmid_hits[i:]
    for h in pmid_hits[:n]:
      hit_name = '_'.join(h)
      links_fout.write('%s/BATCH/HITs/%s/%s/%s\n' %(LINK, hit_name, h[0], h[0]))
      HIT_TOP = '%s/brat_data/HITs/%s' %(TOP, hit_name)
      for pmid in h:
        DOC_TOP = '%s/%s/' %(HIT_TOP, pmid)
        init_doc(DOC_TOP, pmid, pmid)

def init_all_docs(n_i = 0, n = 10, task = CURRENT_TASK, fname = None):
  fname = fname or '%s/resources/pmids.txt' %TOP
  pmids = [int(l.strip()) for l in open(fname, 'r').readlines()][n_i:n_i+n]
  DOCS_TOP = '%s/brat_data/PICO/%s/' %(TOP, task)
  for pmid in pmids:
    DOC_TOP = '%s/%d/' %(DOCS_TOP, pmid)
    init_doc(DOC_TOP, pmid, pmid, task)
  links_fname = '%s/links.txt' %(DOCS_TOP)
  with open(links_fname, 'w') as links_fout:
    i_hit = n_i / HIT_SIZE
    n_hit = len(pmids) / HIT_SIZE
    for h in PMID_HITS[i_hit:i_hit+n_hit]:
      if len(h) == HIT_SIZE:
        hit_name = h[0]
        links_fout.write('%s/%s/%s/%s\n' %(LINK, task, hit_name, h[0]))

def init_seq_collection(n = None, task = CURRENT_TASK, fname = None):
  fname = fname or '%s/resources/pmids.txt' %TOP
  pmids = [l.strip() for l in open(fname, 'r').readlines()]
  pmids = pmids[:n]
  SEQ_TOP = '%s/brat_data/seq/%d/' %(TOP, len(pmids))
  for i,pmid in enumerate(pmids):
    DOC_TOP = '%s/%d/' %(SEQ_TOP, i)
    init_doc(DOC_TOP, pmid, str(i), task)
