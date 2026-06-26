"""
TouchDesigner Operator Parameter Diagnostic — v4
=================================================
Run this script ONCE to get all parameter names for every operator
used in the 5 network scripts.

HOW TO RUN:
  1. Create a Text DAT anywhere in your project
  2. Paste this entire script, set Language = Python, Run Script
  3. Output appears in the Textport (Alt+T)
  4. Copy the full output and share it
"""

print("=" * 65)
print("TouchDesigner Parameter Diagnostic  v4")
print("=" * 65)


def probe(type_name, node_name='_probe_tmp'):
    p = me.parent()
    try:
        o = p.create(type_name, node_name)
    except Exception as e:
        print(f"  COULD NOT CREATE '{type_name}': {e}")
        return

    # Collect all parameter names
    all_par_names = []
    try:
        for par in o.pars():
            try:
                all_par_names.append(par.name)
            except Exception:
                pass
    except Exception as e:
        print(f"  pars() failed: {e}")

    print(f"  ALL PARAMS: {sorted(all_par_names)}")

    # Connection info
    has_setInput = hasattr(o, 'setInput')
    try:
        ic_len = len(o.inputConnectors)
    except Exception:
        ic_len = -1
    print(f"  setInput={has_setInput}  inputConnectors.len={ic_len}")

    try:
        o.destroy()
    except Exception:
        pass


_ops = [
    'audiodeviceinCHOP',
    'audiospectrumCHOP',
    'analyzeCHOP',
    'mathCHOP',
    'nullCHOP',
    'choptoTOP',
    'levelTOP',
    'noiseTOP',
    'hsvAdjustTOP',
    'feedbackTOP',
    'compositeTOP',
    'glowTOP',
    'nullTOP',
    'circleTOP',
    'transformTOP',
    'rampTOP',
    'renderTOP',
    'displaceTOP',
    'videodeviceinTOP',
]

for _op_type in _ops:
    print(f"\n── {_op_type}")
    probe(_op_type)

# SOPs inside a Geo COMP
print("\n── gridSOP / particleSOP / nullSOP (inside geoComp)")
try:
    _geo = me.parent().create('geoComp', '_probe_geo_outer')
    for _st in ('gridSOP', 'particleSOP', 'nullSOP'):
        print(f"\n  {_st}:")
        probe(_st, '_probe_sop_inner')
    _geo.destroy()
except Exception as _e:
    print(f"  geoComp probe failed: {_e}")

print("\n" + "=" * 65)
print("END — paste the full output above to fix all scripts at once.")
print("=" * 65)
