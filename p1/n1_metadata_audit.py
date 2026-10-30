"""N1準備用の読取り専用メタデータ監査。DCDはbyte SHAとheaderだけ読む。"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import struct
import time


def ca_keys(path):
    """CAの文字列対応を読む。実座標の距離・RMSD・Qは計算しない。"""
    keys = []
    for line in path.read_text().splitlines():
        if line.startswith('ENDMDL'):
            break
        if line.startswith('ATOM') and line[12:16].strip() == 'CA':
            keys.append((line[21:22], line[22:26].strip(), line[26:27].strip(), line[17:20].strip(), line[16:17].strip()))
    if len(keys) != 28 or len(set(keys)) != 28:
        raise ValueError('28個の一意なCA対応を確認できません。')
    return keys


def main(a):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise RuntimeError('GPU不可視条件が必要です。')
    begin, cpu = time.monotonic(), time.process_time()
    a.output.mkdir(exist_ok=False, parents=True)
    def guard():
        if time.monotonic()-begin > 300 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2*1024**2:
            raise RuntimeError('準備監査の時間/RSS保護値を超えました。')
    def sha(path):
        h = hashlib.sha256()
        with path.open('rb') as f:
            while chunk := f.read(1024*1024):
                h.update(chunk); guard()
        return h.hexdigest()
    plan = json.loads(a.manifest.read_text())
    run = a.project/'runs/b1-expansion-20261026'
    reference = a.project/'source/inputs/p1-fsd-ey/1FME-folded-model1.pdb'
    ref_keys = ca_keys(reference)
    if sha(reference) != 'a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8':
        raise ValueError('天然参照SHA不一致。')
    md, models, embedding = [], [], []
    try:
        for task in plan:
            kind, tid = task['request']['kind'], task['task_id']
            if kind == 'ai':
                kind = task['request']['operation']
            if kind not in ('md', 'train', 'infer'):
                continue
            s = run/'tasks'/tid/'science'
            if sha(s/'result.json') != task['raw_result_sha256']:
                raise ValueError('既存result SHA不一致: '+tid)
            d = json.loads((s/'result.json').read_text())
            if sha(run/'tasks'/tid/'request.json') != task['raw_request_sha256']:
                raise ValueError('既存request SHA不一致: '+tid)
            if kind == 'md':
                artifacts = d['artifacts']
                for name in ('sim.dcd', 'initial.pdb'):
                    if sha(s/name) != artifacts[name]:
                        raise ValueError('MD原ファイルSHA不一致: '+tid+'/'+name)
                if ca_keys(s/'initial.pdb') != ref_keys:
                    raise ValueError('CA文字列対応不一致: '+tid)
                with (s/'sim.dcd').open('rb') as f:
                    header = f.read(100)
                endian = '<' if struct.unpack('<i', header[:4])[0] == 84 else '>'
                if struct.unpack(endian+'i', header[:4])[0] != 84 or header[4:8] != b'CORD':
                    raise ValueError('想定DCD headerではありません: '+tid)
                frames = struct.unpack(endian+'i', header[8:12])[0]
                expected = int(d['length_ns']*2000)
                if frames != expected:
                    raise ValueError('DCD headerのframe数不一致: '+tid)
                md.append(dict(task_id=tid,relative_dcd='tasks/'+tid+'/science/sim.dcd',DCD_sha256=artifacts['sim.dcd'],DCD_bytes=(s/'sim.dcd').stat().st_size,topology_sha256=artifacts['initial.pdb'],header_frames=frames,CA_mapping='PASS_28',kind='HISTORY' if '-h' in tid else 'DOWNSTREAM',length_ns=d['length_ns'],seed=d['seed'],initial_time_ps=d['initial_time_ps'],final_time_ps=d['final_time_ps']))
            if kind == 'train':
                actual = sha(s/'checkpoint.pt')
                if actual != d['checkpoint_sha256']:
                    raise ValueError('既存checkpoint SHA不一致: '+tid)
                models.append(dict(task_id=tid,checkpoint_sha256=actual,loaded_model=False))
            if kind == 'infer':
                actual = sha(s/'ranking.npz')
                if actual != d['artifacts']['ranking.npz']:
                    raise ValueError('保存embedding SHA不一致: '+tid)
                embedding.append(dict(task_id=tid,relative_path='tasks/'+tid+'/science/ranking.npz',sha256=actual,rows_not_recomputed=True,role='HISTORY_CANDIDATES_ONLY_NOT_DOWNSTREAM_EMBEDDING'))
        assert len(md) == 272 and len(models) == 80 and len(embedding) == 96
        with (a.output/'MD-file-audit.csv').open('x') as f:
            w=csv.DictWriter(f,fieldnames=list(md[0]));w.writeheader();w.writerows(md)
        archives=a.project/'artifacts/b1-expansion-20261026/archives'
        am=json.loads((archives/'archive-manifest.json').read_text())
        archive_rows=[dict(name=k,exists=(archives/k).is_file(),size_match=(archives/k).stat().st_size==v['bytes'],bytes=v['bytes'],expected_sha256=v['sha256'],SHA_rehashed_this_audit=False) for k,v in am.items()]
        assert len(archive_rows)==9 and all(r['exists'] and r['size_match'] for r in archive_rows)
        versions={name:importlib.metadata.version(name) for name in ['numpy','MDAnalysis','openmm','torch','scikit-learn','mdlearn']}
        result=dict(status='PASS_METADATA_ONLY',MD_files=len(md),history_files=32,downstream_files=240,model_byte_SHA_checked=len(models),model_loads=0,embedding_files_SHA_checked=len(embedding),DCD_coordinate_frames_decoded=0,new_native_scientific_values=0,new_MD_train_inference_LOF=0,models=models,embedding=embedding,archives=archive_rows,versions=versions,wall_s=time.monotonic()-begin,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,GPU_visible=False)
        (a.output/'metadata-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('models','embedding','archives')},ensure_ascii=False))
    except BaseException as e:
        (a.output/'failure.json').write_text(json.dumps({'status':'FAILED_METADATA_AUDIT','reason':str(e),'new_scientific_values':0},ensure_ascii=False)+'\n')
        raise


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('manifest',type=Path);p.add_argument('output',type=Path)
    main(p.parse_args())
