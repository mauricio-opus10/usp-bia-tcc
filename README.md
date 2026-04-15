# Teoria dos Grafos e Ciência de Redes na Comparação de Padrões Estruturais que Antecederam as Guerras Mundiais

**TCC — MBA em Business Intelligence & Analytics**
**Universidade de São Paulo (USP/ECA)**

---

## 📑 Apêndices do TCC (para a banca)

> A versão final submetida do TCC **não inclui os apêndices** para cumprir o limite de 30 páginas. Eles estão disponíveis aqui:
>
> | Apêndice | Conteúdo | Link |
> |---|---|---|
> | **A** | Lista de Estados por período e código COW | 📄 [`apendices/apendice_A_estados.md`](apendices/apendice_A_estados.md) |
> | **B** | 12 tabelas completas de centralidade (4 camadas × 2 períodos), métricas globais, evolução, comunidades Louvain e robustez CINC | 📄 [`apendices/apendice_B_centralidade.md`](apendices/apendice_B_centralidade.md) |
>
> 👉 **Pasta completa dos apêndices:** [`apendices/`](apendices/) — inclui versões CSV machine-readable e [README explicativo](apendices/README.md).
>
> 🌐 **Redes prontas para o Gephi:** [`gephi/redes/`](gephi/redes/) — 10 arquivos GEXF (4 camadas × 2 períodos + 2 multilayer), com contagens validadas contra a Tabela B.9 do Apêndice B.
>
> Pipeline em [`src/network/metrics.py`](src/network/metrics.py); regenere os outputs com `run_pipeline_comparison.py`.

---

## Visão Geral

Este projeto aplica técnicas de Business Intelligence, Analytics e teoria dos grafos para modelar e comparar redes de **alianças, comércio, disputas e diplomacia entre Estados** nas janelas temporais que antecederam a Primeira e a Segunda Guerra Mundial, interpretando diferenças estruturais à luz do contexto histórico.

### Pergunta de Pesquisa

> Quais padrões estruturais mensuráveis nas redes interestatais (alianças, comércio, disputas e diplomacia) diferenciam as janelas pré-1914 e pré-1939, e como essas métricas podem ser interpretadas no contexto histórico sem inferir causalidade automática?

## Janelas Temporais

| Janela | Período | Evento Final |
|--------|---------|--------------|
| Pré-WWI | 1890–1914 | Primeira Guerra Mundial |
| Pré-WWII | 1925–1939 | Segunda Guerra Mundial |

## Modelagem das Redes

| Elemento | Descrição |
|----------|-----------|
| **Nós (vértices)** | Estados do sistema internacional (filtrados por capacidade material - CINC) |
| **Arestas (ligações)** | Relações entre Estados, ponderadas quando aplicável |
| **Camadas (multilayer)** | (A) Alianças formais, (C) Comércio bilateral, (D) Disputas militarizadas, (Dp) Diplomacia |

## Fontes de Dados

### Correlates of War (COW)
- **Formal Alliances (v4.1):** alianças formais entre Estados
- **Bilateral Trade (v4.0):** fluxos comerciais bilaterais
- **Militarized Interstate Disputes (MIDs v5.0):** disputas militarizadas
- **Diplomatic Exchange (v2006.1):** intercâmbio diplomático
- **National Material Capabilities (NMC v5.0):** capacidades materiais (CINC score)

### ATOP (Alliance Treaty Obligations and Provisions)
- Detalhamento de tipos de obrigações em tratados de aliança

### Maddison Project Database
- Indicadores macroeconômicos históricos (PIB per capita, população)

## Estrutura do Repositório

```
usp-bia-tcc/
│
├── README.md                        # Este arquivo
├── .gitignore
├── requirements.txt                 # Dependências Python
├── requirements.lock                # Versões fixas (reprodutibilidade)
│
├── gerar_figuras_tcc.py             # Gerador das 8 figuras de publicação
├── gerar_dados_diplomacia.py        # Análise da rede de diplomacia
│
├── apendices/                       # Apêndices A e B do TCC (ver §Apêndices)
│
├── src/                             # Código-fonte Python
│   ├── etl/                         # ETL (load_cow.py, transform.py)
│   ├── network/                     # Construção e análise de redes
│   ├── visualization/               # Visualizações e export Gephi
│   └── utils/                       # Constantes e helpers (RANDOM_SEED=42)
│
├── notebooks/                       # Jupyter notebooks exploratórios
├── r_scripts/                       # Scripts auxiliares em R
├── sql/                             # Queries SQL auxiliares
├── tests/                           # Testes unitários
├── reports/                         # Relatórios e entregas
├── gephi/                           # Redes em formato GEXF (10 arquivos prontos para o Gephi)
│   └── redes/                       # 4 camadas × 2 períodos + 2 multilayer
│
└── data/                            # ⚠️ Conteúdo NÃO versionado — regenerável pela pipeline
    ├── raw/                         # Dados brutos COW/ATOP/Maddison (obter da fonte)
    ├── processed/                   # Dados intermediários
    └── output/                      # Figuras, GEXFs e CSVs gerados localmente
```

> **Sobre `data/`:** este repositório é vitrine de código, não armazena os datasets brutos nem os artefatos de output (figuras PNG, GEXFs, CSVs intermediários). Para obter os dados originais, consulte as fontes em [§Fontes de Dados](#fontes-de-dados); para regenerar os outputs, rode a pipeline (ver [§Reprodutibilidade](#reprodutibilidade-e-stack-técnica)). As **métricas-chave do TCC** estão consolidadas em forma legível em [`apendices/`](apendices/).

## Métricas de Rede

| Métrica | O que mede |
|---------|------------|
| **Densidade** | Proporção de conexões existentes vs. possíveis |
| **Grau (degree)** | Número de conexões por nó |
| **Betweenness** | Nós que funcionam como "pontes" |
| **Closeness** | Proximidade média a todos os outros nós |
| **Eigenvector/PageRank** | Influência considerando conexões dos vizinhos |
| **Modularidade** | Formação de comunidades/blocos |

## Figuras do TCC

| Figura | Conteúdo | Diretório |
|--------|----------|-----------|
| 1 | Comparação das redes de alianças | `figura_1_aliancas_comparacao/` |
| 2 | Comunidades Louvain | `figura_2_comunidades_louvain/` |
| 3 | Ranking de densidade por camada | `figura_3_ranking_densidade/` |
| 4 | Comparação visual das 4 redes | `figura_4_comparacao_4_redes/` |
| 5 | Slope chart — brokers de disputas | `figura_5_brokers_slope_disputas/` |
| 6 | Heatmap de betweenness (4 camadas) | `figura_6_heatmap_betweenness/` |
| 7 | Jaccard inter-camadas (heatmap) | `figura_7_jaccard_multiplex/` |
| 8 | Teste de robustez CINC | `figura_8_robustez_cinc/` |

## Reprodutibilidade e Stack Técnica

**Stack:**

- `pandas`, `numpy` — manipulação de dados
- `networkx` — modelagem e análise de grafos
- `community-louvain` — detecção de comunidades
- `matplotlib`, `seaborn` — visualizações
- `python-docx` — geração do TCC em Word
- `scipy` — convex hull para visualização de comunidades

**Reprodutibilidade:**

- Seed fixo (`RANDOM_SEED = 42`) em `src/utils/helpers.py`, propagado para Louvain e demais rotinas estocásticas.
- Versões fixas em `requirements.lock`.
- Para regenerar todos os artefatos do TCC localmente:

```bash
~/.virtualenvs/datascience/bin/python run_pipeline_comparison.py
~/.virtualenvs/datascience/bin/python gerar_figuras_tcc.py
```

## Cronograma

| Fase | Período | Entregas |
|------|---------|----------|
| Preliminares | Dez/2025 | ETL inicial, primeira rede, métricas básicas |
| Desenvolvimento | Jan-Mar/2026 | Redes completas, comparações, robustez |
| Finalização | Abr-Mai/2026 | Redação, revisão, defesa |

## Diretrizes

- **Sem extrapolações preditivas** — foco em comparação histórica estrutural
- **Centralidade ≠ Causalidade** — interpretar métricas com cautela
- **Reprodutibilidade** — todo código versionado, dados documentados

## Autor

**Maurício Gonçalves**
MBA em Business Intelligence & Analytics — USP/ECA
Orientador: Prof. Paulo Henrique Assis Feitosa

## Licença

Este projeto é desenvolvido para fins acadêmicos como parte do TCC do MBA USP/ECA.

---

*Última atualização: Fevereiro/2026*
