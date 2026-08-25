function [Tnorm, Rnorm] = shg_mos2_ratios(Md3, p, lambda)
% Verbatim extraction of the original local MATLAB function for reuse in exports.
    [I_4, I_1, IMoS24, IMoS21] = shg_4layers(Md3, p, lambda);
    Tnorm = real(I_4(:).'/IMoS24);
    Rnorm = real(I_1(:).'/IMoS21);
end
