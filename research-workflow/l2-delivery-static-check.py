"""保存済みL2成果の件数・不変性・参照・SHAを静的検証する。科学計算は行わない。"""
from pathlib import Path
import csv,json,hashlib,re,subprocess,datetime,ast,argparse
args=argparse.ArgumentParser();args.add_argument('--workspace-readme-sha');a=args.parse_args()
root=Path.cwd();p=root/'docs/P1-L2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def rows(f):return list(csv.DictReader(f.open()))
protected=json.loads((root/'research-workflow/l2-protected-baseline.json').read_text())
changed=[f for f,h in protected.items() if sha(root/f)!=h]
assert not changed,changed
if a.workspace_readme_sha:assert sha(root/'README.md')==a.workspace_readme_sha
expected={'experiment-matrix.csv':36,'checkpoint-matrix.csv':156,'training-membership.csv':9600,'evaluation-ids.csv':1600,'model-metrics.csv':936,'geometry.csv':624,'latent.csv':936,'paired-contrasts.csv':3960,'representation-stability.csv':1320,'LOF-comparisons.csv':660,'selection-summary.csv':156,'overview.csv':78,'root-effects.csv':96,'loss-curves.csv':288,'decision-cells.csv':144,'optimizer-step-audit.csv':156,'checkpoint-lineage.csv':156,'parent-audit.csv':24,'RNG-pair-audit.csv':48,'step-improvement-summary.csv':18,'update-effects-summary.csv':24,'initialization-summary.csv':26,'LOF-summary.csv':55,'loss-spike-case-r02-s8-i2-M0.csv':1600}
for f,n in expected.items():assert len(rows(p/f))==n,(f,n)
cp=rows(p/'checkpoint-matrix.csv');actual=rows(p/'checkpoint-audit.csv')
# 列名は実ファイルschemaに従って照合する。
print('checkpoint_schema',list(cp[0]),list(actual[0]))
cp_key='checkpoint_id' if 'checkpoint_id' in cp[0] else 'checkpoint'
a_key='checkpoint_id' if 'checkpoint_id' in actual[0] else 'checkpoint'
assert {r[cp_key] for r in cp}=={r[a_key] for r in actual}
assert len({r['checkpoint'] for r in rows(p/'selection-summary.csv')})==156
manifests={}
for name in ['delivery-sha256.json','completion-delivery-sha256.json','output-sha256.json']:
 data=json.loads((p/name).read_text());assert all(sha(p/f)==h for f,h in data.items());manifests[name]=len(data)
late=json.loads((p/'final-server-check.json').read_text())['late_output_sha256']
assert all(sha(p/f)==h for f,h in late.items())
assert (p/'design-handoff-8d34e371.md').read_bytes()==subprocess.check_output(['git','show','8d34e3714e246afb0bd74fe6943abeafd8f89c5b:docs/P1-L2/handoff-to-chatgpt.md'])
links=[];bad=[]
newdocs=['review-dossier.md','handoff-to-chatgpt.md','supervisor-summary.md','reproduce.md','README.md']
for name in newdocs:
 for match in re.finditer(r'\]\(([^)]+)\)',(p/name).read_text()):
  target=match.group(1).split('#')[0]
  if not target or '://' in target:continue
  if target in ['remote-readback.json','execution-delivery-validation.json']:continue
  links.append((name,target))
  if not (p/target).exists():bad.append((name,target))
assert not bad,bad
# 自己参照・遠隔回読は後続commitで成立させるため、ここでは成功を先取りしない。
for f in p.glob('*.json'):
 if not f.name.startswith('._'):json.loads(f.read_text())
for f in (root/'p1').glob('l2_*.py'):ast.parse(f.read_text())
for f in p.iterdir():
 if not f.name.startswith('._') and f.suffix in ['.md','.json','.csv']:
  text=f.read_text()
  assert not re.search(r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|github_pat_|ghp_[A-Za-z0-9]{30}',text),f
q=json.loads((p/'qualification-checks.json').read_text());assert [r['joint_cells'] for r in q]==[26,26,45]
server=json.loads((p/'final-server-check.json').read_text());assert server['status']=='PASS' and server['active_L2_workers']==0 and server['old_archives_exist_and_size_match']
receipt={'status':'PASS','date_JST':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),'validation_type':'静的件数・保存SHA・実行証拠の照合。科学再実行/独立科学審査ではない。','protected_old_files_unchanged':len(protected),'preexisting_root_README_unchanged':True if a.workspace_readme_sha else 'NOT_REQUESTED','table_row_counts':expected,'checkpoint_ID_set_match':True,'manifest_entries_match':manifests,'late_server_SHA_match':len(late),'design_handoff_byte_preserved':True,'existing_relative_links_checked':len(links),'missing_relative_links':bad,'figures_v2_visual_QA':'PASS_NONLOCAL_LONG_PHYSICAL','scientific_compute':'COMPLETE','technical_audit':'PASS','independent_scientific_review':'PENDING','researcher_scientific_acceptance':'PENDING','GitHub_readback':'PENDING_SEPARATE_RECEIPT','new_scientific_computation_this_validation':0}
(p/'execution-delivery-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('PASS',len(protected),len(links),sum(expected.values()))
