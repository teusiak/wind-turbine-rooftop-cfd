import pyvista as pv
import numpy as np

# =============================================================================
# SETTINGS
# =============================================================================
vtk_main = "./VTK1/meshCase_turbine_893.vtm"

# Use the ORIGINAL clean CAD STL geometry for display, not the solved-mesh
# boundary patch export. checkMesh flagged real topological defects in the
# solved-mesh boundary patches - the raw STL is watertight design geometry
# with no such issues, and we don't need any solved field data ON these
# surfaces anyway (they're just shown as solid context alongside the
# volumetric streamlines).
# NOTE: this is the NO-BUILDING baseline case - turbine + pole only.
turbine_stl = "./constant/triSurface/turbine_final.stl"
pole_stl = "./constant/triSurface/pole_final.stl"

vtk_subset = "./VTK/meshCase_turbine_0.vtm"
turbine_subset = "./VTK/meshCase_turbine_0/boundary/turbine.vtp"

TURBINE_X, TURBINE_Y, TURBINE_Z = 0.447, -3.022, 105.05
ROTOR_RADIUS = 2.5

U_CLIM = [0.0, 15.2]
SCALAR_BAR_ARGS = dict(title="Velocity Magnitude [m/s]", n_labels=5, italic=False,
                       width=0.6, position_x=0.2)  # PyVista's own default (position_x=0.35 with
                       # width=0.6) spans 35%-95% of the window, centered at 65% rather than 50% -
                       # this is what was actually shifting the colorbar right in every render.
                       # position_x=(1-width)/2 centers a bar of this width exactly.


# =============================================================================
# HELPERS
# =============================================================================
def focus_bounds(*meshes, padding=1.4):
    """Camera framing bounds around just the geometry of interest, skipping
    any empty meshes rather than letting them corrupt the box."""
    valid = [m for m in meshes if m.n_points > 0]
    if not valid:
        return None
    b = np.array([m.bounds for m in valid])
    xmin, xmax = b[:, 0].min(), b[:, 1].max()
    ymin, ymax = b[:, 2].min(), b[:, 3].max()
    zmin, zmax = b[:, 4].min(), b[:, 5].max()
    cx, cy, cz = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2
    hx, hy, hz = (xmax - xmin) / 2 * padding, (ymax - ymin) / 2 * padding, (zmax - zmin) / 2 * padding
    return (cx - hx, cx + hx, cy - hy, cy + hy, cz - hz, cz + hz)


def ensure_normals(mesh):
    """foamToVTK boundary patch exports typically don't include point
    normals. smooth_shading (Phong) requires them - without them, some
    renderers produce broken/scattered-looking output instead of a clean
    shaded surface. Compute them explicitly."""
    return mesh.compute_normals(auto_orient_normals=True, consistent_normals=True)


def ensure_point_data(vol, field='U'):
    """Streamline integration needs POINT data. foamToVTK often only writes
    cell data - convert if needed."""
    if field not in vol.point_data and field in vol.cell_data:
        print(f"  -> converting '{field}' from cell_data to point_data")
        vol = vol.cell_data_to_point_data()
    return vol


def make_context_seed(upstream_y, x_extent=45, z_range=(0, 190), nx=9, nz=9):
    """Broad, sparse plane spanning most of the domain cross-section, placed
    just upstream of the geometry. Gives visual context for the overall
    approach flow, separate from the precise rotor-plane seeding below."""
    xs = np.linspace(-x_extent, x_extent, nx)
    zs = np.linspace(z_range[0], z_range[1], nz)
    pts = np.array([[x, upstream_y, z] for x in xs for z in zs])
    return pv.PolyData(pts)


def make_rotor_seed(center, radius, r_res=10, c_res=36):
    """Dense disc exactly matching the rotor swept area - shows precisely
    what reaches the turbine."""
    return pv.Disc(center=center, inner=0.0, outer=radius,
                    normal=(0, 1, 0), r_res=r_res, c_res=c_res)


def trace_streamlines(vol, seed, **kwargs):
    defaults = dict(vectors='U', integration_direction='both',
                     max_time=3000.0, initial_step_length=0.5,
                     terminal_speed=1e-3)
    defaults.update(kwargs)
    return vol.streamlines_from_source(seed, **defaults)


# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading data...")
vol_full = pv.read(vtk_main)[0]
surf_turbine = pv.read(turbine_stl)
surf_pole = pv.read(pole_stl)

vol_full = ensure_point_data(vol_full, 'U')
surf_turbine = ensure_normals(surf_turbine)
surf_pole = ensure_normals(surf_pole)

print(f"vol_full: n_points={vol_full.n_points}, bounds={vol_full.bounds}")
print(f"surf_turbine: n_points={surf_turbine.n_points}, n_faces={surf_turbine.n_faces_strict}")
print(f"surf_pole: n_points={surf_pole.n_points}, n_faces={surf_pole.n_faces_strict}")

print("Loading subset (refined zone) data...")
vol_small = pv.read(vtk_subset)[0]
surf_turbine_sub = pv.read(turbine_stl)  # same clean STL, not the solved-mesh boundary export
vol_small = ensure_point_data(vol_small, 'U')
surf_turbine_sub = ensure_normals(surf_turbine_sub)
print(f"vol_small: n_points={vol_small.n_points}, bounds={vol_small.bounds}")
print(f"surf_turbine_sub: n_points={surf_turbine_sub.n_points}, n_faces={surf_turbine_sub.n_faces_strict}")

# =============================================================================
# SEEDING: broad context plane + dense rotor-disc, combined
# =============================================================================
print("Building seed sources...")
context_seed = make_context_seed(upstream_y=TURBINE_Y - 100, x_extent=45, z_range=(0, 190), nx=9, nz=9)
rotor_seed = make_rotor_seed((TURBINE_X, TURBINE_Y - 8.0, TURBINE_Z), ROTOR_RADIUS, r_res=10, c_res=36)

print("Tracing streamlines...")
stream_context = trace_streamlines(vol_full, context_seed)
stream_rotor = trace_streamlines(vol_full, rotor_seed, max_time=800.0)  # shorter than context - avoids excessive tangling in recirculation loops

print(f"stream_context: n_points={stream_context.n_points}, n_lines={stream_context.n_cells}")
print(f"stream_rotor:   n_points={stream_rotor.n_points}, n_lines={stream_rotor.n_cells}")

# =============================================================================
# PICTURE 1: FULL SCENE - context streamlines (thin, pale) + rotor streamlines
# (bold, colored) + building + turbine
# =============================================================================
print("Creating Picture 1: Full Scene...")
p1 = pv.Plotter(off_screen=True, window_size=[1920, 1080])
p1.enable_parallel_projection()  # orthographic camera: avoids perspective foreshortening skewing the visual centering of a symmetric bounding box (the earlier perspective renders looked left-shifted even when reset_camera's bounds were centered)
p1.set_background("white")

p1.add_mesh(surf_turbine, color="#333333", smooth_shading=True, show_edges=True, edge_color="black")
p1.add_mesh(surf_pole, color="silver", opacity=0.6, smooth_shading=False,
            show_edges=True, edge_color="dimgray")

# Context streamlines: thin, semi-transparent, muted - visual richness without
# competing for attention with the precise rotor-plane result.
if stream_context.n_points > 0:
    p1.add_mesh(stream_context, scalars="U", line_width=1.5, opacity=0.5,
                render_lines_as_tubes=False, cmap="turbo", clim=U_CLIM,
                show_scalar_bar=False)

# Rotor-plane streamlines: bold tubes, full color, this is the scientifically
# meaningful result (what actually reaches the swept rotor area).
# Using an explicit .tube() filter (real-world radius) instead of
# render_lines_as_tubes+line_width (screen-space pixels) - the pixel-based
# version blows up disproportionately large when the camera zooms in near
# the tangled recirculation zone by the building.
if stream_rotor.n_points > 0:
    rotor_tube_radius = 0.12  # meters - tune this directly for thickness
    stream_rotor_tubes = stream_rotor.tube(radius=rotor_tube_radius)
    p1.add_mesh(stream_rotor_tubes, scalars="U", cmap="turbo", clim=U_CLIM,
                scalar_bar_args=SCALAR_BAR_ARGS)

# Draw AND fit the camera to the box the domain actually has, full stop. The
# earlier symmetric +/-150 m slice around the turbine kept the building nicely
# centered, but the real fetch is asymmetric (~196 m upstream, ~400 m
# downstream - see Section 3.2), so streamlines correctly traced across the
# whole domain kept running past both ends of that shrunken box, making the
# "tunnel" look cropped relative to the flow it was supposed to contain.
# Using the true bounds means the box (and hence the canvas) is centered on
# the domain's own center, not on the turbine - the turbine sits a bit left
# of center inside it, which matches the physically real, asymmetric fetch.
b1 = vol_full.bounds
p1.add_mesh(pv.Box(bounds=b1).outline(), color="black", line_width=1)

p1.view_isometric()
p1.reset_camera(bounds=b1)
p1.show(screenshot="full_scene_analysis_nobuilding.png", auto_close=False)
p1.export_gltf("full_scene_nobuilding.glb")
p1.close()

print("\nDone: full_scene_analysis_nobuilding.png")

# =============================================================================
# PICTURE 2: REFINED ZONE ONLY - close-up on turbine, no building.
# Dense rotor-disc streamlines only (no broad context plane needed here -
# this is a tight, detailed look at the swept rotor area and its wake).
# =============================================================================
print("\nCreating Picture 2: Refined Zone Only...")

rotor_seed_sub = make_rotor_seed((TURBINE_X, TURBINE_Y - 8.0, TURBINE_Z), ROTOR_RADIUS, r_res=5, c_res=16)
stream_sub = trace_streamlines(vol_small, rotor_seed_sub, max_time=350.0)
print(f"stream_sub: n_points={stream_sub.n_points}, n_lines={stream_sub.n_cells}")

p2 = pv.Plotter(off_screen=True, window_size=[1920, 1080])

p2.enable_parallel_projection()  # orthographic camera: avoids perspective foreshortening skewing the visual centering of a symmetric bounding box (the earlier perspective renders looked left-shifted even when reset_camera's bounds were centered)
p2.set_background("white")

p2.add_mesh(surf_turbine_sub, color="#333333", smooth_shading=True, show_edges=True, edge_color="black")

if stream_sub.n_points > 0:
    stream_sub_tubes = stream_sub.tube(radius=0.05)  # thinner still - very close camera, fewer/cleaner lines now
    p2.add_mesh(stream_sub_tubes, scalars="U", cmap="turbo", clim=U_CLIM, scalar_bar_args=SCALAR_BAR_ARGS)

FRAME_HALF_RANGE = (20.0, 20.0, 15.0)  # X, Y, Z half-ranges around the turbine
b2 = (TURBINE_X - FRAME_HALF_RANGE[0], TURBINE_X + FRAME_HALF_RANGE[0],
      TURBINE_Y - FRAME_HALF_RANGE[1], TURBINE_Y + FRAME_HALF_RANGE[1],
      TURBINE_Z - FRAME_HALF_RANGE[2], TURBINE_Z + FRAME_HALF_RANGE[2])
p2.add_mesh(pv.Box(bounds=b2).outline(), color="black", line_width=2)

p2.view_isometric()
p2.reset_camera(bounds=b2)
p2.show(screenshot="refined_zone_subset_only_nobuilding.png", auto_close=False)
p2.export_gltf("refined_zone_only_nobuilding.glb")
p2.close()

print("Done: refined_zone_subset_only_nobuilding.png")

# =============================================================================
# PICTURE 3: METHODOLOGY GEOMETRY CLOSE-UPS - no flow data, just the physical
# setup. Two versions: building+turbine together (siting context), and
# turbine alone (design detail, unobstructed).
# =============================================================================
print("\nCreating Picture 3a: Turbine + Pole close-up (geometry only)...")
p3a = pv.Plotter(off_screen=True, window_size=[1920, 1080])
p3a.enable_parallel_projection()  # orthographic camera: avoids perspective foreshortening skewing the visual centering of a symmetric bounding box (the earlier perspective renders looked left-shifted even when reset_camera's bounds were centered)
p3a.set_background("white")

p3a.add_mesh(surf_turbine, color="#333333", smooth_shading=True, show_edges=True, edge_color="black")
p3a.add_mesh(surf_pole, color="silver", opacity=1.0, smooth_shading=False,
             show_edges=True, edge_color="dimgray")  # fully opaque - no streamlines to hide behind it

p3a.view_isometric()
b3a = focus_bounds(surf_pole, surf_turbine, padding=1.15)  # tighter padding than the full-scene shots - this is a close-up
if b3a is not None:
    p3a.reset_camera(bounds=b3a)
else:
    p3a.reset_camera()
p3a.show(screenshot="geometry_pole_turbine_closeup_nobuilding.png", auto_close=False)
p3a.export_gltf("geometry_pole_turbine_closeup_nobuilding.glb")
p3a.close()
print("Done: geometry_pole_turbine_closeup_nobuilding.png")

print("\nCreating Picture 3b: Turbine alone (geometry only)...")
p3b = pv.Plotter(off_screen=True, window_size=[1920, 1080])
p3b.enable_parallel_projection()  # orthographic camera: avoids perspective foreshortening skewing the visual centering of a symmetric bounding box (the earlier perspective renders looked left-shifted even when reset_camera's bounds were centered)
p3b.set_background("white")

p3b.add_mesh(surf_turbine, color="#333333", smooth_shading=True, show_edges=True, edge_color="black")

p3b.view_isometric()
b3b = focus_bounds(surf_turbine, padding=1.3)  # a bit more breathing room since it's the sole subject
if b3b is not None:
    p3b.reset_camera(bounds=b3b)
else:
    p3b.reset_camera()
p3b.show(screenshot="geometry_turbine_only_nobuilding.png", auto_close=False)
p3b.export_gltf("geometry_turbine_only_nobuilding.glb")
p3b.close()
print("Done: geometry_turbine_only_nobuilding.png")
