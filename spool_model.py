"""Physics model for the pulled-spool desktop simulator."""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Optional

G = 9.8


@dataclass
class Parameters:
    theta_deg: float = 30.0
    inner_radius_cm: float = 5.0
    outer_radius_cm: float = 10.0
    mass_kg: float = 1.0
    force_n: float = 1.5
    mu_static: float = 0.50
    inertia_ratio: float = 0.30  # I / (M * Ro^2)

    @property
    def inner_radius_m(self) -> float:
        return self.inner_radius_cm / 100.0

    @property
    def outer_radius_m(self) -> float:
        return self.outer_radius_cm / 100.0

    @property
    def inertia(self) -> float:
        ro = self.outer_radius_m
        return self.inertia_ratio * self.mass_kg * ro * ro


@dataclass
class SimulationResult:
    valid: bool
    message: str
    theta_c_deg: Optional[float] = None
    acceleration_m_s2: Optional[float] = None
    normal_force_n: Optional[float] = None
    friction_x_n: Optional[float] = None
    max_static_friction_n: Optional[float] = None
    state: str = "INVALID"
    rolling_direction: str = "-"
    friction_direction: str = "-"
    note: str = ""


def calculate(params: Parameters) -> SimulationResult:
    """
    Calculate the exact no-slip solution and classify the current state.

    x is the direction of the horizontal component of the pulling force.
    For theta > 90 degrees, the spool is turned around, matching Fig. 5
    in the project reference paper.
    """
    ri = params.inner_radius_m
    ro = params.outer_radius_m
    mass = params.mass_kg
    force = params.force_n
    theta_deg = params.theta_deg
    mu_s = params.mu_static
    inertia = params.inertia

    if ri <= 0 or ro <= 0:
        return SimulationResult(False, "반지름은 0보다 커야 합니다.")
    if ri >= ro:
        return SimulationResult(False, "안쪽 반지름 Ri는 바깥쪽 반지름 Ro보다 작아야 합니다.")
    if mass <= 0:
        return SimulationResult(False, "질량은 0보다 커야 합니다.")
    if force < 0:
        return SimulationResult(False, "당기는 힘 F는 0 이상이어야 합니다.")
    if mu_s < 0:
        return SimulationResult(False, "정지 마찰계수 μs는 0 이상이어야 합니다.")
    if inertia <= 0:
        return SimulationResult(False, "관성모멘트 I는 0보다 커야 합니다.")
    if not 0 <= theta_deg <= 180:
        return SimulationResult(False, "각도 θ는 0°부터 180° 사이여야 합니다.")

    theta = math.radians(theta_deg)
    theta_c = math.degrees(math.acos(ri / ro))
    normal = mass * G - force * math.sin(theta)
    max_static = max(mu_s * normal, 0.0)

    # At 90°, horizontal pulling is zero. The reference paper excludes this
    # point because its definition of 'forward' uses the horizontal component.
    if abs(theta_deg - 90.0) < 1e-7:
        state = "LIFT-OFF" if normal <= 0 else "90° EXCLUDED"
        return SimulationResult(
            valid=True,
            message="계산 완료",
            theta_c_deg=theta_c,
            normal_force_n=normal,
            max_static_friction_n=max_static,
            state=state,
            note="90°에서는 수평 당김 성분이 0이므로 전진 방향의 정의가 제외됩니다.",
        )

    denominator = mass + inertia / (ro * ro)

    if theta_deg < 90.0:
        acceleration = force * (math.cos(theta) - ri / ro) / denominator
        friction_x = -force * (mass * ri * ro + inertia * math.cos(theta)) / (
            mass * ro * ro + inertia
        )
    else:
        acceleration = force * (ri / ro - math.cos(theta)) / denominator
        friction_x = force * (mass * ri * ro + inertia * math.cos(theta)) / (
            mass * ro * ro + inertia
        )

    if normal <= 0:
        state = "LIFT-OFF"
        note = "수직항력 N이 0 이하이므로 바닥 접촉이 유지되지 않습니다."
    elif abs(friction_x) > max_static + 1e-9:
        state = "SLIDING"
        note = "필요한 정지 마찰력이 μsN을 초과합니다. 이후의 미끄러짐 운동은 별도 모델이 필요합니다."
    elif abs(acceleration) < 1e-8:
        state = "AT REST"
        note = "임계각 부근입니다. 약하게 당길 때 스풀은 이동하지 않습니다."
    else:
        state = "ROLLING WITHOUT SLIPPING"
        note = "정지 마찰 조건을 만족하므로 구름 운동 식을 적용할 수 있습니다."

    if acceleration > 1e-8:
        rolling_direction = "RIGHT / FORWARD"
    elif acceleration < -1e-8:
        rolling_direction = "LEFT / BACKWARD"
    else:
        rolling_direction = "NO TRANSLATION"

    if friction_x > 1e-8:
        friction_direction = "RIGHT"
    elif friction_x < -1e-8:
        friction_direction = "LEFT"
    else:
        friction_direction = "ZERO"

    return SimulationResult(
        valid=True,
        message="계산 완료",
        theta_c_deg=theta_c,
        acceleration_m_s2=acceleration,
        normal_force_n=normal,
        friction_x_n=friction_x,
        max_static_friction_n=max_static,
        state=state,
        rolling_direction=rolling_direction,
        friction_direction=friction_direction,
        note=note,
    )
