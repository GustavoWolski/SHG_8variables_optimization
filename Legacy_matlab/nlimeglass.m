%%  DBA 13092019
%%  Esta funcion calcula el indice de refraccion para el lme glass
%%  equacion extraida de: https://refractiveindex.info/?shelf=3d&book=glass&page=soda-lime-clear
%%  n=1.5130−0.003169λ2+0.003962λ−2
%%
%%  unidades de lambda en la eq son micrometros
%%  unidades de entrada de lambda son m


function nglass = nlimeglass(lambda)

   l = lambda/1E-6;
    
   nglass = 1.5130 - 0.003169*l^2 + 0.003962/(l^2);

end
