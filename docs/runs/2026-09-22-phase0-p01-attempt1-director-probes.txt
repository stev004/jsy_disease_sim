import json
import tempfile
from pathlib import Path
import yaml
from jersey_outbreak.phase0_campaign import CampaignConfig, CandidateCell, ProfileDiagnostic, RecoveryRow, TruthDiagnostics, evaluate_p01, write_research_bundle
p=Path('configs/calibration/v13_phase0_synthetic.yaml')
base=yaml.safe_load(p.read_text())
with tempfile.TemporaryDirectory(prefix='jos-p01-director-') as tmp:
    for name, mutate in [('start_date',lambda d:d.update(start_date='2025-02-01')),('duration_days',lambda d:d.update(duration_days=29)),('profile_gap',lambda d:d['identifiability'].update(profile_gap=0.9)),('coverage_minimum',lambda d:d['acceptance'].update(descriptive_coverage_minimum=0.0))]:
        d=yaml.safe_load(p.read_text()); mutate(d)
        q=Path(tmp)/f'{name}.yaml'; q.write_text(yaml.safe_dump(d,sort_keys=False))
        try: CampaignConfig.from_yaml(q); print(f'ALTERED_DECLARATION_ACCEPTED {name}')
        except Exception as e: print(f'ALTERED_DECLARATION_REJECTED {name}: {type(e).__name__}')
    c=CampaignConfig.from_yaml(p)
    truth=CandidateCell(0.08,2,0.75,0.25)
    profiles=tuple(ProfileDiagnostic(d.name,d.candidates,(1.,0.,1.),0.,1.,False,1.,True) for d in c.dimensions)
    diag=TruthDiagnostics(10,1,1,1,3,True,True)
    rows=tuple(RecoveryRow(seed,'1'*64,truth,profiles,False,truth,diag) for seed in (1,2,3,4,5))
    ev=evaluate_p01(rows,config=c)
    print('NO_MEASURED_WORKLOAD_UNDECLARED_TARGET_SEEDS_STATUS',ev.status)
    out=Path(tmp)/'bundle'
    kwargs=dict(campaign_config_path=p,predeclaration_path=Path('/home/steven/jos-p0-predeclaration.md'),seed_ledger=[],candidate_loss_surfaces={})
    write_research_bundle(out,**kwargs)
    write_research_bundle(out,**kwargs)
    print('REPEATED_BUNDLE_WRITES_ALLOWED',True)
    sums=(out/'SHA256SUMS').read_text()
    print('SECOND_HASH_LIST_INCLUDES_ITS_OLD_SELF',any(line.endswith('  SHA256SUMS') for line in sums.splitlines()))