"""
TouchDesigner Operator Type Diagnostic
=======================================
Run this FIRST if any network script fails with NameError.

HOW TO RUN:
  1. Create a Text DAT anywhere in your project
  2. Paste this script, set Language = Python, Run Script
  3. The output will appear in the Textport (Alt+T)
  4. Share or read the output to understand what's available
     in your specific TouchDesigner build.
"""

print("=" * 60)
print("TouchDesigner Python Environment Diagnostic")
print("=" * 60)

# 1. Confirm we are inside TD's Python environment
print(f"\n1. Running inside TouchDesigner: {'me' in dir()}")
try:
    print(f"   This DAT:       {me}")
    print(f"   Parent COMP:    {me.parent()}")
except Exception as e:
    print(f"   'me' access failed: {e}")

# 2. Scan globals() for OP type constants
g = globals()
chops_g = sorted(k for k in g if k.endswith('CHOP'))
tops_g  = sorted(k for k in g if k.endswith('TOP'))
sops_g  = sorted(k for k in g if k.endswith('SOP'))
print(f"\n2. OP types found in globals():")
print(f"   CHOP count: {len(chops_g)}   sample: {chops_g[:4]}")
print(f"   TOP count:  {len(tops_g)}    sample: {tops_g[:4]}")
print(f"   SOP count:  {len(sops_g)}    sample: {sops_g[:4]}")

# 3. Scan the td module
print(f"\n3. Scanning the 'td' module:")
try:
    import td as _td
    chops_td = sorted(k for k in dir(_td) if k.endswith('CHOP'))
    tops_td  = sorted(k for k in dir(_td) if k.endswith('TOP'))
    print(f"   CHOP count: {len(chops_td)}   sample: {chops_td[:4]}")
    print(f"   TOP count:  {len(tops_td)}    sample: {tops_td[:4]}")
    print(f"   td.audiodevInCHOP exists: {hasattr(_td, 'audiodevInCHOP')}")
    print(f"   td.mathCHOP exists:       {hasattr(_td, 'mathCHOP')}")
except Exception as e:
    print(f"   import td failed: {e}")

# 4. Scan builtins
import builtins as _bt
chops_bt = sorted(k for k in dir(_bt) if k.endswith('CHOP'))
tops_bt  = sorted(k for k in dir(_bt) if k.endswith('TOP'))
print(f"\n4. OP types found in builtins:")
print(f"   CHOP count: {len(chops_bt)}   sample: {chops_bt[:4]}")
print(f"   TOP count:  {len(tops_bt)}    sample: {tops_bt[:4]}")

# 5. Audio-specific search across all sources
print(f"\n5. Everything containing 'audio' (any case) across all sources:")
audio_g  = [x for x in g    if 'audio' in x.lower()]
audio_bt = [x for x in dir(_bt) if 'audio' in x.lower()]
try:
    import td as _td2
    audio_td = [x for x in dir(_td2) if 'audio' in x.lower()]
except Exception:
    audio_td = []
print(f"   globals():  {audio_g}")
print(f"   builtins:   {audio_bt}")
print(f"   td module:  {audio_td}")

# 6. Test string-based operator creation (does TD accept type as a string?)
print(f"\n6. Testing string-based create() on me.parent():")
try:
    test_op = me.parent().create('math', '_diag_test')
    print(f"   create('math', ...) WORKED → op type string IS supported")
    test_op.destroy()
except Exception as e:
    print(f"   create('math', ...) failed: {e}")

try:
    test_op = me.parent().create('mathCHOP', '_diag_test2')
    print(f"   create('mathCHOP', ...) WORKED → full type string supported")
    test_op.destroy()
except Exception as e:
    print(f"   create('mathCHOP', ...) failed: {e}")

print("\n" + "=" * 60)
print("Paste this full output when reporting issues.")
print("=" * 60)
