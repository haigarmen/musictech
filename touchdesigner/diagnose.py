"""
TouchDesigner Operator Parameter Diagnostic — v3
=================================================
Run this script ONCE to get all the information needed to fix the network scripts.

HOW TO RUN:
  1. Create a Text DAT anywhere in your project (NOT inside a Base COMP)
  2. Paste this entire script, set Language = Python, Run Script
  3. The output appears in the Textport (Alt+T)
  4. Copy the full output and share it
"""

print("=" * 65)
print("TouchDesigner Parameter Diagnostic  v3")
print("=" * 65)


def probe(type_name, node_name='_probe_tmp'):
    """Create an operator, print its parameters, destroy it. Returns par list."""
    p = me.parent()
    try:
        o = p.create(type_name, node_name)
    except Exception as e:
        print(f"  COULD NOT CREATE: {e}")
        return None

    # Group parameters by page
    pages = {}
    for par in o.pars():
        pg = par.page.name if hasattr(par, 'page') else '?'
        pages.setdefault(pg, []).append(par.name)

    for pg, names in sorted(pages.items()):
        print(f"    [{pg}] {names}")

    # Test connection methods
    conn_info = []
    if hasattr(o, 'setInput'):
        conn_info.append('setInput=YES')
    else:
        conn_info.append('setInput=NO')
    ic_len = len(o.inputConnectors) if hasattr(o, 'inputConnectors') else -1
    conn_info.append(f'inputConnectors.len={ic_len}')
    print(f"    connection: {', '.join(conn_info)}")

    o.destroy()
    return [p.name for p in o.pars()] if False else None   # pars already printed


# ── Operators used in all 5 network scripts ──────────────────────────────────

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
    print(f"\n── {_op_type} ──────────────────────────────────────────────")
    probe(_op_type)

# ── Operators used only in network 04 (inside geoComp) ───────────────────────

print("\n── geoComp (3D objects — network 04 only) ─────────────────────────────")
_p = me.parent()
try:
    _geo = _p.create('geoComp', '_probe_geo')
    for _inner_type in ('gridSOP', 'particleSOP', 'nullSOP'):
        print(f"\n  inside geoComp → {_inner_type}:")
        probe(_inner_type, '_probe_inner')
    _geo.destroy()
except Exception as _e:
    print(f"  geoComp failed: {_e}")

print("\n" + "=" * 65)
print("END OF DIAGNOSTIC — paste this full output to fix all scripts at once.")
print("=" * 65)
