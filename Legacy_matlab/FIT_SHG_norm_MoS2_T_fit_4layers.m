function FIT_SHG_norm_MoS2_T_fit_4layers()
% se calcula para 4 camadas 1 (ar) | 2 (oxido) | 3 (Nonlinear layer) | 4 (glass)
% 01092025 se normaliza por el valor de MoS2 sobre el mismo substrato

close all;
clc;
if exist('graphics_toolkit', 'file')
    graphics_toolkit('gnuplot');
end
setenv('GNUTERM', 'png');
if exist('pkg', 'file') || exist('pkg', 'builtin')
    try
        pkg load optim;
    catch
    end
end

lambda = 1560E-9;

% DBA 04092025 [d T R] medidos
M = [65E-9 2192.89 621.17
     80E-9 2133.53 876.81
     100E-9 2522.53 1137.68
     150E-9 3857.56 731.88
     190E-9 3649.85 1021.73
     250E-9 1988.13 920.289
     300E-9 359.05 1521.73
     400E-9 59.64 1072.46
     500E-9 37.68 1057.97
     600E-9 16.17 1028.98];

% Parameter vector:
% p = [log10(chi) d2_nm n21w n22w real(n31w) imag(n31w) real(n32w) imag(n32w)]
p0 = [0, 10, 2.10, 2.43, 2.04, 0.70, 1.42, 0.80];

% Broad bounds: allow the optimizer to move beyond the previous active
% limits n21w = 5 and real(n31w) = 1.
lb = [-12, 1.00, 0.10, 0.10, 0.10, 0.000, 0.10, 0.000];
ub = [ 12, 100., 10.0, 10.0, 10.0, 10.00, 10.0, 10.00];
fit_weights = [1, 1]; % [T R]; increase the first value to prioritize T.
peak_weight_T = 200; % Extra penalty to match T at the experimental peak.

% d3 is the independent layer-thickness variable.
% Fit chi, d2, and all refractive-index parameters using T and R simultaneously.
pstarts = [p0;
           0, 12, 1.80, 2.20, 2.04, 0.70, 1.42, 0.80;
           0, 15, 2.40, 3.00, 1.80, 1.20, 1.80, 0.40;
           0, 20, 3.00, 3.50, 1.50, 3.00, 2.20, 0.20;
           0, 25, 3.40, 3.90, 1.20, 4.50, 2.00, 0.10;
           0, 40, 4.00, 4.50, 1.20, 2.00, 1.50, 0.30;
           0, 55, 4.50, 5.00, 1.10, 1.50, 1.30, 0.40];

best_err = Inf;
pfit = p0;
for istart = 1:size(pstarts, 1)
    ptry0 = pstarts(istart, :);
    ptry0(1) = best_chi_for_shape(ptry0, M, lambda, lb, ub, fit_weights, peak_weight_T);
    ptry = fit_selected_parameters(ptry0, 1:length(p0), M, lambda, lb, ub, fit_weights, peak_weight_T);
    err_try = fit_error(ptry, M, lambda, fit_weights, peak_weight_T);
    fprintf('start %d weighted objective = %.6g\n', istart, err_try);
    if err_try < best_err
        best_err = err_try;
        pfit = ptry;
    end
end

% 1. Open the file for writing ('w' creates a new file or overwrites an existing one)
fid = fopen('best_fit_parameters_T_R.txt', 'w');

% Check if the file opened successfully
if fid == -1
    error('File could not be opened. Check your folder permissions.');
end

% 2. Write the values to the file by adding 'fid' as the first argument
fprintf(fid, '\nBest fit parameters:\n');
fprintf(fid, 'chi  = %.8g\n', 10^pfit(1));
fprintf(fid, 'log10(chi) = %.8g\n', pfit(1));
fprintf(fid, 'd2   = %.4f nm\n', pfit(2));
fprintf(fid, 'fit weights [T R] = [%.6g %.6g]\n', fit_weights(1), fit_weights(2));
fprintf(fid, 'T peak weight = %.6g\n', peak_weight_T);
fprintf(fid, 'n21w = %.6f\n', pfit(3));
fprintf(fid, 'n22w = %.6f\n', pfit(4));
fprintf(fid, 'n31w = %.6f + i*%.6f\n', pfit(5), pfit(6));
fprintf(fid, 'n32w = %.6f + i*%.6f\n\n', pfit(7), pfit(8));

% 3. Always close the file when you are done!
fclose(fid);

disp('Results successfully saved to best_fit_parameters_T_R.txt');

Md3_exp = M(:,1)'/1E-9;
Md3 = ceil(pfit(2)):1:600;

[Tfit_exp, Rfit_exp] = shg_mos2_ratios(Md3_exp, pfit, lambda);
[Tfit, Rfit] = shg_mos2_ratios(Md3, pfit, lambda);

Texp = M(:,2);
Rexp = M(:,3);
Terr = sum(((Texp - Tfit_exp(:))/max(Texp)).^2);
Rerr = sum(((Rexp - Rfit_exp(:))/max(Rexp)).^2);

fprintf('Weighted fit error T  = %.6g\n', Terr);
fprintf('Weighted fit error R  = %.6g\n', Rerr);
fprintf('Weighted fit error TR = %.6g\n\n', Terr + Rerr);

figure('visible', 'off');
plot(Md3_exp, Texp, '*k', Md3, Tfit, 'r-', ...
     Md3_exp, Rexp, 'ok', Md3, Rfit, 'b-', 'linewidth', 2);
xlabel('d_3 (nm)', 'fontsize', 20);
ylabel('\chi_{norm}', 'fontsize', 20);
legend({'T exp','T fit: I_4/I_{MoS2,4}', ...
        'R exp','R fit: I_1/I_{MoS2,1}'}, ...
       'fontsize', 12, 'location', 'northeast');
grid on;
print('-dpng', '-r300', 'SHG_fit_T_R.png');

vsave = [M(:,1)/1E-9 Texp Tfit_exp(:) Rexp Rfit_exp(:)];
save('SHG_fit_T_R.dat', 'vsave', '-ascii');
end

function pfit = fit_selected_parameters(pstart, idx, M, lambda, lb, ub, fit_weights, peak_weight_T)
    if exist('nonlin_residmin', 'file')
        fixed = true(size(pstart));
        fixed(idx) = false;
        settings = optimset('lbound', lb(:), 'ubound', ub(:), ...
                            'fixed', fixed(:), 'MaxIter', 250, ...
                            'TolFun', 1E-8, 'Display', 'off');
        residuals = @(p) fit_residuals(p(:).', M, lambda, fit_weights, peak_weight_T);
        [pfit, ~, cvg, outp] = nonlin_residmin(residuals, pstart(:), settings);
        pfit = pfit(:).';
        pfit = min(max(pfit, lb), ub);
        fprintf('nonlin_residmin stage: cvg = %d, iterations = %d\n', cvg, outp.niter);
        return;
    end

    x0 = pstart(idx);
    options = optimset('maxiter', 5000, 'maxfunevals', 50000, ...
                       'tolx', 1E-8, 'tolfun', 1E-10);
    objective = @(x) bounded_fit_error(x, idx, pstart, M, lambda, lb, ub, fit_weights, peak_weight_T);
    xfit = fminsearch(objective, x0, options);

    pfit = pstart;
    pfit(idx) = xfit;
    pfit = min(max(pfit, lb), ub);
end

function resid = fit_residuals(p, M, lambda, fit_weights, peak_weight_T)
    Md3_exp = M(:,1)'/1E-9;
    [Tteo, Rteo] = shg_mos2_ratios(Md3_exp, p, lambda);

    resid = [sqrt(fit_weights(1))*(M(:,2) - Tteo(:))/max(M(:,2));
             sqrt(fit_weights(2))*(M(:,3) - Rteo(:))/max(M(:,3));
             sqrt(peak_weight_T)*peak_T_residual(M, Tteo)];
end

function err = bounded_fit_error(x, idx, pbase, M, lambda, lb, ub, fit_weights, peak_weight_T)
    p = pbase;
    p(idx) = x;

    below = max(lb - p, 0);
    above = max(p - ub, 0);
    scale = max(abs(ub - lb), 1);
    penalty = 1E5*sum((below./scale).^2 + (above./scale).^2);

    p = min(max(p, lb), ub);
    err = fit_error(p, M, lambda, fit_weights, peak_weight_T) + penalty;
end

function err = fit_error(p, M, lambda, fit_weights, peak_weight_T)
    Md3_exp = M(:,1)'/1E-9;
    [Tteo, Rteo] = shg_mos2_ratios(Md3_exp, p, lambda);

    Texp = M(:,2);
    Rexp = M(:,3);
    err = fit_weights(1)*sum(((Texp - Tteo(:))/max(Texp)).^2) + ...
          fit_weights(2)*sum(((Rexp - Rteo(:))/max(Rexp)).^2) + ...
          peak_weight_T*peak_T_residual(M, Tteo)^2;
end

function chi = best_chi_for_shape(p, M, lambda, lb, ub, fit_weights, peak_weight_T)
    pshape = p;
    pshape(1) = 0;
    [Tunit, Runit] = shg_mos2_ratios(M(:,1)'/1E-9, pshape, lambda);

    y = [sqrt(fit_weights(1))*M(:,2)/max(M(:,2));
         sqrt(fit_weights(2))*M(:,3)/max(M(:,3));
         sqrt(peak_weight_T)];
    a = [sqrt(fit_weights(1))*Tunit(:)/max(M(:,2));
         sqrt(fit_weights(2))*Runit(:)/max(M(:,3));
         sqrt(peak_weight_T)*Tunit(experimental_T_peak_index(M))/max(M(:,2))];

    alpha = max((a'*y)/(a'*a), 0);
    chi = log10(max(sqrt(alpha), realmin));
    chi = min(max(chi, lb(1)), ub(1));
end

function resid = peak_T_residual(M, Tteo)
    ipeak = experimental_T_peak_index(M);
    resid = (M(ipeak, 2) - Tteo(ipeak))/max(M(:,2));
end

function ipeak = experimental_T_peak_index(M)
    [~, ipeak] = max(M(:,2));
end

function [Tnorm, Rnorm] = shg_mos2_ratios(Md3, p, lambda)
    [I_4, I_1, IMoS24, IMoS21] = shg_4layers(Md3, p, lambda);
    Tnorm = real(I_4(:).'/IMoS24);
    Rnorm = real(I_1(:).'/IMoS21);
end

function [I_4, I_1, IMoS24, IMoS21] = shg_4layers(Md3, p, lambda)
    k0 = 2*pi/lambda;

    chi2 = 10^p(1);
    d2 = p(2)*1E-9;
    n21w = p(3);
    n22w = p(4);
    n31w = p(5) + 1i*p(6);
    n32w = p(7) + 1i*p(8);

    n11w = 1;
    n12w = 1;
    n41w = nlimeglass(lambda);
    lambshg = lambda/2;
    n42w = nlimeglass(lambshg);

    I_4 = zeros(size(Md3));
    I_1 = zeros(size(Md3));

    ic = 1;
    while ic <= length(Md3)
        dnm = Md3(ic);
        d3 = (dnm - p(2))*1E-9;

        fase21w = n21w*k0*d2;
        fase31w = n31w*k0*d3;
        fase22w = n22w*2*k0*d2;
        fase32w = n32w*2*k0*d3;

        %%%%%%%%%%%%%% calculo de r (overall) %%%%%%%%
        r211w = rij(n21w,n11w,0);
        t211w = tij(n21w,n11w,0);

        M211w = (1/t211w)*[1     r211w;
                           r211w 1];

        P21w = [exp(1i*fase21w)  0;
                0                exp(-1i*fase21w)];

        r321w = rij(n31w,n21w,0);
        t321w = tij(n31w,n21w,0);

        M321w = (1/t321w)*[1     r321w;
                           r321w 1];

        P31w = [exp(1i*fase31w)  0;
                0                exp(-1i*fase31w)];

        r431w = rij(n41w,n31w,0);
        t431w = tij(n41w,n31w,0);

        M431w = (1/t431w)*[1     r431w;
                           r431w 1];

        T1w = M431w*P31w*M321w*P21w*M211w;
        r = -T1w(2,1)/T1w(2,2);

        E11w = [1;
                r];

        E31w = M321w*P21w*M211w*E11w;

        Emas = E31w(1,1);
        Emen = E31w(2,1);

        Es2k = [Emas.^2;
                Emen.^2];

        % Zero-wave-vector nonlinear source from the two counterpropagating
        % fundamental fields: E+E- and E-E+.
        Es0k = [Emas.*Emen;
                Emen.*Emas];

        %%%%%%% SHG %%%%%%%%%%%%%%%%%%%%%%%%
        r212w = rij(n22w,n12w,0);
        t212w = tij(n22w,n12w,0);

        M212w = (1/t212w)*[1     r212w;
                           r212w 1];

        P22w = [exp(1i*fase22w)  0;
                0                exp(-1i*fase22w)];

        r322w = rij(n32w,n22w,0);
        t322w = tij(n32w,n22w,0);

        M322w = (1/t322w)*[1     r322w;
                           r322w 1];

        ML = M322w*P22w*M212w;
        L22 = ML(2,2);
        L12 = ML(1,2);

        r342w = rij(n32w,n42w,0);
        t342w = tij(n32w,n42w,0);

        M342w = (1/t342w)*[1     r342w;
                           r342w 1];

        P3m2w = [exp(-1i*fase32w) 0;
                 0                exp(1i*fase32w)];

        MR = P3m2w*M342w;

        R11 = MR(1,1);
        R21 = MR(2,1);

        MfactEs = (1/(R11*L22 - R21*L12))*[L22 -L12;
                                           R21 -R11];

        ns2k = n31w;

        rs2k = rij(n32w,ns2k,0);
        ts2k = tij(n32w,ns2k,0);
        fases2k = ns2k*2*k0*d3;

        Ms2k = (1/ts2k)*[1     rs2k;
                         rs2k 1];

        Ps2k = [exp(1i*fases2k)  0;
                0                exp(-1i*fases2k)];

        As2k = 1/(ns2k^2 - n32w^2);

        S2k = As2k*(P3m2w*Ms2k*Ps2k - Ms2k);
        ESHG2k = chi2*MfactEs*S2k*Es2k;

        %%%%% segundo termo: source with ns = 0
        ns0k = 0;

        rs0k = rij(n32w,ns0k,0);
        ts0k = tij(n32w,ns0k,0);
        fases0k = ns0k*2*k0*d3;

        Ms0k = (1/ts0k)*[1     rs0k;
                         rs0k 1];

        Ps0k = [exp(1i*fases0k)  0;
                0                exp(-1i*fases0k)];

        As0k = -1/(n32w^2);
        S0k = As0k*(P3m2w*Ms0k*Ps0k - Ms0k);
        ESHG0k = chi2*MfactEs*S0k*Es0k;

        ESHG = ESHG2k + ESHG0k;

        % ESHG(1): field leaving through layer 4 (transmission).
        % ESHG(2): field leaving through layer 1 (reflection).
        I_4(ic) = real(ESHG(1,1)*conj(ESHG(1,1)));
        I_1(ic) = real(ESHG(2,1)*conj(ESHG(2,1)));

        ic = ic + 1;
    end

    k2w = 2*k0;
    c = 3E8;
    eps0 = 8.8541878176E-12;
    w1 = 2*pi*(c/lambda);
    dmos2 = 0.65E-9;
    sigS = -1i*(4.97 - 1)*eps0*w1*dmos2;

    rs = rij(n11w,n41w,sigS);

    EMoS24 = -1i*k2w*(1 + rs)^2*(n12w/(n12w + n42w));
    IMoS24 = real(EMoS24.*conj(EMoS24));

    r412w = rij(n42w,n12w,0);
    EMoS21 = 1i*(k2w/2)*(1 + rs)^2*(1 + r412w);
    IMoS21 = real(EMoS21.*conj(EMoS21));
end
