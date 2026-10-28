#!/usr/bin/env bash
# 承認済みR1の後段だけを直列実行する。元再現中に第二workerを起動しない。
set -euo pipefail
project=${1:?本人プロジェクトが必要です}
output=${2:?R1専用出力が必要です}
bundle=${3:?検証済みbundleが必要です}
python_bin=${4:?既存許可Pythonが必要です}
original_pid=${5:?元再現プロセスのPIDが必要です}
implementation_commit=${6:?固定CPU実装commitが必要です}

export CUDA_VISIBLE_DEVICES=-1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="${output}/../mpl-cache"
exec 9>"${output}/pipeline.lock"
flock -n 9
cd "$bundle"

# 既存の本人プロセスを待つだけであり、停止・再起動は行わない。
while kill -0 "$original_pid" 2>/dev/null; do
  process_state=$("$python_bin" - "$original_pid" <<'PY'
import os,sys
from pathlib import Path
p=Path('/proc')/sys.argv[1]
try:
    owner=p.stat().st_uid
    state=(p/'stat').read_text().split(') ',1)[1].split()[0]
    cmd=(p/'cmdline').read_bytes()
except FileNotFoundError:
    print('DONE')
    raise SystemExit(0)
if owner!=os.getuid():
    raise SystemExit('元再現PIDの所有者が一致しません。')
if state=='Z':
    print('DONE')
    raise SystemExit(0)
if b'p1.r1_cpu_review' not in cmd or b'original' not in cmd:
    raise SystemExit('元再現PIDが別のプロセスに変わりました。')
print('RUNNING')
PY
)
  if [[ "$process_state" == DONE ]]; then break; fi
  sleep 10
done

"$python_bin" - "$output" <<'PY'
import json,sys
from pathlib import Path
out=Path(sys.argv[1])
assert json.loads((out/'original-reproduction.json').read_text())['status']=='PASS'
events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
assert any(e['event']=='stage_complete' and e.get('stage')=='original' for e in events)
assert not any(e['event']=='stopped' for e in events)
print('全ORIGINAL_HISTORYのPASSとプロセス終了を確認しました。',flush=True)
PY

# 新規プロセスの仮想アドレス空間も2 GiBに制限する。数値設定は変更しない。
ulimit -v 2097152
for stage in references lof summary; do
  "$python_bin" -m p1.r1_cpu_review --project "$project" --output "$output" --bundle "$bundle" --stage "$stage"
done
"$python_bin" -m p1.r1_cpu_report --project "$project" --output "$output" --implementation-commit "$implementation_commit"
"$python_bin" -m p1.r1_cpu_review --project "$project" --output "$output" --bundle "$bundle" --stage finish
"$python_bin" -m p1.r1_cpu_report --project "$project" --output "$output" --implementation-commit "$implementation_commit" --finalize
printf '%s\n' '承認済みR1 CPU全工程が完了しました。独立科学審査を待って停止します。'
