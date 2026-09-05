"""V3 SHG simulator: air | active Nb | glass, with no explicit oxide layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from physics.fresnel import rij
from physics.glass import nlimeglass
from physics.simulator import C, DEFAULT_WAVELENGTH_M, EPS0, _as_thickness_array
from physics.transfer_matrix import column_vector, interface_matrix, propagation_matrix


TOTAL_REFERENCE_THICKNESS_NM = 150.0
"""Measured total thickness used to define the direct V3 Nb-thickness coordinate."""


@dataclass(frozen=True)
class SimulationDiagnosticsV3:
    """Single-thickness V3 intermediates, intentionally excluding oxide terms."""

    n31w: complex
    n32w: complex
    d3_nb_m: float
    phase31w: complex
    phase32w: complex
    m311w: NDArray[np.complex128]
    p31w: NDArray[np.complex128]
    m431w: NDArray[np.complex128]
    t1w: NDArray[np.complex128]
    reflection: complex
    e31w: NDArray[np.complex128]
    emas: complex
    emen: complex
    es2k: NDArray[np.complex128]
    es0k: NDArray[np.complex128]
    m312w: NDArray[np.complex128]
    ml: NDArray[np.complex128]
    m342w: NDArray[np.complex128]
    p3m2w: NDArray[np.complex128]
    mr: NDArray[np.complex128]
    mfact_es: NDArray[np.complex128]
    ms2k: NDArray[np.complex128]
    ps2k: NDArray[np.complex128]
    as2k: complex
    s2k: NDArray[np.complex128]
    eshg_2k: NDArray[np.complex128]
    ms0k: NDArray[np.complex128]
    ps0k: NDArray[np.complex128]
    as0k: complex
    s0k: NDArray[np.complex128]
    eshg_0k: NDArray[np.complex128]
    eshg: NDArray[np.complex128]
    i_4: float
    i_1: float


@dataclass(frozen=True)
class RawSimulationResultV3:
    """Unnormalized V3 intensities and the unchanged MoS2 reference values."""

    I_4: NDArray[np.float64]
    I_1: NDArray[np.float64]
    IMoS24: float
    IMoS21: float
    diagnostics: SimulationDiagnosticsV3 | None = None


@dataclass(frozen=True)
class SimulationResultV3:
    """Normalized V3 transmission and reflection values."""

    T: NDArray[np.float64]
    R: NDArray[np.float64]
    I_4: NDArray[np.float64]
    I_1: NDArray[np.float64]
    IMoS24: float
    IMoS21: float
    diagnostics: SimulationDiagnosticsV3 | None = None


def _parameter_values_v3(
    p: Iterable[float] | NDArray[np.floating],
) -> tuple[float, float, complex, complex]:
    """Extract exactly the six V3 parameters without optimization constraints."""

    parameters = np.asarray(p, dtype=np.float64).reshape(-1)
    if parameters.size != 6:
        raise ValueError("V3 p must contain exactly six parameters.")
    return (
        10 ** parameters[0],
        float(parameters[1]),
        complex(parameters[2], parameters[3]),
        complex(parameters[4], parameters[5]),
    )


def _nb_thickness_m(measured_total_nm: float, d3_nb_nm: float) -> float:
    """Map a legacy total-thickness datum to the direct V3 Nb-layer thickness.

    ``d3_nb_nm`` is the Nb thickness at the stated 150 nm total-thickness
    reference.  Replacing ``d_oxide`` in the legacy relation by
    ``150 - d3_nb_nm`` preserves the unchanged experimental thickness axis
    while leaving no oxide layer, index, interface, or propagation matrix.
    """

    return (measured_total_nm - (TOTAL_REFERENCE_THICKNESS_NM - d3_nb_nm)) * 1e-9


def shg_3layers_v3(
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    p: Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
    *,
    diagnostics: bool = False,
) -> RawSimulationResultV3:
    """Evaluate V3's direct air | Nb | glass transfer-matrix structure.

    The nonlinear-source terms and MoS2 normalization are retained literally
    from the validated four-layer model.  Only the oxide interfaces and
    propagation matrices are absent.
    """

    thicknesses = _as_thickness_array(thickness_nm)
    if diagnostics and thicknesses.size != 1:
        raise ValueError("diagnostics=True requires exactly one thickness value.")

    k0 = 2 * np.pi / wavelength_m
    chi2, d3_nb_nm, n31w, n32w = _parameter_values_v3(p)
    n11w = 1.0 + 0j
    n12w = 1.0 + 0j
    n41w = complex(nlimeglass(wavelength_m))
    n42w = complex(nlimeglass(wavelength_m / 2))

    i_4 = np.zeros(thicknesses.shape, dtype=np.float64)
    i_1 = np.zeros(thicknesses.shape, dtype=np.float64)
    diagnostic_result: SimulationDiagnosticsV3 | None = None

    for index, dnm in enumerate(thicknesses):
        d3_nb = _nb_thickness_m(float(dnm), d3_nb_nm)
        phase31w = n31w * k0 * d3_nb
        phase32w = n32w * 2 * k0 * d3_nb

        m311w = interface_matrix(n31w, n11w)
        p31w = propagation_matrix(phase31w)
        m431w = interface_matrix(n41w, n31w)
        t1w = m431w @ p31w @ m311w
        reflection = -t1w[1, 0] / t1w[1, 1]

        e11w = column_vector(1, reflection)
        e31w = m311w @ e11w
        emas = e31w[0, 0]
        emen = e31w[1, 0]
        es2k = column_vector(emas**2, emen**2)
        es0k = column_vector(emas * emen, emen * emas)

        m312w = interface_matrix(n32w, n12w)
        ml = m312w
        l22 = ml[1, 1]
        l12 = ml[0, 1]
        m342w = interface_matrix(n32w, n42w)
        p3m2w = propagation_matrix(-phase32w)
        mr = p3m2w @ m342w
        r11 = mr[0, 0]
        r21 = mr[1, 0]
        mfact_es = (1 / (r11 * l22 - r21 * l12)) * np.array(
            [[l22, -l12], [r21, -r11]], dtype=np.complex128
        )

        ns2k = n31w
        ms2k = interface_matrix(n32w, ns2k)
        ps2k = propagation_matrix(ns2k * 2 * k0 * d3_nb)
        as2k = 1 / (ns2k**2 - n32w**2)
        s2k = as2k * (p3m2w @ ms2k @ ps2k - ms2k)
        eshg_2k = chi2 * (mfact_es @ s2k @ es2k)

        ns0k = 0.0 + 0j
        ms0k = interface_matrix(n32w, ns0k)
        ps0k = propagation_matrix(ns0k * 2 * k0 * d3_nb)
        as0k = -1 / (n32w**2)
        s0k = as0k * (p3m2w @ ms0k @ ps0k - ms0k)
        eshg_0k = chi2 * (mfact_es @ s0k @ es0k)

        eshg = eshg_2k + eshg_0k
        i_4[index] = float(np.real(eshg[0, 0] * np.conjugate(eshg[0, 0])))
        i_1[index] = float(np.real(eshg[1, 0] * np.conjugate(eshg[1, 0])))

        if diagnostics:
            diagnostic_result = SimulationDiagnosticsV3(
                n31w=n31w,
                n32w=n32w,
                d3_nb_m=d3_nb,
                phase31w=phase31w,
                phase32w=phase32w,
                m311w=m311w,
                p31w=p31w,
                m431w=m431w,
                t1w=t1w,
                reflection=reflection,
                e31w=e31w,
                emas=emas,
                emen=emen,
                es2k=es2k,
                es0k=es0k,
                m312w=m312w,
                ml=ml,
                m342w=m342w,
                p3m2w=p3m2w,
                mr=mr,
                mfact_es=mfact_es,
                ms2k=ms2k,
                ps2k=ps2k,
                as2k=as2k,
                s2k=s2k,
                eshg_2k=eshg_2k,
                ms0k=ms0k,
                ps0k=ps0k,
                as0k=as0k,
                s0k=s0k,
                eshg_0k=eshg_0k,
                eshg=eshg,
                i_4=i_4[index],
                i_1=i_1[index],
            )

    k2w = 2 * k0
    w1 = 2 * np.pi * (C / wavelength_m)
    sig_s = -1j * (4.97 - 1) * EPS0 * w1 * 0.65e-9
    rs = rij(n11w, n41w, sig_s)
    e_mos2_4 = -1j * k2w * (1 + rs) ** 2 * (n12w / (n12w + n42w))
    i_mos2_4 = float(np.real(e_mos2_4 * np.conjugate(e_mos2_4)))
    r412w = rij(n42w, n12w, 0)
    e_mos2_1 = 1j * (k2w / 2) * (1 + rs) ** 2 * (1 + r412w)
    i_mos2_1 = float(np.real(e_mos2_1 * np.conjugate(e_mos2_1)))
    return RawSimulationResultV3(i_4, i_1, i_mos2_4, i_mos2_1, diagnostic_result)


def shg_mos2_ratios_v3(
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    p: Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return V3 normalized transmission and reflection."""

    raw = shg_3layers_v3(thickness_nm, p, wavelength_m)
    return np.real(raw.I_4 / raw.IMoS24), np.real(raw.I_1 / raw.IMoS21)


def simulate_v3(
    p: Iterable[float] | NDArray[np.floating],
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
    *,
    diagnostics: bool = False,
) -> SimulationResultV3:
    """Simulate V3 without applying objective or optimization constraints."""

    raw = shg_3layers_v3(thickness_nm, p, wavelength_m, diagnostics=diagnostics)
    return SimulationResultV3(
        T=np.real(raw.I_4 / raw.IMoS24),
        R=np.real(raw.I_1 / raw.IMoS21),
        I_4=raw.I_4,
        I_1=raw.I_1,
        IMoS24=raw.IMoS24,
        IMoS21=raw.IMoS21,
        diagnostics=raw.diagnostics,
    )
