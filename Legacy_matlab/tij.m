function tij = tij(n1,n2,sigS)


eps0 = 8.8541878176E-12; %F/m ==> C/(Vm)
c= 3E8; %m/s

Z0 = 1/(eps0*c);

tij = 2*n1/(n1 + n2 + Z0*sigS);

end