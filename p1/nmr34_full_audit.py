"""新出力のbyte/SHAと原archive存在を監査し、消費時間を既存台帳へ加算する。"""
import argparse,fcntl,json,time,hashlib,datetime
from pathlib import Path
from nmr34_full import checkpoint
from nmr34_v2_execute import append_event


def audit(project,out):
    """原DCDをdecodeせず、成功成果を読み取り専用で監査する。"""
    import psutil
    lock=(project/'artifacts/nmr34-full-global.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=out/'budget-state.json';prior=json.loads(ledger.read_text());assert not prior['segment_open']
    start=time.monotonic();peak=0
    def guard():
        nonlocal peak
        peak=max(peak,psutil.Process().memory_info().rss)
        if prior['spent_s']+time.monotonic()-start>=7200 or time.monotonic()-start>=300 or peak>2*1024**3:
            raise RuntimeError('監査資源門で停止')
    def sha(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024**2),b''):guard();h.update(b)
        return h.hexdigest()
    assert json.loads((out/'compute-complete.json').read_text())['completed']==272
    assert json.loads((out/'analysis-complete.json').read_text())['status']=='PASS'
    units=[]
    for dest in sorted((out/'units').iterdir()):
        r=json.loads((dest/'receipt.json').read_text());assert r['status']=='PASS'
        assert json.loads((dest/'success.json').read_text())['status']=='PASS'
        for name,h in r['outputs'].items():assert sha(dest/name)==h
        units.append({k:v for k,v in r.items() if k!='outputs'})
    assert len(units)==272
    archives=[];ar=project/'artifacts/b1-expansion-20261026/archives'
    for name,m in json.loads((ar/'archive-manifest.json').read_text()).items():
        p=ar/name;assert p.is_file() and p.stat().st_size==m['bytes'];archives.append(dict(name=name,bytes=p.stat().st_size,historical_SHA=m['sha256'],fresh_SHA=False))
    files=[]
    controls={'budget-state.json','budget-events.jsonl'}
    import zipfile,numpy as np
    near_pairs=0
    for p in (out/'units').glob('*/chunk-*.npz'):
        with zipfile.ZipFile(p) as archive:
            with archive.open('near_pair.npy') as stream:
                version=np.lib.format.read_magic(stream)
                shape,_,_=np.lib.format._read_array_header(stream,version)
                near_pairs+=shape[0]
        guard()
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name not in controls and p.name!='delivery-audit.json':files.append(dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)))
    elapsed=time.monotonic()-start;spent=prior['spent_s']+elapsed
    append_event(out/'budget-events.jsonl',dict(event='DELIVERY_AUDIT',wall_s=elapsed,spent_s=spent))
    checkpoint(ledger,{**prior,'spent_s':spent})
    for name in sorted(controls):
        p=out/name;files.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
    assert sum(r['bytes'] for r in files)<2*1024**3
    result=dict(status='PASS',near_pairs=near_pairs,checked_at_JST=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),units=units,archives=archives,new_outputs=files,
        total_output_bytes=sum(r['bytes'] for r in files),audit_wall_s=elapsed,cumulative_wall_with_audit_s=spent,audit_peak_RSS_bytes=peak,global_lock_held=False)
    with (out/'delivery-audit.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ['units','archives','new_outputs']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('output',type=Path);a=p.parse_args();audit(a.project,a.output)
