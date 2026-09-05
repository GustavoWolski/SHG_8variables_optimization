# Equações e Intuição Física 

> **Objetivo deste documento:** transformar as equações usadas no modelo em anotações de estudo.
>
> Para cada equação:
> - **O que faz?**
> - **Qual é a equação?**
> - **O que representa cada termo?**
> - **O que entra?**
> - **O que sai?**
> - **Qual é a intuição física?**
> - **Onde aparece no projeto?**
>
> As fórmulas estão escritas no formato LaTeX compatível com Obsidian.

---

# Visão geral

O modelo trabalha com ondas eletromagnéticas que atravessam uma estrutura multicamada.

A ideia central é acompanhar duas componentes do campo:

- $E^+$: onda propagando no sentido positivo;
- $E^-$: onda propagando no sentido negativo.

Em cada camada, essas ondas:

1. propagam;
2. encontram interfaces;
3. são parcialmente refletidas;
4. são parcialmente transmitidas.

O método de matriz de transferência organiza essas operações usando vetores e matrizes $2\times2$.

No código atual, o processo é realizado primeiro na frequência fundamental $\omega$ e depois em $2\omega$ para calcular a resposta de segundo harmônico.

---

# Atualização V3 — pilha direta ar | Nb | vidro

As equações numeradas abaixo descrevem a pilha V2 preservada. Para o V3, o
óxido deixa de existir como meio óptico: não há seus índices, interfaces ou
matrizes de propagação. O campo continua sendo gerado na camada ativa/Nb e as
fontes não lineares, as intensidades e a normalização por MoS$_2$ não mudam.

A coordenada direta de espessura é $d_{3,\mathrm{Nb}}\in[130,150]$ nm. Para
preservar o eixo experimental $D$ do modelo anterior, a espessura que entra
nas fases de Nb é

$$
d_{\mathrm{Nb}}(D)=D-\left(150\ \mathrm{nm}-d_{3,\mathrm{Nb}}\right).
$$

O valor entre parênteses é somente a substituição algébrica da relação
$d_{\mathrm{total}}=d_{\mathrm{oxide}}+d_{\mathrm{Nb}}$ na referência de
150 nm; ele não reintroduz uma camada de óxido na matriz.

Na frequência fundamental, a estrutura V3 é:

$$
T_{\omega,V3}=M_{43,\omega}P_{3,\omega}M_{31,\omega},
\qquad
\mathbf{E}_{3,\omega}=M_{31,\omega}\mathbf{E}_{1,\omega}.
$$

Em $2\omega$, o bloco à esquerda da fonte é apenas a interface direta:

$$
M_{L,V3}=M_{31,2\omega}.
$$

O bloco à direita, as matrizes de fonte $2k$ e $0k$, a soma coerente dos
campos, $I=|E|^2$, e as normalizações $T=I_4/I_{\mathrm{MoS2},4}$ e
$R=I_1/I_{\mathrm{MoS2},1}$ permanecem os mesmos. Os dois índices reais de
Nb são coordenadas independentes no V3; não há restrição de dispersão normal.

---

# Equação 1 — Campo elétrico dentro de uma camada

## O que faz?

Representa o campo elétrico total em uma posição $z$ dentro de uma camada.

## Equação

$$
E(z)=E^+e^{ikz}+E^-e^{-ikz}
$$

## O que representa cada coisa?

### $E(z)$

Campo elétrico total na posição $z$.

### $E^+$

Amplitude complexa da onda que se propaga no sentido positivo de $z$.

### $E^-$

Amplitude complexa da onda que se propaga no sentido negativo de $z$.

Essa segunda onda normalmente aparece devido às reflexões nas interfaces entre os materiais.

### $k$

Número de onda dentro do material.

Em uma forma simples:

$$
k=nk_0
$$

onde:

$$
k_0=\frac{2\pi}{\lambda}
$$

### $n$

Índice de refração do material.

Ele pode ser complexo:

$$
n=n_r+ik
$$

> Atenção: aqui a letra $k$ também é frequentemente usada para representar o coeficiente de extinção do índice complexo. Para evitar confusão, neste documento chamaremos o número de onda de $k_{\mathrm{onda}}$ quando necessário.

### $z$

Posição dentro da camada.

### $e^{ikz}$

Acumulação de fase da onda que viaja para frente.

### $e^{-ikz}$

Acumulação de fase da onda que viaja para trás.

## O que entra?

- $E^+$
- $E^-$
- índice de refração $n$
- comprimento de onda $\lambda$
- posição $z$

## O que sai?

O campo elétrico total:

$$
E(z)
$$

na posição desejada.

## Intuição

Existem duas ondas dentro da camada:

```text
E+  ───────────────►

E-  ◄───────────────
```

Uma anda para frente e outra para trás.

O campo observado é a soma das duas.

Como elas possuem fase, podem ocorrer:

- interferência construtiva;
- interferência destrutiva;
- máximos;
- mínimos.

Essa interferência é uma das razões pelas quais a intensidade depende fortemente da espessura das camadas.

---

# Equação 2 — Número de onda no vácuo

## O que faz?

Transforma o comprimento de onda em uma quantidade que descreve quanto a fase muda por unidade de distância.

## Equação

$$
k_0=\frac{2\pi}{\lambda}
$$

## O que representa cada coisa?

### $k_0$

Número de onda no vácuo.

Unidade:

$$
\text{rad/m}
$$

### $\lambda$

Comprimento de onda da luz.

No código atual:

$$
\lambda=1560\text{ nm}
$$

## O que entra?

- comprimento de onda $\lambda$

## O que sai?

- número de onda $k_0$

## Intuição

Uma onda acumula uma fase de $2\pi$ radianos ao percorrer um comprimento de onda completo.

Por isso:

$$
\lambda \longrightarrow 2\pi
$$

e:

$$
1\text{ metro}\longrightarrow \frac{2\pi}{\lambda}
$$

radianos de fase.

---

# Equação 3 — Fase acumulada dentro de uma camada

## O que faz?

Calcula quanto a fase da onda muda ao atravessar uma camada de espessura $d$.

## Equação

$$
\phi=nk_0d
$$

ou:

$$
\phi=\frac{2\pi nd}{\lambda}
$$

## O que representa cada coisa?

### $\phi$

Fase acumulada durante a propagação.

### $n$

Índice de refração da camada.

### $k_0$

Número de onda no vácuo.

### $d$

Espessura da camada.

## O que entra?

- $n$
- $\lambda$
- $d$

## O que sai?

- fase $\phi$

## Intuição

Quanto maior a espessura, maior o caminho percorrido e maior a mudança de fase.

Quanto maior o índice de refração, maior também a fase acumulada.

Por isso pequenas alterações em:

$$
n
$$

ou:

$$
d
$$

podem deslocar máximos e mínimos das curvas de transmissão e reflexão.

---

# Equação 4 — Matriz de propagação

## O que faz?

Propaga simultaneamente as componentes $E^+$ e $E^-$ através de uma camada.

## Equação

$$
P=
\begin{bmatrix}
e^{i\phi} & 0\\
0 & e^{-i\phi}
\end{bmatrix}
$$

com:

$$
\phi=nk_0d
$$

## O que entra?

- índice $n$;
- espessura $d$;
- comprimento de onda $\lambda$;
- vetor de campos $[E^+,E^-]^T$.

## O que sai?

As amplitudes dos campos depois da propagação pela camada.

## Intuição

A onda para frente recebe:

$$
e^{i\phi}
$$

enquanto a onda para trás recebe:

$$
e^{-i\phi}
$$

A matriz apenas atualiza a fase das duas ondas.

Representação:

```text
antes                    depois

E+  ─────►    camada     ─────► E+ e^(iφ)

E-  ◄─────               ◄───── E- e^(-iφ)
```

No código aparecem matrizes desse tipo como `P21w`, `P31w`, `P22w` e `P3m2w`.

---

# Equação 5 — Coeficiente de reflexão de uma interface

## O que faz?

Determina a amplitude da onda refletida quando a luz encontra uma interface entre dois materiais.

Para incidência normal e meios simples, a forma de Fresnel é:

$$
r_{ij}=\frac{n_i-n_j}{n_i+n_j}
$$

## O que representa cada coisa?

### $r_{ij}$

Coeficiente de reflexão em amplitude na interface entre os meios $i$ e $j$.

### $n_i$

Índice de refração de um lado da interface.

### $n_j$

Índice de refração do outro lado.

## O que entra?

- $n_i$
- $n_j$

## O que sai?

- coeficiente complexo de reflexão $r_{ij}$

## Intuição

Se os dois materiais possuem índices iguais:

$$
n_i=n_j
$$

então:

$$
r_{ij}=0
$$

e não existe reflexão causada pela diferença de índices.

Quanto maior o contraste óptico entre os materiais, maior tende a ser a reflexão.

> **Observação:** o código encapsula esse cálculo na função `rij(...)`. A expressão exata dessa função não aparece no arquivo principal recebido, portanto esta forma de Fresnel é apresentada aqui como interpretação física padrão e deverá ser conferida quando a implementação de `rij` estiver disponível.

---

# Equação 6 — Coeficiente de transmissão de uma interface

## O que faz?

Determina a amplitude transmitida através da interface.

Para incidência normal em meios simples:

$$
t_{ij}=\frac{2n_i}{n_i+n_j}
$$

A convenção pode variar dependendo da direção adotada no método de matriz de transferência.

## O que entra?

- $n_i$
- $n_j$

## O que sai?

- coeficiente de transmissão em amplitude $t_{ij}$

## Intuição

Na interface, a onda incidente é dividida:

```text
                 transmitida
                    ─────►
                   /
incidente ───────►|
                   \
                    ◄─────
                    refletida
```

> **Observação:** o código utiliza a função `tij(...)`. A fórmula exata e sua convenção devem ser confirmadas quando essa função estiver disponível.

---

# Equação 7 — Matriz de interface

## O que faz?

Representa matematicamente o efeito de uma interface sobre as ondas que viajam nos dois sentidos.

## Equação usada no código

$$
M_{ij}
=
\frac{1}{t_{ij}}
\begin{bmatrix}
1&r_{ij}\\
r_{ij}&1
\end{bmatrix}
$$

## O que entra?

- $r_{ij}$;
- $t_{ij}$;
- vetor de campos.

## O que sai?

Um novo vetor contendo as amplitudes relacionadas através da interface.

## Intuição

A matriz de propagação responde:

> “O que acontece enquanto a onda viaja dentro de um material?”

A matriz de interface responde:

> “O que acontece quando a onda troca de material?”

Portanto:

```text
PROPAGAÇÃO  → P

INTERFACE   → M
```

---

# Equação 8 — Matriz de transferência total

## O que faz?

Combina todas as interfaces e todas as propagações da estrutura em uma única matriz.

No código, para a frequência fundamental:

$$
T_{\omega}
=
M_{43,\omega}
P_{3,\omega}
M_{32,\omega}
P_{2,\omega}
M_{21,\omega}
$$

## O que entra?

Todas as:

- matrizes de interface;
- matrizes de propagação.

## O que sai?

Uma matriz $2\times2$ que representa toda a estrutura multicamada.

## Intuição

Em vez de acompanhar manualmente cada reflexão:

```text
ar → óxido → camada ativa → vidro
```

o método transforma tudo em:

$$
T_{\omega}
$$

que funciona como um resumo matemático de toda a estrutura.

A ordem das matrizes é importante.

---

# Equação 9 — Reflexão total da estrutura

## O que faz?

Obtém o coeficiente global de reflexão a partir da matriz de transferência total.

No código:

$$
r=-\frac{T_{21}}{T_{22}}
$$

onde $T_{21}$ e $T_{22}$ são elementos da matriz total.

## O que entra?

- matriz de transferência total $T$.

## O que sai?

- coeficiente global de reflexão $r$.

## Intuição

Todas as reflexões internas já estão embutidas na matriz total.

Portanto, esse $r$ não representa apenas uma interface.

Ele contém o efeito combinado de:

- reflexão no óxido;
- reflexão na camada ativa;
- reflexão no substrato;
- propagação;
- interferência;
- múltiplas reflexões internas.

---

# Equação 10 — Vetor de campo incidente e refletido
## O que faz?

Representa a condição de entrada do sistema.

No código:

$$
\mathbf{E}_{1,\omega}
=
\begin{bmatrix}
1\\
r
\end{bmatrix}
$$

## O que representa cada coisa?

O primeiro termo:

$$
1
$$

representa a amplitude normalizada da onda incidente.

O segundo:

$$
r
$$

representa a onda refletida.

## O que entra?

- amplitude incidente normalizada;
- coeficiente de reflexão global $r$.

## O que sai?

- vetor de campo na entrada.

## Intuição

A intensidade incidente é usada como referência.

Por isso é conveniente definir:

$$
E_{\text{inc}}=1
$$

e medir os outros campos em relação a ela.

---

# Equação 11 — Campo fundamental dentro da camada ativa

## O que faz?

Calcula as amplitudes das ondas fundamental para frente e para trás dentro da camada ativa.

No código:

$$
\mathbf{E}_{3,\omega}
=
M_{32,\omega}
P_{2,\omega}
M_{21,\omega}
\mathbf{E}_{1,\omega}
$$

e:

$$
\mathbf{E}_{3,\omega}
=
\begin{bmatrix}
E^+\\
E^-
\end{bmatrix}
$$

## O que entra?

- campo incidente;
- reflexão global;
- matrizes das interfaces anteriores;
- propagação no óxido.

## O que sai?

- $E^+$ dentro da camada ativa;
- $E^-$ dentro da camada ativa.

## Intuição

Essa é uma etapa fundamental porque a geração não linear depende do campo que realmente existe **dentro do material**, e não apenas do campo que chegou externamente à amostra.

---

# Equação 12 — Fonte não linear associada a $2k$

## O que faz?

Constrói termos quadráticos a partir do campo fundamental.

No código:

$$
\mathbf{E}_{s,2k}
=
\begin{bmatrix}
(E^+)^2\\
(E^-)^2
\end{bmatrix}
$$

## O que entra?

- $E^+$;
- $E^-$.

## O que sai?

- termos quadráticos associados às ondas fundamentais contrapropagantes.

## Intuição

Na geração de segundo harmônico, a resposta não linear é proporcional ao quadrado do campo fundamental.

De maneira simplificada:

$$
P^{(2)}\propto\chi^{(2)}E^2
$$

Por isso aparecem:

$$
(E^+)^2
$$

e:

$$
(E^-)^2.
$$

---

# Equação 13 — Fonte não linear de vetor de onda zero

## O que faz?

Inclui o termo cruzado entre as duas ondas fundamentais que viajam em sentidos opostos.

No código:

$$
\mathbf{E}_{s,0}
=
\begin{bmatrix}
E^+E^-\\
E^-E^+
\end{bmatrix}
$$

## O que entra?

- $E^+$;
- $E^-$.

## O que sai?

- termos cruzados da fonte não linear.

## Intuição

Ao elevar o campo total ao quadrado:

$$
(E^+ + E^-)^2
$$

aparecem três tipos de termos:

$$
(E^+)^2
$$

$$
(E^-)^2
$$

e:

$$
2E^+E^-.
$$

O código trata separadamente os termos associados às ondas individuais e o termo cruzado.

---

# Equação 14 — Polarização não linear de segunda ordem

## O que faz?

Representa a origem física da geração de segundo harmônico.

Forma conceitual:

$$
P^{(2)}(2\omega)
=
\varepsilon_0
\chi^{(2)}
E^2(\omega)
$$

## O que representa cada coisa?

### $P^{(2)}(2\omega)$

Polarização não linear que oscila na frequência $2\omega$.

### $\varepsilon_0$

Permissividade elétrica do vácuo.

### $\chi^{(2)}$

Susceptibilidade não linear de segunda ordem.

### $E(\omega)$

Campo elétrico na frequência fundamental.

## O que entra?

- campo fundamental $E(\omega)$;
- susceptibilidade $\chi^{(2)}$.

## O que sai?

- fonte de polarização na frequência $2\omega$.

## Intuição

Se:

$$
E(\omega)\sim\cos(\omega t)
$$

então:

$$
E^2(\omega)\sim\cos^2(\omega t)
$$

e:

$$
\cos^2(\omega t)
=
\frac{1}{2}
+
\frac{1}{2}\cos(2\omega t)
$$

Portanto, o termo quadrático naturalmente contém uma componente que oscila em:

$$
2\omega.
$$

Essa é a origem do segundo harmônico.

---

# Equação 15 — Comprimento de onda do segundo harmônico

## O que faz?

Relaciona o comprimento de onda fundamental ao comprimento de onda correspondente a $2\omega$.

## Equação

$$
\lambda_{2\omega}
=
\frac{\lambda_{\omega}}{2}
$$

No modelo atual:

$$
\lambda_{\omega}=1560\text{ nm}
$$

portanto:

$$
\lambda_{2\omega}=780\text{ nm}
$$

## Intuição

Como:

$$
f_{2\omega}=2f_{\omega}
$$

e:

$$
c=f\lambda
$$

dobrar a frequência reduz pela metade o comprimento de onda no vácuo.

---

# Equação 16 — Índice de refração complexo

## O que faz?

Representa simultaneamente propagação e absorção no material.

## Equação

Uma notação comum é:

$$
\tilde{n}=n+i\kappa
$$

## O que representa cada coisa?

### $n$

Parte real do índice de refração.

Está relacionada principalmente à velocidade de fase da onda dentro do material.

### $\kappa$

Parte imaginária ou coeficiente de extinção.

Está relacionada à atenuação da onda dentro do material.

## O que entra?

- $n$;
- $\kappa$.

## O que sai?

- índice complexo $\tilde n$.

## Intuição

A parte real controla principalmente:

> “Como a fase da onda evolui?”

A parte imaginária controla principalmente:

> “Quanto a onda é atenuada enquanto se propaga?”

No projeto, ambas serão parâmetros importantes da otimização.

---

# Equação 17 — Restrição de dispersão normal

## O que faz?

Impõe uma condição física sobre os índices reais recuperados pela otimização.

Na dispersão normal adotada no projeto:

$$
n(\omega)<n(2\omega)
$$

## Para a camada 2

Os índices reais do óxido são coordenadas independentes, cada uma no
intervalo fechado $[1,6]$. Não há condição de ordenação para esta camada.

## Para a camada 3

$$
\operatorname{Re}(n_{3,\omega})
<
\operatorname{Re}(n_{3,2\omega})
$$

## O que entra?

- índices candidatos produzidos pelo algoritmo.

## O que sai?

- solução fisicamente válida ou inválida.

## Intuição

Para a camada 3, como $2\omega$ possui frequência maior que $\omega$, a
condição adotada para a região de dispersão normal exige que o índice real
aumente com a frequência. Esta condição não é imposta ao óxido.

Uma forma de garantir isso automaticamente na otimização é:

$$
n(2\omega)=n(\omega)+\Delta n
$$

com:

$$
\Delta n>0.
$$

---

# Equação 18 — Campo total de segundo harmônico

## O que faz?

Soma as duas contribuições de fonte não linear calculadas separadamente pelo modelo.

No código:

$$
\mathbf{E}_{SHG}
=
\mathbf{E}_{SHG,2k}
+
\mathbf{E}_{SHG,0k}
$$

## O que entra?

- contribuição associada a $2k$;
- contribuição associada ao termo cruzado de vetor de onda zero.

## O que sai?

Um vetor com as amplitudes do campo de segundo harmônico que sai pelos dois lados da estrutura.

## Intuição

Existem diferentes contribuições físicas para a geração não linear.

O campo final observado é a soma coerente dessas contribuições.

Como são campos complexos, suas fases importam.

As contribuições podem reforçar ou cancelar parcialmente umas às outras.

---

# Equação 19 — Intensidade a partir do campo

## O que faz?

Converte a amplitude complexa do campo calculado em uma quantidade proporcional à intensidade.

No código:

$$
I=E E^*=|E|^2
$$

onde $E^*$ é o complexo conjugado de $E$.

Para o lado da transmissão:

$$
I_4=
|E_{SHG,1}|^2
$$

Para o lado da reflexão:

$$
I_1=
|E_{SHG,2}|^2
$$

## O que entra?

- campo complexo $E$.

## O que sai?

- intensidade real e não negativa.

## Intuição

O detector não mede diretamente a fase complexa do campo.

A intensidade está relacionada ao módulo quadrado:

$$
|E|^2.
$$

---

# Equação 20 — Transmissão normalizada

## O que faz?

Normaliza a intensidade transmitida calculada utilizando a referência de MoS$_2$ adotada pelo código.

## Equação

$$
T_{\text{norm}}
=
\frac{I_4}{I_{\mathrm{MoS2},4}}
$$

## O que entra?

- intensidade calculada no lado transmitido $I_4$;
- intensidade de referência $I_{\mathrm{MoS2},4}$.

## O que sai?

- transmissão normalizada $T_{\text{norm}}$.

## Intuição

Em vez de comparar apenas uma intensidade absoluta, o modelo compara a resposta da estrutura com uma referência.

Essa é a quantidade posteriormente comparada com os pontos experimentais de transmissão.

---

# Equação 21 — Reflexão normalizada

## O que faz?

Normaliza a intensidade refletida calculada utilizando a referência adotada pelo modelo.

## Equação

$$
R_{\text{norm}}
=
\frac{I_1}{I_{\mathrm{MoS2},1}}
$$

## O que entra?

- intensidade refletida $I_1$;
- intensidade de referência $I_{\mathrm{MoS2},1}$.

## O que sai?

- reflexão normalizada $R_{\text{norm}}$.

## Intuição

É o equivalente, para o lado refletido, da normalização realizada na transmissão.

---

# Equação 22 — Erro da transmissão

## O que faz?

Mede o quanto a curva teórica de transmissão está distante dos dados experimentais.

Uma forma correspondente à lógica atual do código é:

$$
J_T
=
\sum_{i=1}^{N}
\left(
\frac{
T_i^{exp}-T_i^{teo}
}{
\max(T^{exp})
}
\right)^2
$$

## O que entra?

- $T^{exp}$;
- $T^{teo}$.

## O que sai?

Um único número:

$$
J_T\geq0.
$$

Quanto menor, melhor.

## Intuição

Se teoria e experimento forem iguais em todos os pontos:

$$
T_i^{exp}=T_i^{teo}
$$

então:

$$
J_T=0.
$$

---

# Equação 23 — Erro da reflexão

## O que faz?

Mede o quanto a reflexão teórica está distante da reflexão experimental.

## Equação

$$
J_R
=
\sum_{i=1}^{N}
\left(
\frac{
R_i^{exp}-R_i^{teo}
}{
\max(R^{exp})
}
\right)^2
$$

## O que entra?

- $R^{exp}$;
- $R^{teo}$.

## O que sai?

$$
J_R\geq0.
$$

Quanto menor, melhor.

---

# Equação 24 — Função objetivo conjunta

## O que faz?

Transforma o ajuste simultâneo de transmissão e reflexão em um único problema de minimização.

## Equação

$$
J(\mathbf p)
=
w_TJ_T(\mathbf p)
+
w_RJ_R(\mathbf p)
$$

Inicialmente:

$$
w_T=w_R=1.
$$

Portanto:

$$
J=J_T+J_R.
$$

## O que entra?

O vetor de parâmetros:

$$
\mathbf p
$$

e os dados experimentais de $T$ e $R$.

## O que sai?

Um único valor:

$$
J.
$$

Esse é o valor que o algoritmo de otimização tentará minimizar.

## Intuição

O algoritmo não sabe física por conta própria.

Ele simplesmente recebe uma combinação de parâmetros e pergunta ao simulador:

> “Quão ruim é esta solução?”

A função objetivo responde com $J$.

```text
parâmetros
    │
    ▼
simulador físico
    │
    ├──► T teórico
    │
    └──► R teórico
          │
          ▼
     comparar com
      experimento
          │
          ▼
       JT + JR
          │
          ▼
          J
```

Quanto menor $J$, melhor a combinação de parâmetros.

---

# Equação 25 — Vetor otimizado

## O que faz?

Define matematicamente o objetivo final do projeto.

## Equação

$$
\mathbf p^*
=
\arg\min_{\mathbf p\in\Omega}
J(\mathbf p)
$$

## O que representa cada coisa?

### $\mathbf p$

Vetor contendo os oito parâmetros:

$$
\mathbf{p} =
[
\log_{10}(\chi),
d_2,
n_{2,\omega},
n_{2,2\omega},
\operatorname{Re}(n_{3,\omega}),
\operatorname{Im}(n_{3,\omega}),
\operatorname{Re}(n_{3,2\omega}),
\operatorname{Im}(n_{3,2\omega})
]
$$

### $\Omega$

Região fisicamente permitida.

Inclui, entre outras restrições:

$$
0\leq d_2\leq20\text{ nm}
$$

$$
0\leq\operatorname{Im}(n)\leq4
$$

e:

$$
n(\omega)<n(2\omega).
$$

### $\arg\min$

Significa:

> “Encontre os valores dos parâmetros que produzem o menor valor possível da função objetivo.”

## O que entra?

- espaço de busca;
- restrições;
- simulador;
- função objetivo.

## O que sai?

A melhor combinação encontrada:

$$
\mathbf p^*.
$$

---

# Fluxo completo das equações

Uma forma simplificada de enxergar todo o modelo é:

```text
λ
│
▼
k0 = 2π/λ
│
▼
n + espessura
│
▼
fase φ = n k0 d
│
├───────────────┐
▼               ▼
propagação P    interfaces M
│               │
└───────┬───────┘
        ▼
matriz de transferência
        │
        ▼
E+ e E- dentro da camada ativa
        │
        ▼
fontes não lineares
        │
        ▼
campo em 2ω
        │
        ▼
|E|²
        │
   ┌────┴────┐
   ▼         ▼
 transmissão reflexão
   T         R
   │         │
   ▼         ▼
  JT        JR
   └────┬────┘
        ▼
      J = JT + JR
        │
        ▼
   OTIMIZADOR
        │
        ▼
 novos parâmetros
        │
        └────────────► repetir
```

---

# Resumo rápido para revisão

| Equação | Pergunta que responde |
|---|---|
| $E(z)=E^+e^{ikz}+E^-e^{-ikz}$ | Qual é o campo dentro da camada? |
| $k_0=2\pi/\lambda$ | Quanto a fase varia espacialmente? |
| $\phi=nk_0d$ | Quanta fase é acumulada na camada? |
| $P$ | Como a onda se propaga pela camada? |
| $r_{ij}$ | Quanto é refletido em uma interface? |
| $t_{ij}$ | Quanto é transmitido pela interface? |
| $M_{ij}$ | Como representar a interface matricialmente? |
| $T_\omega$ | Como representar toda a multicamada? |
| $E^+,E^-$ | Quais campos existem dentro da camada ativa? |
| $P^{(2)}\propto\chi^{(2)}E^2$ | De onde vem o segundo harmônico? |
| $E_{SHG}$ | Qual campo de segundo harmônico é gerado? |
| $I=|E|^2$ | Qual é a intensidade correspondente ao campo? |
| $T_{\text{norm}}$ | Qual é a transmissão normalizada? |
| $R_{\text{norm}}$ | Qual é a reflexão normalizada? |
| $J_T$ | Quão ruim está o ajuste de transmissão? |
| $J_R$ | Quão ruim está o ajuste de reflexão? |
| $J=J_T+J_R$ | Quão ruim está o ajuste completo? |
| $\mathbf p^*=\arg\min J$ | Quais parâmetros queremos encontrar? |

---

# Pontos ainda a confirmar com o orientador/código completo

As seguintes partes não devem ser assumidas definitivamente sem consultar as funções auxiliares ou a formulação teórica utilizada pelo orientador:

- expressão exata implementada em `rij(...)`;
- expressão exata implementada em `tij(...)`;
- convenção de sinais das matrizes;
- significado/unidades exatas de $\chi$ no ajuste normalizado;
- justificativa teórica completa dos termos de fonte $2k$ e $0k$;
- expressão usada para o índice do vidro em `nlimeglass(...)`;
- limites físicos definitivos dos índices reais;
- tratamento definitivo da penalidade do pico de transmissão.

Esses pontos deverão ser adicionados a este documento conforme as funções auxiliares e a teoria específica do modelo forem disponibilizadas.
