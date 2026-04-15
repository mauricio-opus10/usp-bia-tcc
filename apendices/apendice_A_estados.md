# Apêndice A — Lista de Estados por Período e Código COW

Este apêndice lista os Estados incluídos nas redes analisadas em cada janela temporal, identificados pelo código numérico do projeto **Correlates of War (COW)**.

## Critério de Seleção

Os Estados foram filtrados pelo **CINC (Composite Index of National Capability) ≥ 1%** em pelo menos um ano da janela temporal correspondente, conforme NMC v5.0 (Singer; Bremer; Stuckey, 1972; atualizado em Singer, 1987).

- **Janela pré-WWI:** 1890–1914
- **Janela pré-WWII:** 1925–1939

## Pré-WWI (1890–1914) — 12 Estados

| ccode | Sigla | Estado |
|------:|:-----:|--------|
| 2     | USA   | Estados Unidos |
| 200   | UKG   | Reino Unido |
| 211   | BEL   | Bélgica¹ |
| 220   | FRN   | França |
| 230   | SPN   | Espanha |
| 255   | GMY   | Alemanha |
| 300   | AUH   | Áustria-Hungria |
| 325   | ITA   | Itália |
| 365   | RUS   | Rússia |
| 640   | TUR   | Império Otomano |
| 710   | CHN   | China |
| 740   | JPN   | Japão |

¹ A **Bélgica** atende ao critério CINC ≥ 1% no período, mas **não possui alianças formais** registradas no dataset COW Formal Alliances v4.1 para 1890–1914. Por isso, a camada de alianças pré-WWI tem **11 nós** (em vez de 12), enquanto as camadas de comércio, disputas e diplomacia possuem 12 nós.

## Pré-WWII (1925–1939) — 13 Estados

| ccode | Sigla | Estado |
|------:|:-----:|--------|
| 2     | USA   | Estados Unidos |
| 140   | BRA   | Brasil |
| 200   | UKG   | Reino Unido |
| 211   | BEL   | Bélgica |
| 220   | FRN   | França |
| 230   | SPN   | Espanha |
| 255   | GMY   | Alemanha |
| 290   | POL   | Polônia |
| 315   | CZE   | Tchecoslováquia |
| 325   | ITA   | Itália |
| 365   | RUS   | União Soviética |
| 710   | CHN   | China |
| 740   | JPN   | Japão |

## Comparação de Composição

A mudança de composição entre as duas janelas é uma **limitação metodológica** explicitamente discutida no TCC (§5). A entrada e saída de Estados decorre de transformações político-territoriais relevantes:

- **Saída (pré-WWI → pré-WWII):** Áustria-Hungria (300) e Império Otomano (640), ambos dissolvidos após 1918.
- **Entrada (pré-WWI → pré-WWII):** Brasil (140), Polônia (290) e Tchecoslováquia (315), refletindo o ganho relativo de capacidade material e a criação de novos Estados pós-Versalhes.
- **Estados comuns aos dois períodos (10):** USA, UKG, BEL, FRN, SPN, GMY, ITA, RUS, CHN, JPN.

## Versão Tabular

A mesma informação está disponível em formato CSV em [`apendice_A_estados.csv`](apendice_A_estados.csv), com colunas:

```
ccode, abbrev, nome_pt, nome_en, pre_wwi, pre_wwii
```

Os campos `pre_wwi` e `pre_wwii` são indicadores binários (1 = presente no período).
