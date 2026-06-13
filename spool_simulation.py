"""
Pulled Spool Simulator
======================
Desktop GUI simulation for Visual Studio or Visual Studio Code.

Run:
    python spool_simulation.py
"""

from __future__ import annotations

import csv
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle

import matplotlib

# The interface and all plot labels are in English. We only make sure the
# minus sign and the few Greek/degree symbols render with a complete font.
matplotlib.rcParams["axes.unicode_minus"] = False

from spool_model import Parameters, SimulationResult, calculate


class SpoolSimulatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pulled Spool Simulator")
        self.root.geometry("1420x900")
        self.root.minsize(1180, 760)

        self.running = False
        self.dt = 0.04
        self.displacement_m = 0.0
        self.velocity_m_s = 0.0
        self.visual_center_x = -0.65

        self.vars = {
            "theta_deg": tk.DoubleVar(value=30.0),
            "inner_radius_cm": tk.DoubleVar(value=5.0),
            "outer_radius_cm": tk.DoubleVar(value=10.0),
            "mass_kg": tk.DoubleVar(value=1.0),
            "force_n": tk.DoubleVar(value=1.5),
            "mu_static": tk.DoubleVar(value=0.50),
            "inertia_ratio": tk.DoubleVar(value=0.30),
        }
        self.value_labels: dict[str, ttk.Label] = {}
        self.summary_vars = {
            "critical": tk.StringVar(value="-"),
            "state": tk.StringVar(value="-"),
            "acceleration": tk.StringVar(value="-"),
            "normal": tk.StringVar(value="-"),
            "friction": tk.StringVar(value="-"),
            "rolling": tk.StringVar(value="-"),
            "friction_direction": tk.StringVar(value="-"),
            "note": tk.StringVar(value="-"),
        }

        self._build_ui()
        self.refresh(reset_motion=True)
        self._tick()

    def _build_ui(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        control = ttk.Frame(self.root, padding=12)
        control.grid(row=0, column=0, sticky="nsw")
        control.columnconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=3)
        main.rowconfigure(1, weight=2)

        ttk.Label(control, text="Pulled Spool Simulator", font=("Arial", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            control,
            text="See how the spool's rolling direction and the\ndirection of friction change with the pulling angle.",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        parameter_box = ttk.LabelFrame(control, text="Inputs", padding=10)
        parameter_box.grid(row=2, column=0, sticky="ew")
        parameter_box.columnconfigure(0, weight=1)

        sliders = [
            ("theta_deg", "Pulling angle theta", 0.0, 180.0),
            ("inner_radius_cm", "Inner radius Ri", 1.0, 14.0),
            ("outer_radius_cm", "Outer radius Ro", 2.0, 20.0),
            ("mass_kg", "Mass M", 0.1, 5.0),
            ("force_n", "Pulling force F", 0.0, 20.0),
            ("mu_static", "Static friction coeff. mu_s", 0.0, 1.5),
            ("inertia_ratio", "Inertia ratio I / (M Ro^2)", 0.05, 1.20),
        ]

        for row, (key, text, low, high) in enumerate(sliders):
            top = ttk.Frame(parameter_box)
            top.grid(row=row * 2, column=0, sticky="ew", pady=(4, 0))
            top.columnconfigure(0, weight=1)
            ttk.Label(top, text=text).grid(row=0, column=0, sticky="w")
            label = ttk.Label(top, text="")
            label.grid(row=0, column=1, sticky="e")
            self.value_labels[key] = label

            ttk.Scale(
                parameter_box,
                variable=self.vars[key],
                from_=low,
                to=high,
                orient="horizontal",
                command=lambda _value: self.refresh(reset_motion=True),
            ).grid(row=row * 2 + 1, column=0, sticky="ew")

        button_frame = ttk.Frame(control)
        button_frame.grid(row=3, column=0, sticky="ew", pady=10)
        for col in range(2):
            button_frame.columnconfigure(col, weight=1)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.toggle_running)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(button_frame, text="Reset", command=self.reset_motion).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        ttk.Button(button_frame, text="Save graph PNG", command=self.save_graph).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=(6, 0)
        )
        ttk.Button(button_frame, text="Save angle-sweep CSV", command=self.save_csv).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=(6, 0)
        )

        summary_box = ttk.LabelFrame(control, text="Results", padding=10)
        summary_box.grid(row=4, column=0, sticky="ew")
        summary_box.columnconfigure(1, weight=1)

        rows = [
            ("Critical angle theta_c", "critical"),
            ("State", "state"),
            ("Acceleration ax", "acceleration"),
            ("Normal force N", "normal"),
            ("Friction fx", "friction"),
            ("Rolling direction", "rolling"),
            ("Friction direction", "friction_direction"),
        ]
        for row, (label_text, key) in enumerate(rows):
            ttk.Label(summary_box, text=label_text).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=2)
            ttk.Label(summary_box, textvariable=self.summary_vars[key], wraplength=230).grid(
                row=row, column=1, sticky="nw", pady=2
            )

        ttk.Separator(summary_box, orient="horizontal").grid(
            row=len(rows), column=0, columnspan=2, sticky="ew", pady=7
        )
        ttk.Label(summary_box, textvariable=self.summary_vars["note"], wraplength=300).grid(
            row=len(rows) + 1, column=0, columnspan=2, sticky="w"
        )

        ttk.Label(
            control,
            text=(
                "Recommended demo values\n"
                "Ri = 5 cm, Ro = 10 cm -> theta_c = 60 deg\n"
                "theta = 30 deg: forward / 60 deg: at rest\n"
                "theta = 75 deg: backward / 120 deg: forward"
            ),
            justify="left",
        ).grid(row=5, column=0, sticky="w", pady=(12, 0))

        simulation_box = ttk.LabelFrame(main, text="Animation", padding=5)
        simulation_box.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        simulation_box.rowconfigure(0, weight=1)
        simulation_box.columnconfigure(0, weight=1)

        self.sim_figure = Figure(figsize=(8.8, 4.4), dpi=100)
        self.sim_ax = self.sim_figure.add_axes([0.06, 0.10, 0.91, 0.84])
        self.sim_canvas = FigureCanvasTkAgg(self.sim_figure, master=simulation_box)
        self.sim_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        graph_box = ttk.LabelFrame(main, text="Acceleration versus pulling angle", padding=5)
        graph_box.grid(row=1, column=0, sticky="nsew")
        graph_box.rowconfigure(0, weight=1)
        graph_box.columnconfigure(0, weight=1)

        self.graph_figure = Figure(figsize=(8.8, 3.3), dpi=100)
        self.graph_ax = self.graph_figure.add_axes([0.09, 0.17, 0.88, 0.76])
        self.graph_canvas = FigureCanvasTkAgg(self.graph_figure, master=graph_box)
        self.graph_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def current_params(self) -> Parameters:
        return Parameters(**{key: var.get() for key, var in self.vars.items()})

    def _update_value_labels(self) -> None:
        p = self.current_params()
        values = {
            "theta_deg": f"{p.theta_deg:.1f}°",
            "inner_radius_cm": f"{p.inner_radius_cm:.1f} cm",
            "outer_radius_cm": f"{p.outer_radius_cm:.1f} cm",
            "mass_kg": f"{p.mass_kg:.2f} kg",
            "force_n": f"{p.force_n:.2f} N",
            "mu_static": f"{p.mu_static:.2f}",
            "inertia_ratio": f"{p.inertia_ratio:.2f}",
        }
        for key, label in self.value_labels.items():
            label.configure(text=values[key])

    def toggle_running(self) -> None:
        self.running = not self.running
        self.start_button.configure(text="Pause" if self.running else "Start")

    def reset_motion(self) -> None:
        self.displacement_m = 0.0
        self.velocity_m_s = 0.0
        self.visual_center_x = -0.65
        self.refresh(reset_motion=False)

    def refresh(self, reset_motion: bool) -> None:
        if reset_motion:
            self.displacement_m = 0.0
            self.velocity_m_s = 0.0
            self.visual_center_x = -0.65

        self._update_value_labels()
        params = self.current_params()
        self.result = calculate(params)
        r = self.result

        if not r.valid:
            self.summary_vars["critical"].set("-")
            self.summary_vars["state"].set("INVALID INPUT")
            self.summary_vars["acceleration"].set("-")
            self.summary_vars["normal"].set("-")
            self.summary_vars["friction"].set("-")
            self.summary_vars["rolling"].set("-")
            self.summary_vars["friction_direction"].set("-")
            self.summary_vars["note"].set(r.message)
        else:
            self.summary_vars["critical"].set(f"{r.theta_c_deg:.2f}°" if r.theta_c_deg is not None else "-")
            self.summary_vars["state"].set(r.state)
            self.summary_vars["acceleration"].set(
                f"{r.acceleration_m_s2:+.4f} m/s²" if r.acceleration_m_s2 is not None else "-"
            )
            self.summary_vars["normal"].set(f"{r.normal_force_n:.4f} N" if r.normal_force_n is not None else "-")
            self.summary_vars["friction"].set(f"{r.friction_x_n:+.4f} N" if r.friction_x_n is not None else "-")
            self.summary_vars["rolling"].set(r.rolling_direction)
            self.summary_vars["friction_direction"].set(r.friction_direction)
            self.summary_vars["note"].set(r.note)

        self.draw_simulation()
        self.draw_graph()

    def _tick(self) -> None:
        if self.running:
            r = getattr(self, "result", None)
            if r and r.valid and r.state == "ROLLING WITHOUT SLIPPING" and r.acceleration_m_s2 is not None:
                self.velocity_m_s += r.acceleration_m_s2 * self.dt
                step = self.velocity_m_s * self.dt
                self.displacement_m += step
                self.visual_center_x += step * 1.8

                if self.visual_center_x > 1.20 or self.visual_center_x < -1.20:
                    self.displacement_m = 0.0
                    self.velocity_m_s = 0.0
                    self.visual_center_x = -0.65 if r.acceleration_m_s2 >= 0 else 0.65

                self.draw_simulation()
        self.root.after(int(self.dt * 1000), self._tick)

    def draw_simulation(self) -> None:
        ax = self.sim_ax
        ax.clear()
        ax.set_xlim(-1.55, 1.55)
        ax.set_ylim(-0.30, 1.75)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")

        p = self.current_params()
        r = getattr(self, "result", calculate(p))

        ground_y = 0.0
        display_ro = 0.43
        display_ri = display_ro * max(0.05, min(p.inner_radius_cm / max(p.outer_radius_cm, 1e-9), 0.95))
        cx, cy = self.visual_center_x, display_ro

        ax.plot([-1.55, 1.55], [ground_y, ground_y], linewidth=2)
        ax.text(-1.49, -0.13, "table", fontsize=10)

        ax.add_patch(Circle((cx, cy), display_ro, fill=False, linewidth=3))
        ax.add_patch(Circle((cx, cy), display_ri, fill=False, linewidth=2))

        phi = -self.displacement_m / max(p.outer_radius_m, 1e-9)
        ax.plot(
            [cx, cx + display_ro * math.cos(phi)],
            [cy, cy + display_ro * math.sin(phi)],
            linewidth=2,
        )
        ax.plot(cx, cy, marker="o", markersize=4)
        ax.text(cx + 0.03, cy + 0.03, "O", fontsize=10)

        theta = math.radians(p.theta_deg)
        if p.theta_deg <= 90.0:
            sx = cx + display_ri * math.sin(theta)
            sy = cy - display_ri * math.cos(theta)
            ux, uy = math.cos(theta), math.sin(theta)
        else:
            alpha = math.radians(180.0 - p.theta_deg)
            sx = cx - display_ri * math.sin(alpha)
            sy = cy + display_ri * math.cos(alpha)
            ux, uy = math.cos(alpha), math.sin(alpha)

        ex, ey = sx + 0.80 * ux, sy + 0.80 * uy
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy), arrowprops={"arrowstyle": "->", "linewidth": 2})
        ax.text(ex + 0.03, ey + 0.03, "F", fontsize=12)
        ax.text(sx + 0.02, sy + 0.02, "S", fontsize=10)

        contact_x = cx
        ax.plot(contact_x, ground_y, marker="o", markersize=4)
        ax.text(contact_x + 0.03, ground_y - 0.12, "P", fontsize=10)

        if r.valid and r.friction_x_n is not None and abs(r.friction_x_n) > 1e-8:
            direction = 1.0 if r.friction_x_n > 0 else -1.0
            ax.annotate(
                "",
                xy=(contact_x + 0.53 * direction, ground_y + 0.035),
                xytext=(contact_x, ground_y + 0.035),
                arrowprops={"arrowstyle": "->", "linewidth": 2},
            )
            ax.text(contact_x + 0.56 * direction, ground_y + 0.08, "friction f", ha="center", fontsize=10)

        if r.valid and r.acceleration_m_s2 is not None and abs(r.acceleration_m_s2) > 1e-8:
            direction = 1.0 if r.acceleration_m_s2 > 0 else -1.0
            ax.annotate(
                "",
                xy=(cx + 0.82 * direction, 1.20),
                xytext=(cx, 1.20),
                arrowprops={"arrowstyle": "->", "linewidth": 2},
            )
            ax.text(cx + 0.42 * direction, 1.27, "motion", ha="center", fontsize=10)

        theta_c_text = f"{r.theta_c_deg:.2f}°" if r.theta_c_deg is not None else "-"
        ax.text(-1.49, 1.64, f"θ = {p.theta_deg:.1f}°     θc = {theta_c_text}     state: {r.state}", fontsize=11)
        ax.text(-1.49, 1.50, "Animation is exact only while rolling without slipping.", fontsize=9)
        self.sim_canvas.draw_idle()

    def draw_graph(self) -> None:
        ax = self.graph_ax
        ax.clear()
        p = self.current_params()

        if p.inner_radius_cm <= 0 or p.outer_radius_cm <= 0 or p.inner_radius_cm >= p.outer_radius_cm:
            ax.text(0.5, 0.5, "Set Ri < Ro to draw the graph.", ha="center", va="center", transform=ax.transAxes)
            self.graph_canvas.draw_idle()
            return

        left_angles = [value * 0.5 for value in range(180)]
        right_angles = [90.5 + value * 0.5 for value in range(180)]
        left_acc = [calculate(Parameters(**{**p.__dict__, "theta_deg": angle})).acceleration_m_s2 for angle in left_angles]
        right_acc = [calculate(Parameters(**{**p.__dict__, "theta_deg": angle})).acceleration_m_s2 for angle in right_angles]

        ax.plot(left_angles, left_acc, label="0° ≤ θ < 90°")
        ax.plot(right_angles, right_acc, label="90° < θ ≤ 180°")
        ax.axhline(0, linewidth=1)
        ax.axvline(90, linewidth=1, linestyle="--", label="90° excluded")

        r = calculate(p)
        if r.theta_c_deg is not None:
            ax.axvline(r.theta_c_deg, linewidth=1, linestyle=":", label=f"θc = {r.theta_c_deg:.1f}°")
        if r.acceleration_m_s2 is not None:
            ax.plot([p.theta_deg], [r.acceleration_m_s2], marker="o", markersize=7)

        ax.set_xlim(0, 180)
        ax.set_xlabel("Pulling angle theta (degrees)")
        ax.set_ylabel("Acceleration ax (m/s^2)")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best", fontsize=8)
        self.graph_canvas.draw_idle()

    def save_graph(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save graph",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile="spool_acceleration_graph.png",
        )
        if filename:
            self.graph_figure.savefig(filename, dpi=180)
            messagebox.showinfo("Saved", f"Graph saved.\n{filename}")

    def save_csv(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
            initialfile="spool_angle_sweep.csv",
        )
        if not filename:
            return

        p = self.current_params()
        fields = [
            "theta_deg", "theta_c_deg", "acceleration_m_s2", "normal_force_n",
            "friction_x_n", "max_static_friction_n", "state",
            "rolling_direction", "friction_direction", "note",
        ]
        with open(filename, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()
            for theta in range(181):
                r = calculate(Parameters(**{**p.__dict__, "theta_deg": float(theta)}))
                writer.writerow({
                    "theta_deg": theta,
                    "theta_c_deg": r.theta_c_deg,
                    "acceleration_m_s2": r.acceleration_m_s2,
                    "normal_force_n": r.normal_force_n,
                    "friction_x_n": r.friction_x_n,
                    "max_static_friction_n": r.max_static_friction_n,
                    "state": r.state,
                    "rolling_direction": r.rolling_direction,
                    "friction_direction": r.friction_direction,
                    "note": r.note,
                })
        messagebox.showinfo("Saved", f"Angle-sweep results saved.\n{filename}")


def main() -> None:
    root = tk.Tk()
    SpoolSimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
