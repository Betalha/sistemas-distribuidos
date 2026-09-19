# Exercício 1.2: como n, k e p afetam a disponibilidade

Implementação em [`disponibilidade.py`](disponibilidade.py), tabela completa em
`resultados.csv`, gráficos em `grafico_analitico.png` e `grafico_comparativo.png`.
Fórmula deduzida no [Exercício 1.1](../e1.1/RESOLUCAO.md).

Varredura de `n ∈ {10, 50, 100, 200}`, `k ∈ {1, ⌈n/2⌉, n}` e `p` de 0 a 1 em passos
de 0,05. Cada ponto também é simulado com `10`, `50` e `200` rodadas. Recorte dos
valores analíticos:

| n | k | caso | p=0,45 | p=0,50 | p=0,55 | p=0,70 | p=0,90 | p=0,95 |
|---|---|------|--------|--------|--------|--------|--------|--------|
| 10 | 1 | k=1 | 0,9975 | 0,9990 | 0,9997 | 1,0000 | 1,0000 | 1,0000 |
| 10 | 5 | k=n/2 | 0,4956 | 0,6230 | 0,7384 | 0,9527 | 0,9999 | 1,0000 |
| 10 | 10 | k=n | 0,0003 | 0,0010 | 0,0025 | 0,0282 | 0,3487 | 0,5987 |
| 50 | 1 | k=1 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| 50 | 25 | k=n/2 | 0,2840 | 0,5561 | 0,8034 | 0,9991 | 1,0000 | 1,0000 |
| 50 | 50 | k=n | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0052 | 0,0769 |
| 100 | 1 | k=1 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| 100 | 50 | k=n/2 | 0,1827 | 0,5398 | 0,8654 | 1,0000 | 1,0000 | 1,0000 |
| 100 | 100 | k=n | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0059 |
| 200 | 1 | k=1 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| 200 | 100 | k=n/2 | 0,0887 | 0,5282 | 0,9319 | 1,0000 | 1,0000 | 1,0000 |
| 200 | 200 | k=n | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |

## Efeito de n

Depende inteiramente do `k`. Com `k = 1`, mais réplicas sempre ajudam: já com
`n = 10` a disponibilidade passa de 0,99 para qualquer `p ≥ 0,40`. Com `p = 0,05`,
ela vai de 0,923 (n=50) para 0,994 (n=100) e 1,0000 (n=200, em 4 casas).

Com `k = n`, mais réplicas sempre atrapalham, e muito. Com `p = 0,95`, exigir as 10
no ar dá 0,599; as 50, 0,077; as 200, praticamente zero (0,95²⁰⁰ ≈ 3,5·10⁻⁵). Cada
réplica adicionada vira mais um ponto único de falha.

## Efeito de k

Fixando `n` e `p`, aumentar `k` sempre reduz a disponibilidade: em `n = 10`,
`p = 0,9`, ela vai de 1,000 (`k = 1`) para 0,9999 (`k = 5`) e despenca para 0,349
(`k = 10`).

O quórum `k = ⌈n/2⌉` é o caso em que `n` amplifica o efeito de `p`. O ponto de
virada é `p = 0,5`, onde ele fica perto de 0,5 (0,623 com n=10 e 0,528 com n=200).
Acima dele, mais réplicas ajudam: com `p = 0,55` vai de 0,738 (n=10) a 0,932
(n=200). Abaixo, mais réplicas atrapalham: com `p = 0,45` cai de 0,496 para 0,089.
Quanto maior o `n`, mais a curva se parece com um degrau em `p = 0,5`.

## Efeito de p

Todas as curvas crescem monotonicamente de `A = 0` em `p = 0` até `A = 1` em `p = 1`.
O que muda com `k` é o formato: `k = 1` sobe quase imediatamente e satura cedo,
enquanto `k = n` fica colado no eixo e só sobe quando `p` está muito perto de 1.
O `p` também determina se replicar compensa: para `k = ⌈n/2⌉` e `k = n`, servidores
ruins (`p` baixo) fazem a replicação trabalhar contra a disponibilidade.

Ver `grafico_analitico.png`: um painel por `n`, uma curva por caso de `k`.

## Simulação e número de rodadas

A simulação estima `A` como a fração de rodadas em que pelo menos `k` dos `n`
servidores ficaram no ar. Com poucas rodadas a estimativa é ruidosa. O desvio padrão
é `√(A(1−A)/rodadas)`, que chega ao máximo de `0,5/√rodadas` quando `A = 0,5`.

| rodadas | erro máx. observado | desvio máx. teórico |
|---------|---------------------|---------------------|
| 10 | 0,197 | 0,158 |
| 50 | 0,122 | 0,071 |
| 200 | 0,052 | 0,035 |

Multiplicar as rodadas por 20 reduziu o erro em cerca de 3,8 vezes, perto dos √20 ≈ 4,5
esperados. O erro só aparece onde a curva está subindo. Onde `A` vale 0 ou 1, a
simulação acerta mesmo com 10 rodadas, porque não há variância. Com `n` grande a
subida fica estreita, então os pontos simulados se afastam da curva só em poucos
valores de `p`: perto de 0,5 no quórum e perto de 1 em `k = n`.

Ver `grafico_comparativo.png`: uma linha por número de rodadas e uma coluna por `n`.
