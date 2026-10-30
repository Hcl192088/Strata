from pathlib import Path
R=Path(__file__).resolve().parent
t=(R/'build_pipeline.py').read_text()
t=t.replace('allowed={32084,27860,17028,23376,23300,25496,30620,os.getpid()}',
            'allowed={7724,25008,15228,15964,32332,5604,26672,os.getpid()}')
a=t.index('    restore_source=');b=t.index('    expected=',a);t=t[:a]+t[b:]
t=t.replace('4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A','AF976BB39DE0A47F68B559FDF985677CA46B17D7D83D50F92307A94B194E9453')
t=t.replace('4255FD01AE6E55A650B2E81316202C5B9206E0AE2271CD9FA81EDC3B27D33C1A','8B993048979A551B885313F85853C157FED1C13AA4DE5EBA1E9B15D284216351')
t=t.replace(",\n        'src/program/generate.cpp':'27CCC961B633A13D4B0E359E9505A5CBF3DDC6AB32B4C82B9FDD9084DBA40F5F'",'')
a=t.index('    # Remove only');b=t.index('    shutil.copyfile(D/',a)
t=t[:a]+"    assert sha(S/'src/core/expert_source.cpp')=='2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658'\n    assert sha(S/'src/program/generate.cpp')=='1F17C2E537DA102F4E4AA1D58F25C4DC083AEEA853369D979E23D5EB50E1B24B'\n"+t[b:]
(R/'build_roles.py').write_text(t)
