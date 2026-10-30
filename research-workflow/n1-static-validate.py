"""N1設計・meta・人工testの静的交付点検。科学値を生成しない。"""
import ast,csv,hashlib,json,re,datetime,subprocess,argparse
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--local-readme-sha');args=parser.parse_args()
root=Path.cwd();p=root/'docs/P1-N1'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def rows(n):return list(csv.DictReader((p/n).open()))
protected=json.loads((p/'evidence-input-sha256.json').read_text());assert all(sha(root/k)==h for k,h in protected.items())
if args.local_readme_sha:assert sha(root/'README.md')==args.local_readme_sha
b=rows('branch-index.csv');h=rows('history-index.csv');md=rows('MD-file-audit.csv');future=rows('future-experiment-matrix.csv')
assert len(b)==240 and len(h)==32 and len(md)==272 and len(future)==64 and len(rows('state-index.csv'))==16
assert len({r['root_id'] for r in b})==8 and len({r['state_id'] for r in b})==16
for sid in {r['state_id'] for r in b}:
 for arm,num in [('F0',3),('F1',6),('F2',6)]:assert sum(r['state_id']==sid and r['arm']==arm for r in b)==num
assert {r['md_task_id'] for r in b}|{r['task_id'] for r in h}=={r['task_id'] for r in md}
assert all(r['evaluation_status']=='NOT_EXECUTED' and r['analysis_role']=='POST_HOC_EXPLORATORY' for r in b)
assert all(r['status']=='PROPOSED_NOT_EXECUTED' for r in future)
a=json.loads((p/'metadata-audit.json').read_text());assert a['MD_files']==272 and a['model_byte_SHA_checked']==80 and a['embedding_files_SHA_checked']==96 and a['DCD_coordinate_frames_decoded']==0 and a['model_loads']==0
for name in ['n1_native_metrics.py','n1_metadata_audit.py']:
 f=root/'p1'/name;ast.parse(f.read_text());assert sha(f)==json.loads((p/'synthetic-test.json').read_text())['source_SHA256'][name]
test=root/'tests/p1/test_n1_native_metrics.py';ast.parse(test.read_text());t=json.loads((p/'synthetic-test.json').read_text());assert t['status']=='PASS' and t['tests']==22 and sha(test)==t['source_SHA256'][test.name]
trans=json.loads((p/'server-transfer-verification.json').read_text());assert all(sha(p/Path(n).name)==v for n,v in trans['files'].items())
links=0;missing=[]
for f in p.glob('*.md'):
 if f.name.startswith('._'):continue
 for dest in re.findall(r'\]\(([^)]+)\)',f.read_text()):
  dest=dest.split('#')[0]
  if not dest or '://' in dest:continue
  if dest in ['delivery-validation.json','remote-readback.json','output-sha256.json']:continue
  links+=1
  if not (p/dest).exists():missing.append([f.name,dest])
assert not missing,missing
for f in p.iterdir():
 if f.name.startswith('._') or f.suffix not in ['.md','.json','.csv','.log']:continue
 text=f.read_text()
 assert not re.search(r'/home/[^/\s"\']+|192\.168\.\d+\.\d+|github_pat_|ghp_[A-Za-z0-9]{30}|-----BEGIN .*PRIVATE KEY',text),f
 if f.suffix=='.json':json.loads(text)
receipt=dict(status='PASS_STATIC_PREPARATION_ONLY',checked_JST=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),source_main='73b93ed224b45b3f62e99e92447241e9af096d8a',protected_old_files=len(protected),protected_unchanged=True,preexisting_root_README_unchanged=True if args.local_readme_sha else 'NOT_REQUESTED',branches=240,states=16,roots=8,histories=32,MD_byte_SHA_header_records=272,models_byte_SHA_only=80,ranking_byte_SHA_only=96,artificial_tests=22,proposed_future_rows=64,internal_links_checked=links,missing_links=missing,source_deployed_SHA_match=True,compact_transfer_SHA_match=True,native_coordinate_frames_evaluated=0,new_MD_training_inference_LOF=0,method_adoption='PENDING',independent_scientific_review='PENDING',researcher_acceptance='PENDING',GitHub_readback='PENDING_ACTUAL_VERIFICATION')
(p/'delivery-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(p/'output-sha256.json').write_text(json.dumps({f.name:sha(f) for f in p.iterdir() if f.is_file() and not f.name.startswith('._') and f.name not in ['output-sha256.json','remote-readback.json','delivery-validation.json']},ensure_ascii=False,indent=2)+'\n')
print('PASS',len(protected),links,'links, no scientific execution')
