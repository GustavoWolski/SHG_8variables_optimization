function [I_4, I_1, IMoS24, IMoS21, debug] = shg_4layers(Md3, p, lambda)
% Verbatim extraction of the physical core from FIT_SHG_norm_MoS2_T_fit_4layers.
% The optional fifth output only exposes already calculated values for validation.

    if nargout >= 5 && length(Md3) ~= 1
        error('Debug output requires exactly one Md3 value.');
    end
    debug = [];

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
        Es0k = [Emas.*Emen;
                Emen.*Emas];

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

    if nargout >= 5
        debug = struct('d2', d2, 'd3', d3, 'n21w', n21w, 'n22w', n22w, ...
            'n31w', n31w, 'n32w', n32w, 'fase21w', fase21w, ...
            'fase31w', fase31w, 'fase22w', fase22w, 'fase32w', fase32w, ...
            'M211w', M211w, 'P21w', P21w, 'M321w', M321w, 'P31w', P31w, ...
            'M431w', M431w, 'T1w', T1w, 'r', r, 'E31w', E31w, ...
            'Emas', Emas, 'Emen', Emen, 'Es2k', Es2k, 'Es0k', Es0k, ...
            'M212w', M212w, 'P22w', P22w, 'M322w', M322w, 'ML', ML, ...
            'M342w', M342w, 'P3m2w', P3m2w, 'MR', MR, ...
            'MfactEs', MfactEs, 'Ms2k', Ms2k, 'Ps2k', Ps2k, ...
            'As2k', As2k, 'S2k', S2k, 'ESHG2k', ESHG2k, ...
            'Ms0k', Ms0k, 'Ps0k', Ps0k, 'As0k', As0k, 'S0k', S0k, ...
            'ESHG0k', ESHG0k, 'ESHG', ESHG, 'I_4', I_4(1), 'I_1', I_1(1));
    end
end
