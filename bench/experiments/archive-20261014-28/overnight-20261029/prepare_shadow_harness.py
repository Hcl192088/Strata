from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
dst=ROOT/'shadow-harness';dst.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'harness/next_steps_ab_20261018.py',dst/'next_steps_ab_20261018.py')
t=(ROOT/'harness/replay_ab_20261027.py').read_text()
old="""                if srv.poll() is not None:
                    raise RuntimeError('server exited rc=%s' % srv.returncode)
"""
assert t.count(old)==1
t=t.replace(old,old+"""                live_log = d / 'engine.log'
                if live_log.exists() and 'DIRECT_SHADOW FATAL' in live_log.read_text(encoding='utf-8', errors='replace'):
                    raise RuntimeError('DIRECT_SHADOW FATAL: candidate refused source/read; no fallback')
""")
old="""            meta['load_s'] = round(time.time() - t0, 1)
"""
assert t.count(old)==1
t=t.replace(old,"""            owned_engines = [p for p in psutil.Process(srv.pid).children(recursive=True) if p.name().lower() == 'strata.exe']
            assert len(owned_engines) == 1, 'engine ownership mismatch'
            engine = owned_engines[0]
            assert ns.sha(Path(engine.exe())) == meta['binary_sha256'], 'running binary mismatch'
            engine.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
            assert engine.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS
            effective = engine.environ()
            assert effective.get('STRATA_IQ3S_MT1') == '1' and not effective.get('STRATA_IQ_MT_MIN')
            assert effective.get('STRATA_DIRECT_SHADOW_FIRST') == (spec.get('env') or {}).get('STRATA_DIRECT_SHADOW_FIRST')
            meta['priority_gate'] = dict(pid=engine.pid, created=engine.create_time(), priority=engine.nice(), verified_at=time.time(), before_first_request=True)
"""+old)
old="""                    body = make_body(pid, max_tokens)
"""
assert t.count(old)==1
t=t.replace(old,"""                    assert engine.is_running() and engine.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS, 'priority/ownership changed'
"""+old)
(dst/'replay_ab_20261027.py').write_text(t)
print(dst)
