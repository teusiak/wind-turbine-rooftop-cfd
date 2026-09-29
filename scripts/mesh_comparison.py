"""
Mesh comparison figure: Coarse / Medium / Fine, sliced through the turbine
location, "Surface With Edges" style (cell density only, no flow coloring).

Run this from the MSc/ folder (the one containing meshCase_coarse/,
meshCase_4-log/, meshCase_dense/ as siblings), NOT from inside a case folder
- unlike the per-case generate.py scripts, this one needs to reach into three
different case directories.

IMPORTANT: meshCase_dense's existing VTK1 export is currently a stale
duplicate of meshCase_4-log's (561,061 cells, not the real 2,324,696-cell
dense mesh). Regenerate it first:

    cd meshCase_dense
    foamToVTK -time 1780

(explicit -time, not -latestTime - avoids picking up the stale 1781/
subsetMesh directory.)

Outputs three separate PNGs (matching the filenames already referenced,
commented-out, in tex/4-results-discussion.tex):
    mesh_coarse_closeup.png
    mesh_medium_closeup.png
    mesh_fine_closeup.png
Copy them into WUT_Thesis/img/ and uncomment the three \\includegraphics
lines in tex/4-results-discussion.tex once generated (the figure captions
there already use the correct cell counts: 182,298 / 561,061 / 2,324,696).
"""
import pyvista as pv

# =============================================================================
# SETTINGS
# =============================================================================
TURBINE_X, TURBINE_Y, TURBINE_Z = 0.447, -3.022, 105.05

# Half-width of the zoom box around the turbine location, in meters. Tune
# this directly if you want to see more/less of the surrounding mesh -
# smaller = tighter zoom, more visible cell-density difference between panels.
ZOOM_HALF_WIDTH = 4.0

CASES = [
    dict(
        label="Coarse",
        cells="182,298",
        vtm="meshCase_coarse/VTK1/meshCase_coarse_1000.vtm",
        out="mesh_coarse_closeup.png",
    ),
    dict(
        label="Medium",
        cells="561,061",
        vtm="meshCase_4-log/VTK1/meshCase_4-log_1462.vtm",
        out="mesh_medium_closeup.png",
    ),
    dict(
        label="Fine",
        cells="2,324,696",
        # regenerate this before running - see module docstring
        vtm="meshCase_dense/VTK1/meshCase_dense_1780.vtm",
        out="mesh_fine_closeup.png",
    ),
]


# =============================================================================
# GENERATE ONE PANEL PER CASE
# =============================================================================
for case in CASES:
    print(f"\n=== {case['label']} ({case['cells']} cells) ===")
    print(f"Loading {case['vtm']} ...")
    vol = pv.read(case["vtm"])[0]
    print(f"  n_points={vol.n_points}, n_cells={vol.n_cells}")

    # Slice through the turbine location, normal to the domain's cross-stream
    # (X) axis - gives a streamwise/vertical cut through the rotor plane,
    # matching the side-elevation view used elsewhere in the thesis.
    sl = vol.slice(normal="x", origin=(TURBINE_X, TURBINE_Y, TURBINE_Z))
    print(f"  slice: n_points={sl.n_points}, n_cells={sl.n_cells}")

    p = pv.Plotter(off_screen=True, window_size=[1000, 1000])
    p.set_background("white")

    # Mesh density only - flat single color, edges on, no scalar field.
    p.add_mesh(sl, color="white", show_edges=True, edge_color="black",
               line_width=0.4, style="surface")

    p.view_yz()  # look along the slice normal (X) - shows the Y-Z cut face-on
    # reset_camera bounds are (xmin,xmax,ymin,ymax,zmin,zmax) in WORLD space:
    b = (TURBINE_X - 0.5, TURBINE_X + 0.5,
         TURBINE_Y - ZOOM_HALF_WIDTH, TURBINE_Y + ZOOM_HALF_WIDTH,
         TURBINE_Z - ZOOM_HALF_WIDTH, TURBINE_Z + ZOOM_HALF_WIDTH)
    p.reset_camera(bounds=b)

    p.show(screenshot=case["out"], auto_close=False)
    p.close()
    print(f"  -> {case['out']}")

print("\nDone. Copy all three PNGs into WUT_Thesis/img/.")
