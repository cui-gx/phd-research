"""検証済みL2表から全状態・全初期化を省略しない図を作る。"""
import argparse
import os
from pathlib import Path
from p1.l2_engineering import rows, runtime

def figures(a):
    runtime()
    os.environ['MPLCONFIGDIR']=str(a.output/'figure-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    public=a.output/'public';overview=rows(public/'overview.csv');metrics=rows(public/'model-metrics.csv');geometry=rows(public/'geometry.csv')
    colors={'M0':'#444444','F1':'#2166ac','F2':'#b35806'}
    for mask in ['NONLOCAL','LONG']:
        fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,label in zip(axs,['OLD_VALIDATION','RECENT_HELDOUT']):
            for arm,color in colors.items():
                for state in ['r01-s4','r01-s8','r02-s4','r02-s8']:
                    for init in ['1','2','3']:
                        rr=sorted([r for r in metrics if r['arm']==arm and r['state_id']==state and r['init_id']==init and r['set']==label and r['mask']==mask],key=lambda r:int(r['chain_steps']))
                        ax.plot([int(r['chain_steps']) for r in rr],[float(r['MODEL_BCE_per_frame']) for r in rr],color=color,alpha=.16,lw=.7)
                rr=sorted([r for r in overview if r['arm']==arm and r['set']==label and r['mask']==mask],key=lambda r:int(r['chain_steps']))
                x=[int(r['chain_steps']) for r in rr]
                ax.plot(x,[float(r['MODEL_BCE_per_frame_mean']) for r in rr],color=color,marker='o',lw=2,label=arm)
                ax.plot(x,[float(r['TRAIN_FREQUENCY_BCE_per_frame_mean']) for r in rr],color=color,ls='--',lw=1,label=arm+' 訓練頻度')
            ax.set_title(label);ax.set_xlabel('chain内の最適化step');ax.set_ylim(bottom=0);ax.set_xticks([0,200,400,800,1600]);ax.grid(alpha=.15)
        upper=max(float(r['MODEL_BCE_per_frame']) for r in metrics if r['mask']==mask)*1.08
        for ax in axs:ax.set_ylim(0,upper)
        axs[0].set_ylabel('再構成BCE [nats/フレーム]');axs[1].legend(fontsize=8,loc='upper left',bbox_to_anchor=(1.01,1))
        fig.suptitle(mask+'：細線は個別状態・初期化、太線は記述平均')
        fig.text(.5,.01,'2歴史根・4状態・3初期化。F1/F2の累計stepは横軸+200。信頼区間ではない。',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.05,.87,.92]);fig.savefig(public/('reconstruction-'+mask.lower()+'-v2.png'),dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,label in zip(axs,['OLD_VALIDATION','RECENT_HELDOUT']):
        for arm,color in colors.items():
            for state in ['r01-s4','r01-s8','r02-s4','r02-s8']:
                for init in ['1','2','3']:
                    rr=[r for r in metrics if r['arm']==arm and r['state_id']==state and r['init_id']==init and r['set']==label and r['mask']=='NONLOCAL'];rr.sort(key=lambda r:int(r['chain_steps']))
                    gm={(g['checkpoint'],g['set']):g for g in geometry if g['scale']=='RAW'}
                    ax.plot([int(r['chain_steps']) for r in rr],[float(gm[(r['checkpoint'],label)]['physical_knn_overlap']) for r in rr],color=color,alpha=.16,lw=.7)
            rr=sorted([r for r in overview if r['arm']==arm and r['set']==label and r['mask']=='NONLOCAL'],key=lambda r:int(r['chain_steps']))
            ax.plot([int(r['chain_steps']) for r in rr],[float(r['physical_knn_overlap_mean']) for r in rr],color=color,lw=2,marker='o',label=arm)
        base=next(r for r in overview if r['set']==label and r['mask']=='NONLOCAL')
        ax.axhline(float(base['contact_physical_knn_overlap_mean']),color='#555555',ls='--',lw=1,label='接触近傍')
        ax.axhline(float(base['time_physical_knn_overlap_mean']),color='#888888',ls=':',lw=1,label='時刻近傍')
        ax.set_title(label);ax.set_xlabel('chain内の最適化step');ax.set_ylim(0,1);ax.set_xticks([0,200,400,800,1600]);ax.grid(alpha=.15)
    axs[0].set_ylabel('RAW潜在と物理10近傍の重複率');axs[1].legend(fontsize=8)
    fig.suptitle('再構成とは別に検査する物理近傍保存')
    fig.text(.5,.01,'細線は全個別結果、太線は記述平均。独立標本数はフレーム数・checkpoint数ではない。',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.05,1,.92]);fig.savefig(public/'physical-neighbors-v2.png',dpi=180);plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);figures(p.parse_args())
