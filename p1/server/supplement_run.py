"""Bounded local runner for preregistered S2 supplement A/B/C CPU analyses."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PLAN_COMMIT="0ae3d092659be6c32b176ab8fa17612a833f49f9"
PLAN_SHA="dbdd38d7153570dc81318351639877a4a17254fe479c3faa249f668d5f5fff42"
LIMITS={"A":600,"B":900,"C":300}
MODULES={"A":"p1.server.supplement_coverage","B":"p1.server.supplement_selection",
         "C":"p1.server.supplement_physics"}
OUTPUT_CAP=1_000_000_000
RSS_CAP=4_000_000_000
LEDGER=Path("results/processed/P1-S2-SUPPLEMENT-20261025/budget-ledger.json")
MANIFESTS={"A":("coverage-manifest.json","DERIVED"),
           "B":("selection-manifest.json","MEASURED"),
           "C":("physics-manifest.json","MEASURED")}


def size_of(path):
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def run():
    import psutil
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--analysis-commit",required=True)
    parser.add_argument("--stage",choices=("A","B","C","all"),default="all")
    args=parser.parse_args()
    raw=args.raw.resolve();out=args.output.resolve()
    if not raw.is_dir() or out.exists():raise ValueError("Raw input missing or output exists")
    plan=Path("docs/P1-S2-supplement/analysis-plan.md")
    if hashlib.sha256(plan.read_bytes()).hexdigest()!=PLAN_SHA:
        raise ValueError("Preregistered plan SHA mismatch")
    out.mkdir(parents=True)
    LEDGER.parent.mkdir(parents=True,exist_ok=True)
    ledger=json.loads(LEDGER.read_text()) if LEDGER.exists() else {"attempts":[],"used_stage_s":{k:0.0 for k in LIMITS}}
    if any(a.get("state")=="running" for a in ledger["attempts"]):
        raise RuntimeError("Prior science attempt has no terminal receipt; reconcile it before continuing")
    env=os.environ.copy()
    env.update({"OMP_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2","MKL_NUM_THREADS":"2",
                "VECLIB_MAXIMUM_THREADS":"2","NUMEXPR_NUM_THREADS":"2", "CUDA_VISIBLE_DEVICES":"",
                "PYTORCH_ENABLE_MPS_FALLBACK":"0", "PYTHONDONTWRITEBYTECODE":"1",
                "PYTHONPATH":f"{Path('vendor/mdlearn-938cb80').resolve()}:{Path.cwd()}"})
    stages=("A","B","C") if args.stage=="all" else (args.stage,)
    receipt={"plan_commit":PLAN_COMMIT,"plan_sha256":PLAN_SHA,"analysis_commit":args.analysis_commit,
             "raw":str(raw),"created_utc":datetime.now(timezone.utc).isoformat(),
             "limits":{"threads":2,"rss_bytes":RSS_CAP,"output_bytes":OUTPUT_CAP,"stage_seconds":LIMITS,
                       "total_seconds":1800},"stages":[]}
    total=0.0
    for stage in stages:
        used=sum(ledger["used_stage_s"].values())
        allowance=min(LIMITS[stage]-ledger["used_stage_s"][stage],1800-used)
        if allowance<=0:
            receipt["stages"].append({"stage":stage,"status":"failed","stop_reason":"cumulative_budget_exhausted"})
            continue
        stage_out=out/stage
        log=out/f"stage-{stage}.log"
        code=f"from {MODULES[stage]} import analyze; analyze(__import__('sys').argv[1],__import__('sys').argv[2],__import__('sys').argv[3],__import__('sys').argv[4])"
        cmd=[sys.executable,"-B","-c",code,str(raw),str(stage_out),PLAN_COMMIT,args.analysis_commit]
        started=time.monotonic();peak_rss=0;stop_reason=None
        ledger["attempts"].append({"stage":stage,"output":str(stage_out),"state":"running",
                                    "started_utc":datetime.now(timezone.utc).isoformat(),"allowance_s":allowance})
        LEDGER.write_text(json.dumps(ledger,indent=2))
        with log.open("wb") as stream:
            proc=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            while proc.poll() is None:
                try:
                    p=psutil.Process(proc.pid)
                    members=[p]+p.children(recursive=True)
                    rss=sum(q.memory_info().rss for q in members if q.is_running())
                    peak_rss=max(peak_rss,rss)
                except psutil.Error:
                    rss=0
                elapsed=time.monotonic()-started
                if elapsed>allowance: stop_reason="cumulative_science_timeout"
                if rss>RSS_CAP: stop_reason="rss_cap"
                if size_of(out)>OUTPUT_CAP: stop_reason="output_cap"
                if stop_reason:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL)
                    break
                time.sleep(0.5)
            code=proc.wait()
        wall=time.monotonic()-started;total+=wall
        ledger["used_stage_s"][stage]+=wall
        ledger["attempts"][-1].update(state="finished",wall_s=wall,return_code=code,
                                       stop_reason=stop_reason)
        LEDGER.write_text(json.dumps(ledger,indent=2))
        manifest_name,expected_status=MANIFESTS[stage]
        manifest_path=stage_out/manifest_name
        try:
            manifest=json.loads(manifest_path.read_text())
            manifest_status=manifest.get("status")
        except (OSError,ValueError):
            manifest_status="MISSING_OR_INVALID"
        item={"stage":stage,"return_code":code,"stop_reason":stop_reason,"wall_s":wall,
              "peak_rss_bytes":peak_rss,"log_sha256":hashlib.sha256(log.read_bytes()).hexdigest(),
              "output_bytes_after_stage":size_of(out),"manifest_status":manifest_status,
              "status":"complete" if code==0 and not stop_reason and manifest_status==expected_status else "failed"}
        receipt["stages"].append(item)
        (out/"run-receipt.json").write_text(json.dumps(receipt,indent=2))
    receipt["total_science_s"]=total
    (out/"run-receipt.json").write_text(json.dumps(receipt,indent=2))
    return 0 if len(receipt["stages"])==len(stages) and all(i["status"]=="complete" for i in receipt["stages"]) else 1


if __name__=="__main__":sys.exit(run())
