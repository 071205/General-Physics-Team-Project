# Pulled Spool Simulator

Visual and interactive simulation of the pulled spool problem in classical mechanics, with experimental verification.

## Overview

This project reproduces and tests the static-friction model for a spool pulled by a ribbon at various angles, following Carl E. Mungan, "Pulling a Spool," *Phys. Teach.* **61**, 178–181 (2023).

**Authors:**
- Choi Jihun (202611231)
- Lee Jeongwon (202611164)
- Hur Yul (202611240)
- Park Junsung (202611095)

**Course:** General Physics I (BS103A), DGIST, 2026 Spring

## Key Physics

The spool exhibits three distinct rolling behaviors depending on the pulling angle:

- **0° ≤ θ < θc**: Rolls forward (toward the puller)
- **θ = θc**: Does not roll (critical angle: θc = arccos(Ri/Ro))
- **θc < θ < 90°**: Rolls backward (away from the puller) ← counterintuitive!
- **90° < θ ≤ 180°**: Rolls forward again

The critical angle is **θc = arccos(Ri/Ro)**, where the pulling force's line of action passes through the contact point with the table.

## Quick Start

### Windows (Easiest)
1. Download all files from this repository
2. Double-click `run_windows.bat`
3. The simulator will install dependencies and launch automatically

### macOS / Linux / Manual Install

```bash
# Install dependencies
pip install -r requirements.txt

# Run the simulator
python spool_simulation.py
```

## Features

- **Live Animation**: Watch the spool roll, stay put, or reverse direction in real-time
- **Parameter Controls**: Adjust pulling angle, inner/outer radii, mass, force, and friction coefficient
- **Acceleration Graph**: Plot how spool acceleration varies with pulling angle (0° to 180°)
- **State Classification**: Detects rolling without slipping, sliding, or lift-off conditions
- **Export**: Save acceleration vs. angle graphs as PNG or angle-sweep results as CSV

## Recommended Demo Sequence

**Default parameters:** Ri = 5 cm, Ro = 10 cm → θc = 60°

| Angle | Prediction | Observation |
|-------|-----------|-------------|
| 30°   | Forward   | Spool rolls toward you; ribbon winds in |
| 60°   | At rest   | Spool stays in place; cannot roll |
| 75°   | Backward  | Spool rolls away; ribbon unwinds |
| 120°  | Forward   | (Turn spool around) Spool rolls forward again |

Experiment with adjusting **Ri and Ro** to see how the critical angle changes!

## File Structure

```
General-Physics-Team-Project/
├── README.md                       ← You are here
├── spool_simulation.py             ← Main GUI program
├── spool_model.py                  ← Physics calculations
├── requirements.txt                ← Python dependencies
├── run_windows.bat                 ← Windows launcher
├── Experiment1 - small angle.mp4   ← Exp 1: rolls forward (theta < theta_c)
├── Experiment1 - critical angle.mp4 ← Exp 1: stays put (theta = theta_c)
├── Experiment1 - large angle.mp4   ← Exp 1: rolls backward (theta_c < theta < 90)
├── Experiment2 - shorter than R.mp4 ← Exp 2: acting radius < Ro
├── Experiment2 - same with R.mp4    ← Exp 2: acting radius = Ro
└── Experiment2 - longer than R.mp4  ← Exp 2: acting radius > Ro
```

## Experiment Videos

The experiment recordings are included in this repository (the `.mp4` files above).
Click any video file in the file list to play it in the browser.

### Experiment 1: Rolling Direction vs. Pulling Angle
Demonstrates that the spool's rolling direction reverses as the pulling angle crosses the critical angle: it rolls toward us at a small angle, stays put at the critical angle, and rolls away at an intermediate angle.

### Experiment 2: Effective Acting Radius
Shows that varying the radius at which the string acts—independent of pulling angle—produces the same three regimes by changing the torque about the contact point.

## Physics Model Details

The simulator solves the no-slip equations of motion exactly:

**Newton's Second Law (Translation):**
```
F cos(θ) - f = M ax
```

**Newton's Second Law (Rotation about center):**
```
Ro f - Ri F = I ax / Ro
```

where:
- F = pulling force (N)
- θ = pulling angle (degrees)
- f = static friction force (N)
- M = spool mass (kg)
- Ro = outer contact radius (m)
- Ri = inner axle radius (m)
- I = moment of inertia (kg⋅m²)
- ax = center-of-mass acceleration (m/s²)

**Eliminating friction gives the acceleration:**
```
ax = F (cos θ - cos θc) / (M + I/Ro²)
```

where θc = arccos(Ri/Ro) is the critical angle.

The sign of the acceleration determines rolling direction:
- ax > 0: rolls forward
- ax = 0: does not roll (at θc)
- ax < 0: rolls backward

## State Classifications

- **ROLLING WITHOUT SLIPPING**: The predicted no-slip solution is valid
- **AT REST**: Near the critical angle; spool does not move under gentle pulling
- **SLIDING**: Required friction exceeds μs × N; spool would slip
- **LIFT-OFF**: Normal force N ≤ 0; spool would leave the table

## Troubleshooting

### "ModuleNotFoundError: No module named 'matplotlib'"
Run:
```bash
pip install matplotlib
```

### Simulator won't start on Windows
Try opening Command Prompt in this folder and running:
```bash
python spool_simulation.py
```

### Graph not displaying
Make sure Ri < Ro in the input parameters.

## Paper Reference

**Carl E. Mungan** (2023). "Pulling a Spool." *The Physics Teacher*, 61(3), 178–181.  
https://doi.org/10.1119/5.0042450

## Project Report

See the full experimental report and theoretical analysis:
- English: `spool_report.pdf`
- Korean: `spool_report_ko.pdf`

## License

Educational use. DGIST 2026.

---

**Questions or Issues?**

Check the report or experiment videos for detailed explanations of the physics and experimental methods.
