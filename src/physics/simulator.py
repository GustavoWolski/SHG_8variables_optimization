"""Faithful Python port of the MATLAB four-layer SHG simulator core."""

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from physics.fresnel import rij, tij
from physics.glass import nlimeglass
from physics.transfer_matrix import column_vector, interface_matrix, propagation_matrix


DEFAULT_WAVELENGTH_M = 1560e-9
EPS0 = 8.8541878176e-12
C = 3e8


@dataclass(frozen=True)
class SimulationDiagnostics:
    """Intermediate values from one thickness evaluation; disabled by default."""

    n21w: complex
    n22w: complex
    n31w: complex
    n32w: complex
    d2_m: float
    d3_m: float
    phase21w: complex
    phase31w: complex
    phase22w: complex
    phase32w: complex
    m211w: NDArray[np.complex128]
    p21w: NDArray[np.complex128]
    m321w: NDArray[np.complex128]
    p31w: NDArray[np.complex128]
    m431w: NDArray[np.complex128]
    t1w: NDArray[np.complex128]
    reflection: complex
    e31w: NDArray[np.complex128]
    emas: complex
    emen: complex
    es2k: NDArray[np.complex128]
    es0k: NDArray[np.complex128]
    m212w: NDArray[np.complex128]
    p22w: NDArray[np.complex128]
    m322w: NDArray[np.complex128]
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
class RawSimulationResult:
    """Unnormalized SHG intensities and MATLAB's MoS2 reference intensities."""

    I_4: NDArray[np.float64]
    I_1: NDArray[np.float64]
    IMoS24: float
    IMoS21: float
    diagnostics: SimulationDiagnostics | None = None


@dataclass(frozen=True)
class SimulationResult:
    """Theoretical normalized transmission and reflection from the four-layer model."""

    T: NDArray[np.float64]
    R: NDArray[np.float64]
    I_4: NDArray[np.float64]
    I_1: NDArray[np.float64]
    IMoS24: float
    IMoS21: float
    diagnostics: SimulationDiagnostics | None = None


def _as_thickness_array(thickness_nm: float | Iterable[float] | NDArray[np.floating]) -> NDArray[np.float64]:
    """Flatten scalar, row, or column thickness inputs as MATLAB's ``length`` loop does."""

    return np.asarray(thickness_nm, dtype=np.float64).reshape(-1)


def _parameter_values(
    p: Iterable[float] | NDArray[np.floating],
) -> tuple[float, float, float, complex, complex, complex]:
    """Extract the eight MATLAB parameters without applying physical constraints."""

    parameters = np.asarray(p, dtype=np.float64).reshape(-1)
    if parameters.size < 8:
        raise ValueError("p must contain at least the eight MATLAB model parameters.")

    chi2 = 10 ** parameters[0]
    d2_nm = parameters[1]
    d2 = d2_nm * 1e-9
    n21w = complex(parameters[2])
    n22w = complex(parameters[3])
    n31w = complex(parameters[4], parameters[5])
    n32w = complex(parameters[6], parameters[7])
    return chi2, d2_nm, d2, n21w, n22w, n31w, n32w


def shg_4layers(
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    p: Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
    *,
    diagnostics: bool = False,
) -> RawSimulationResult:
    """Port MATLAB ``shg_4layers`` with its explicit thickness loop.

    ``thickness_nm`` is MATLAB's ``Md3`` (the measured total thickness), not
    the net active-layer thickness. Set ``diagnostics=True`` only for a single
    thickness to retrieve intermediate fields and matrices.
    """

    thicknesses = _as_thickness_array(thickness_nm)
    if diagnostics and thicknesses.size != 1:
        raise ValueError("diagnostics=True requires exactly one thickness value.")

    k0 = 2 * np.pi / wavelength_m
    chi2, d2_nm, d2, n21w, n22w, n31w, n32w = _parameter_values(p)

    n11w = 1.0 + 0j
    n12w = 1.0 + 0j
    n41w = complex(nlimeglass(wavelength_m))
    lambda_shg = wavelength_m / 2
    n42w = complex(nlimeglass(lambda_shg))

    i_4 = np.zeros(thicknesses.shape, dtype=np.float64)
    i_1 = np.zeros(thicknesses.shape, dtype=np.float64)
    diagnostic_result: SimulationDiagnostics | None = None

    for index, dnm in enumerate(thicknesses):
        d3 = (dnm - d2_nm) * 1e-9

        phase21w = n21w * k0 * d2
        phase31w = n31w * k0 * d3
        phase22w = n22w * 2 * k0 * d2
        phase32w = n32w * 2 * k0 * d3

        m211w = interface_matrix(n21w, n11w)
        p21w = propagation_matrix(phase21w)
        m321w = interface_matrix(n31w, n21w)
        p31w = propagation_matrix(phase31w)
        m431w = interface_matrix(n41w, n31w)

        t1w = m431w @ p31w @ m321w @ p21w @ m211w
        reflection = -t1w[1, 0] / t1w[1, 1]

        e11w = column_vector(1, reflection)
        e31w = m321w @ p21w @ m211w @ e11w
        emas = e31w[0, 0]
        emen = e31w[1, 0]

        es2k = column_vector(emas**2, emen**2)
        es0k = column_vector(emas * emen, emen * emas)

        m212w = interface_matrix(n22w, n12w)
        p22w = propagation_matrix(phase22w)
        m322w = interface_matrix(n32w, n22w)
        ml = m322w @ p22w @ m212w
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
        ps2k = propagation_matrix(ns2k * 2 * k0 * d3)
        as2k = 1 / (ns2k**2 - n32w**2)
        s2k = as2k * (p3m2w @ ms2k @ ps2k - ms2k)
        eshg_2k = chi2 * (mfact_es @ s2k @ es2k)

        ns0k = 0.0 + 0j
        ms0k = interface_matrix(n32w, ns0k)
        ps0k = propagation_matrix(ns0k * 2 * k0 * d3)
        as0k = -1 / (n32w**2)
        s0k = as0k * (p3m2w @ ms0k @ ps0k - ms0k)
        eshg_0k = chi2 * (mfact_es @ s0k @ es0k)

        eshg = eshg_2k + eshg_0k
        i_4[index] = float(np.real(eshg[0, 0] * np.conjugate(eshg[0, 0])))
        i_1[index] = float(np.real(eshg[1, 0] * np.conjugate(eshg[1, 0])))

        if diagnostics:
            diagnostic_result = SimulationDiagnostics(
                n21w=n21w,
                n22w=n22w,
                n31w=n31w,
                n32w=n32w,
                d2_m=float(d2),
                d3_m=float(d3),
                phase21w=phase21w,
                phase31w=phase31w,
                phase22w=phase22w,
                phase32w=phase32w,
                m211w=m211w,
                p21w=p21w,
                m321w=m321w,
                p31w=p31w,
                m431w=m431w,
                t1w=t1w,
                reflection=reflection,
                e31w=e31w,
                emas=emas,
                emen=emen,
                es2k=es2k,
                es0k=es0k,
                m212w=m212w,
                p22w=p22w,
                m322w=m322w,
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
    dmos2 = 0.65e-9
    sig_s = -1j * (4.97 - 1) * EPS0 * w1 * dmos2

    rs = rij(n11w, n41w, sig_s)
    e_mos2_4 = -1j * k2w * (1 + rs) ** 2 * (n12w / (n12w + n42w))
    i_mos2_4 = float(np.real(e_mos2_4 * np.conjugate(e_mos2_4)))

    r412w = rij(n42w, n12w, 0)
    e_mos2_1 = 1j * (k2w / 2) * (1 + rs) ** 2 * (1 + r412w)
    i_mos2_1 = float(np.real(e_mos2_1 * np.conjugate(e_mos2_1)))

    return RawSimulationResult(i_4, i_1, i_mos2_4, i_mos2_1, diagnostic_result)


def shg_mos2_ratios(
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    p: Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return ``Tnorm, Rnorm`` exactly as MATLAB ``shg_mos2_ratios`` does."""

    raw = shg_4layers(thickness_nm, p, wavelength_m)
    return np.real(raw.I_4 / raw.IMoS24), np.real(raw.I_1 / raw.IMoS21)


def simulate(
    p: Iterable[float] | NDArray[np.floating],
    thickness_nm: float | Iterable[float] | NDArray[np.floating],
    wavelength_m: float = DEFAULT_WAVELENGTH_M,
    *,
    diagnostics: bool = False,
) -> SimulationResult:
    """Simulate theoretical normalized transmission and reflection for ``p``.

    No bounds, dispersion constraints, objective function, or optimization
    logic is applied here. This function only evaluates the physical model.
    """

    raw = shg_4layers(thickness_nm, p, wavelength_m, diagnostics=diagnostics)
    return SimulationResult(
        T=np.real(raw.I_4 / raw.IMoS24),
        R=np.real(raw.I_1 / raw.IMoS21),
        I_4=raw.I_4,
        I_1=raw.I_1,
        IMoS24=raw.IMoS24,
        IMoS21=raw.IMoS21,
        diagnostics=raw.diagnostics,
    )
