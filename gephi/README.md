# Gephi — Redes do TCC

Esta pasta contém as **redes geradas pela pipeline** em formato [GEXF](https://gephi.org/gexf/format/) (Graph Exchange XML Format), prontas para abertura no [Gephi](https://gephi.org/).

## Conteúdo

```
gephi/
├── README.md                # Este arquivo
├── projetos/                # (reservado) projetos .gephi nativos
└── redes/                   # 10 arquivos GEXF — 4 camadas × 2 períodos + 2 multilayer
```

## Arquivos disponíveis

| Camada | Pré-WWI (1890–1914) | Pré-WWII (1925–1939) |
|---|---|---|
| **Alianças**   | [`redes/alliance_pre_wwi.gexf`](redes/alliance_pre_wwi.gexf) — 11 nós, 21 arestas¹ | [`redes/alliance_pre_wwii.gexf`](redes/alliance_pre_wwii.gexf) — 13 nós, 33 arestas |
| **Comércio**   | [`redes/trade_pre_wwi.gexf`](redes/trade_pre_wwi.gexf) — 12 nós, 62 arestas | [`redes/trade_pre_wwii.gexf`](redes/trade_pre_wwii.gexf) — 13 nós, 77 arestas |
| **Disputas**   | [`redes/disputes_pre_wwi.gexf`](redes/disputes_pre_wwi.gexf) — 12 nós, 41 arestas | [`redes/disputes_pre_wwii.gexf`](redes/disputes_pre_wwii.gexf) — 13 nós, 57 arestas |
| **Diplomacia** | [`redes/diplomatic_pre_wwi.gexf`](redes/diplomatic_pre_wwi.gexf) — 12 nós, 64 arestas | [`redes/diplomatic_pre_wwii.gexf`](redes/diplomatic_pre_wwii.gexf) — 13 nós, 78 arestas |
| **Multilayer (4 camadas)** | [`redes/multilayer_4camadas_pre_wwi.gexf`](redes/multilayer_4camadas_pre_wwi.gexf) — 20 nós, 65 arestas | [`redes/multilayer_4camadas_pre_wwii.gexf`](redes/multilayer_4camadas_pre_wwii.gexf) — 22 nós, 81 arestas |

¹ A rede de alianças pré-WWI tem **11 nós** (não 12) porque a Bélgica, embora atenda ao critério CINC ≥ 1%, não possui alianças formais registradas no COW Formal Alliances v4.1 para 1890–1914. Detalhes no [Apêndice A](../apendices/apendice_A_estados.md).

## Como abrir no Gephi

1. **Instale o Gephi** (versão 0.10+ recomendada): https://gephi.org/users/download/
2. **File → Open** e selecione um dos `.gexf`.
3. No diálogo de importação, mantenha o tipo de grafo **não-direcionado**.
4. Aplique um layout (sugestões):
   - **ForceAtlas 2** com `Scaling=10`, `Gravity=1` para alianças e disputas.
   - **Yifan Hu** para comércio e diplomacia (redes mais densas).
5. Para colorir comunidades: **Statistics → Modularity** (resolução 1.0), depois **Appearance → Nodes → Color → Partition → Modularity Class**.

## Reprodutibilidade

Os contadores de nós/arestas acima são exatamente os mesmos reportados na **Tabela B.9 — Métricas Globais por Camada e Período** (ver [`../apendices/apendice_B_centralidade.md`](../apendices/apendice_B_centralidade.md)).

Os GEXFs são gerados pela pipeline em `src/visualization/gephi_export.py` a partir dos grafos NetworkX construídos em `src/network/build_network.py`. Para regenerá-los a partir dos dados brutos COW:

```bash
~/.virtualenvs/datascience/bin/python run_pipeline_comparison.py
```

Os arquivos serão escritos em `data/output/` e podem ser recopiados para esta pasta.
