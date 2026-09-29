# CFD Analysis of Rooftop Wind Turbine Siting

M.Sc. thesis project (Environmental Protection Engineering, Warsaw University of Technology) — a full CFD pipeline built from scratch to evaluate how much usable wind power a small vertical-axis wind turbine (H-Darrieus) actually captures depending on where it is mounted on a building rooftop.

## Motivation

Small rooftop wind turbines are often marketed as a way to add renewable generation to existing buildings, but the wind resource right above a roof is heavily disturbed by the building itself. This project quantifies that disturbance with CFD instead of relying on generic wind-resource assumptions, comparing 3 rooftop siting configurations against an open-terrain baseline.

## Key result

A **~100-fold difference** in captured wind power density between the worst and best rooftop positions tested (**1.9% vs. 195%** of the open-terrain baseline), confirmed with a formal grid convergence study (3 mesh resolutions: 182,298 / 561,061 / 2,324,696 cells).

## Pipeline / tech stack

| Stage | Tool |
|---|---|
| Geometry (building, pole, turbine) | FreeCAD |
| Meshing (background + snappyHexMesh) | Gmsh, OpenFOAM `blockMesh` / `snappyHexMesh` |
| Solver | OpenFOAM (`simpleFoam`, steady RANS), built from source and containerized in Docker |
| Post-processing & visualization | Python (PyVista), ParaView |
| Automation | Bash / Batch / PowerShell mesh-generation scripts, Python comparison scripts |

The whole pipeline — geometry → mesh → solve → post-process — is scripted rather than driven by hand through GUIs, which is what made it practical to re-run for 3 siting configurations and 3 mesh resolutions.

## Repository contents

This repo contains the **authored source** behind the study — scripts and case configuration — not the multi-gigabyte solved simulation output (mesh + field data), which isn't practical or useful to version in git.

```
scripts/
  generate.py          # PyVista post-processing: renders velocity/vorticity fields,
                        # streamlines and geometry context from solved VTK output
  pvScriptMesh.py       # ParaView automation for mesh visualization
  mesh_comparison.py    # Builds the 3-way coarse/medium/fine mesh comparison figure
                        # used in the grid convergence study
  Allmesh / .bat / .ps1 # End-to-end mesh generation (blockMesh -> surface feature
                        # extraction -> snappyHexMesh), cross-platform

docker/
  openfoam-docker        # Official OpenCFD run script for the OpenFOAM Docker image

case/
  system/                # Solver, mesh and numerical scheme configuration
                          # (controlDict, fvSchemes, fvSolution, snappyHexMeshDict, ...)
  constant/triSurface/    # Input CAD geometry (turbine, pole, building/tunnel walls)
  0/                      # Initial and boundary conditions (U, p, k, omega, nut)

results/
  Rendered geometry and flow visualizations produced by scripts/generate.py
```

Not included: solved field data, generated volume meshes (`constant/polyMesh`), simulation logs, and the OpenFOAM source tree itself (built separately from [openfoam.com](https://www.openfoam.com/)) — these are either regenerable from the scripts/config above, or not authored by me.

## Running it

1. Build/pull OpenFOAM (this project used OpenFOAM v2406) — natively or via `docker/openfoam-docker`.
2. From inside `case/`, run `../scripts/Allmesh` to generate the mesh.
3. Run the solver (`simpleFoam`) to steady-state convergence.
4. Use `scripts/generate.py` / `scripts/pvScriptMesh.py` to render results from the solved VTK output.

## Author

Teodor Noga — [linkedin.com/in/teodor-noga-5a58231a9](https://www.linkedin.com/in/teodor-noga-5a58231a9)
