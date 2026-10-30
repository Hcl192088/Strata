from pathlib import Path
R=Path(__file__).resolve().parent
for src,dst in [('analyze_pipeline.py','analyze_roles.py'),('audit_pipeline.py','audit_roles.py')]:
    t=(R/src).read_text()
    for old,new in [('PD','RD'),('OD','GD'),('P','R'),('O','G')]:t=t.replace("'"+old+"'","'"+new+"'")
    t=t.replace('pipeline-results','roles-results')
    if src.startswith('audit'):
        t=t.replace('3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230','165059E7A5F528B80D5B029C487741AD652E0F0C38F4B6E112F99F4AAC61A110')
        t=t.replace("('R','RD','CHK','SMOKE')","('G','GD','R','RD','CHK','SMOKE')")
        needle="    assert env.get('STRATA_NATIVE_PIPE_CHECK')"
        pos=t.index(needle)
        t=t[:pos]+"    assert env.get('STRATA_NATIVE_PIPE_ROLES')==('1' if arm in ('R','RD','CHK','SMOKE') else None)\n"+t[pos:]
        t=t.replace("('STRATA_NATIVE_PIPE','STRATA_NATIVE_PIPE_CHECK','STRATA_CPU_PHASE_DIAG'","('STRATA_NATIVE_PIPE_ROLES','STRATA_NATIVE_PIPE','STRATA_NATIVE_PIPE_CHECK','STRATA_CPU_PHASE_DIAG'")
    (R/dst).write_text(t)
    compile(t,dst,'exec')
