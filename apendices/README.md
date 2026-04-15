# Apêndices do TCC

Esta pasta contém os **apêndices da versão completa do TCC**, removidos do PDF submetido para cumprir o limite de 30 páginas estabelecido pelo MBA USP/ECA. Eles estão aqui para consulta da banca e para garantir reprodutibilidade.

**TCC:** *Teoria dos Grafos e Ciência de Redes na Comparação de Padrões Estruturais que Antecederam as Guerras Mundiais*
**Autor:** Maurício Gonçalves
**Orientador:** Prof. Paulo Henrique Assis Feitosa

## Conteúdo

| Arquivo | Descrição |
|---|---|
| [`apendice_A_estados.md`](apendice_A_estados.md) | Lista dos Estados analisados em cada janela temporal, com códigos COW. |
| [`apendice_A_estados.csv`](apendice_A_estados.csv) | Versão tabular do Apêndice A (machine-readable). |
| [`apendice_B_centralidade.md`](apendice_B_centralidade.md) | 12 tabelas (B.1–B.12): centralidade por camada/período, métricas globais, evolução, comunidades Louvain e teste de robustez. |
| [`apendice_B_centralidade.csv`](apendice_B_centralidade.csv) | Centralidade consolidada (4 camadas × 2 períodos × ~12 Estados, 99 linhas). |

## Observações

- As tabelas de centralidade do Apêndice B reportam **degree, betweenness, closeness e eigenvector**. As tabelas B.1 e B.2 (alianças) também incluem **centralidade de grau normalizada (C. Grau)** e **clustering local**.
- O Apêndice A documenta uma assimetria importante: a **rede de alianças pré-WWI tem 11 nós** (não 12), porque a Bélgica — que atende ao critério CINC ≥ 1% — não possui alianças formais registradas no COW Formal Alliances v4.1 para 1890–1914.
- Os dados brutos para regerar todas as tabelas estão em `../data/output/comparison/centralidade_novas.csv`, `../data/output/metricas_multilayer.csv` e `../data/output/robustez_cinc.csv`.

## Versões equivalentes em Word

As versões `.docx` originais dos apêndices também existem na raiz do repositório local do autor (`Apendice_B_Tabelas_Centralidade.docx` e `Apendices_BCD_TCC.docx`), mas **não são versionadas no GitHub** — esta versão Markdown é a fonte canônica para consulta.
