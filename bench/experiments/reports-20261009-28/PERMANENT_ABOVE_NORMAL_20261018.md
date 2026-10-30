User explicitly authorized permanent AboveNormal startup configuration.
Remote server task Strata-Task020-API settings Priority changed4->2;
existing principal,actions,triggers and other settings preserved.
Launcher tools/start_task020_api.ps1 PriorityClass Normal->AboveNormal.
tools/strata_memory_policy.py explicitly sets newly detected Strata child to
psutil.ABOVE_NORMAL_PRIORITY_CLASS and verifies readback before RAM retention;
does not rely on Windows child processes inheriting AboveNormal by default.
No engine/model/source rebuild,temperature or other inference setting changed.
Current engine PID33756 remains AboveNormal/BasePriority10;API not restarted.
Permanent next-start behavior has not been exercised by a real API restart.
Python syntax compilation passed;task XML andlauncher re-read after modification.
Original taskXML/launcher/policy preserved in:
C:\Users\User\Strata-Adrian-control\runs\permanent-above-normal-20261018
