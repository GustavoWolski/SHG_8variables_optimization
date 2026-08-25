function export_reference_cases(output_dir)
% Export deterministic four-layer SHG reference values without optimization.
% Run from MATLAB/Octave: export_reference_cases

    if nargin < 1
        legacy_dir = fileparts(mfilename('fullpath'));
        repository_dir = fileparts(legacy_dir);
        output_dir = fullfile(repository_dir, 'tests', 'reference');
    end
    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end

    lambda = 1560E-9;
    thickness_nm = [65 80 100 150 190 250 300 400 500 600];
    thickness_m = thickness_nm * 1E-9;

    case_names = {'case_1_p0', 'case_2_valid_a', 'case_3_valid_b'};
    p_cases = [
        0, 10, 2.10, 2.43, 2.04, 0.70, 1.42, 0.80;
        0.5, 8, 2.00, 2.40, 2.20, 0.30, 2.80, 0.60;
       -2.0, 15, 3.50, 4.10, 4.00, 1.20, 5.00, 2.10
    ];

    write_parameters(fullfile(output_dir, 'matlab_reference_parameters.csv'), case_names, p_cases);

    fid = fopen(fullfile(output_dir, 'matlab_reference_cases.csv'), 'w');
    if fid == -1
        error('Could not open matlab_reference_cases.csv for writing.');
    end
    fprintf(fid, 'case,thickness_nm,T,R,I_4,I_1,IMoS24,IMoS21\n');

    for icase = 1:size(p_cases, 1)
        p = p_cases(icase, :);
        [T, R] = shg_mos2_ratios(thickness_nm, p, lambda);
        [I_4, I_1, IMoS24, IMoS21] = shg_4layers(thickness_nm, p, lambda);
        for ithickness = 1:length(thickness_nm)
            fprintf(fid, '%s,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n', ...
                case_names{icase}, thickness_nm(ithickness), T(ithickness), R(ithickness), ...
                I_4(ithickness), I_1(ithickness), IMoS24, IMoS21);
        end
    end
    fclose(fid);

    fid = fopen(fullfile(output_dir, 'matlab_reference_intermediates.csv'), 'w');
    if fid == -1
        error('Could not open matlab_reference_intermediates.csv for writing.');
    end
    fprintf(fid, 'case,name,row,column,real,imag\n');
    for icase = 1:size(p_cases, 1)
        [~, ~, ~, ~, debug] = shg_4layers(150, p_cases(icase, :), lambda);
        write_debug_values(fid, case_names{icase}, debug);
    end
    fclose(fid);

    fprintf('MATLAB reference files written to %s\n', output_dir);
end

function write_parameters(filename, case_names, p_cases)
    fid = fopen(filename, 'w');
    if fid == -1
        error('Could not open matlab_reference_parameters.csv for writing.');
    end
    fprintf(fid, 'case,log10_chi,d2_nm,n2_w,n2_2w,re_n3_w,im_n3_w,re_n3_2w,im_n3_2w\n');
    for icase = 1:size(p_cases, 1)
        fprintf(fid, '%s,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n', ...
            case_names{icase}, p_cases(icase, :));
    end
    fclose(fid);
end

function write_debug_values(fid, case_name, debug)
    names = {'d2', 'd3', 'n21w', 'n22w', 'n31w', 'n32w', ...
        'fase21w', 'fase31w', 'fase22w', 'fase32w', ...
        'M211w', 'P21w', 'M321w', 'P31w', 'M431w', 'T1w', 'r', ...
        'E31w', 'Emas', 'Emen', 'Es2k', 'Es0k', ...
        'M212w', 'P22w', 'M322w', 'ML', 'M342w', 'P3m2w', 'MR', ...
        'MfactEs', 'Ms2k', 'Ps2k', 'As2k', 'S2k', 'ESHG2k', ...
        'Ms0k', 'Ps0k', 'As0k', 'S0k', 'ESHG0k', 'ESHG', 'I_4', 'I_1'};
    for iname = 1:length(names)
        value = debug.(names{iname});
        for irow = 1:size(value, 1)
            for icolumn = 1:size(value, 2)
                entry = value(irow, icolumn);
                fprintf(fid, '%s,%s,%d,%d,%.17g,%.17g\n', ...
                    case_name, names{iname}, irow, icolumn, real(entry), imag(entry));
            end
        end
    end
end
