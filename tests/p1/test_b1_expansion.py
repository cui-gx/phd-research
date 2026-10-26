"""B1拡張の割付・情報窓・欠損と階層記述を合成データで検査する。"""
import unittest
import numpy as np
from p1.server.expansion_contract import experiment_matrix
from p1.server.b1_science import indices
from p1.server.expansion_science import grid_cells,js_bits,state_features
from p1.server.expansion_analysis import randomness_summary,safe_correlation


class ExpansionTests(unittest.TestCase):
    def test_scope_and_shared_F0(self):
        a=experiment_matrix();self.assertEqual(a,experiment_matrix())
        self.assertEqual(len(a['roots']),8);self.assertEqual(len(a['states']),16);self.assertEqual(len(a['branches']),240)
        self.assertEqual(len({b['branch_id'] for b in a['branches']}),240)
        self.assertEqual(sum(b['length_ns'] for b in a['branches']),960)
        for state in a['states']:
            rows=[b for b in a['branches'] if b['state_id']==state['state_id']]
            self.assertEqual([sum(b['arm']==arm for b in rows) for arm in ['F0','F1','F2']],[3,6,6])
            for m in (1,2,3):self.assertEqual(len({b['MD_seed'] for b in rows if b['MD_block']==m}),1)
            for t in (1,2):self.assertEqual(len({b['training_seed'] for b in rows if b['training_block']==t}),1)
        self.assertEqual(a['branches'][0]['state_id'],'r01-s4')

    def test_role_seeds_disjoint(self):
        a=experiment_matrix();history={v['history_seed'] for v in a['roots']};train={s for v in a['states'] for s in v['training_seeds'].values()};md={s for v in a['states'] for s in v['MD_seeds'].values()}
        self.assertEqual((len(history),len(train),len(md)),(8,32,48));self.assertFalse(history&train or history&md or train&md)

    def test_relative_windows_at_eight_ns(self):
        time=np.arange(1,16001)*.5;valid=np.ones(16000,bool);b=6000
        old=indices(time,valid,b-1900,b-400,800);val=indices(time,valid,b-300,b,200);new=indices(time,valid,b,b+1600,400)
        self.assertTrue(np.all((time[old]>4100)&(time[old]<=5600)))
        self.assertTrue(np.all((time[val]>5700)&(time[val]<=6000)))
        self.assertTrue(np.all((time[new]>6000)&(time[new]<=7600)))
        self.assertFalse(set(old)&set(new) or set(old)&set(val))
        with self.assertRaises(ValueError):indices(time[:4000],valid[:4000],6000,7600,400)

    def test_fixed_physical_bins_and_JS(self):
        self.assertEqual(grid_cells([0,.49,.5,1.],[0,.049,.05,1.]),[(0,0),(0,0),(1,1),(2,20)])
        self.assertAlmostEqual(js_bits([(0,0)]*8,[(0,0)]*4),0.)
        self.assertAlmostEqual(js_bits([(0,0)]*8,[(1,1)]*4),1.)
        self.assertIsNone(js_bits([],[(0,0)]))

    def test_crossed_noise_description(self):
        r=randomness_summary([[0,1,2],[10,11,12]])
        self.assertEqual(r['training_means'],[1.,11.]);self.assertEqual(r['training_mean_difference'],10.)
        self.assertEqual(r['MD_SD_by_training'],[1.,1.]);self.assertEqual(r['additive_residual_RMS'],0.)
        self.assertFalse(r['pure_interaction_variance_identified'])
        with self.assertRaises(ValueError):randomness_summary([1,2,3])

    def test_future_data_rejected_before_reading(self):
        import time
        with self.assertRaises(ValueError):state_features(dict(inputs_available_monotonic=time.monotonic()+100,pool='/nonexistent'),None)

    def test_full_matrix_aggregation_and_shared_baseline(self):
        import tempfile,json,csv
        from pathlib import Path
        from p1.server.expansion_analysis import finalize_campaign,CONTINUOUS
        from p1.server.gq_r2 import dump
        matrix=experiment_matrix()
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)/'run';art=Path(tmp)/'art';art.mkdir();(run/'tasks').mkdir(parents=True)
            def task(name):
                folder=run/'tasks'/name;out=folder/'science';out.mkdir(parents=True)
                dump(folder/'request.json',dict(kind='analysis'))
                dump(folder/'execution.json',dict(GPU_occupation_s=0,elapsed_s=1))
                dump(out/'result.json',dict(status='success',artifacts={}))
                return out
            for st in matrix['states']:
                sid=st['state_id'];num=int(st['root_id'][1:])
                p=task(sid+'-features');dump(p/'state-features.json',dict(root_id=st['root_id'],state_id=sid,X=dict(new_nonrepeat_fraction_eps2=float(num)/8),Z={},W=dict(grid_cells_total=num)))
                p=task(sid+'-selection');dump(p/'selection-comparisons.json',[dict(overlaps={'1':0})])
                for name in ['M0','F1-t1','F1-t2','F2-t1','F2-t2']:task(sid+'-'+name)
            for b in matrix['branches']:
                p=task(b['branch_id']+'-analysis');dump(p/'result.json',dict(status='success',artifacts={},qualified_frames=8))
                value=int(b['root_id'][1:])*10+b['milestone_ns']+int(b['arm'][1:])+b['training_block']+b['MD_block']
                continuous=[];discrete=[]
                for burn in [0,100,200,500]:
                    for prefix in [1.,2.,4.]:
                        continuous.append(dict(burn_ps=burn,prefix_ns=prefix,frames=8,**{k:value for k in CONTINUOUS}))
                        for e in [1.5,2.,3.]:
                            for tau in [0,5]:discrete.append(dict(burn_ps=burn,prefix_ns=prefix,epsilon_A=e,tau_ps=tau,added_regions=value,representative_frame_ids=[],confirmation_frame_ids=[]))
                dump(p/'continuous.json',continuous);dump(p/'discrete.json',discrete);dump(p/'autocorrelation.json',[])
                (p/'time-windows.csv').write_text('start_ps,frames,distance_mean_A\n0,8,1\n')
            result=finalize_campaign(run,art,matrix)
            self.assertEqual(result['completed_downstream'],240)
            with (art/'summary-v1/root-summary.csv').open() as f:rows=list(csv.DictReader(f))
            main=next(r for r in rows if r['comparison']=='F2-F1' and r['metric']=='distance_mean_A' and r['burn_ps']=='100' and r['prefix_ns']=='4.0')
            self.assertEqual(int(main['complete_roots']),8);self.assertAlmostEqual(float(main['mean']),1.)
            self.assertAlmostEqual(float(main['bootstrap95_low']),1.);self.assertAlmostEqual(float(main['bootstrap95_high']),1.)
            with (art/'summary-v1/paired-effects.csv').open() as f:pairs=list(csv.DictReader(f))
            selected=[r for r in pairs if r['state_id']=='r01-s4' and r['comparison']=='F2-F0' and r['metric']=='distance_mean_A' and r['burn_ps']=='100' and r['prefix_ns']=='4.0']
            self.assertEqual(len(selected),6);self.assertEqual(len({r['shared_F0_branch_id'] for r in selected}),3)

    def test_publication_redaction(self):
        from p1.server.expansion_publish import sanitized
        from pathlib import Path
        value={'/owned/project/file':'GPU-01234567-89ab-cdef-0123-456789abcdef'}
        self.assertEqual(sanitized(value,Path('/owned/project')),{'<PROJECT>/file':'GPU_REDACTED'})

    def test_root_archive_integrity_and_resume(self):
        import tempfile,json
        from pathlib import Path
        from p1.server.expansion_publish import archive
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);run=base/'run';art=base/'art';(run/'tasks').mkdir(parents=True);art.mkdir()
            (run/'manifest.json').write_text('{}')
            matrix=experiment_matrix()
            for r in matrix['roots']:
                p=run/'tasks'/(r['root_id']+'-example');p.mkdir();(p/'evidence').write_text('original')
            first=archive(run,art,matrix);self.assertEqual(len(first),9)
            self.assertEqual(first,archive(run,art,matrix))
            with (art/'archives/r01.tar.gz').open('ab') as f:f.write(b'changed')
            with self.assertRaises(ValueError):archive(run,art,matrix)

    def test_constant_correlation_is_missing(self):
        self.assertIsNone(safe_correlation([1,1],[1,2],rank=True))
        self.assertAlmostEqual(safe_correlation([1,2,3],[3,2,1],rank=True),-1.)


if __name__=='__main__':unittest.main()
