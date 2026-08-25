function rij = rij(n1,n2,sigS)


eps0 = 8.8541878176E-12; %F/m ==> C/(Vm)
c= 3E8; %m/s

Z0 = 1/(eps0*c);

rij = (n1 - n2 - Z0*sigS)/(n1 + n2 + Z0*sigS);

end