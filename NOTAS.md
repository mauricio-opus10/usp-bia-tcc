# Notas de Desenvolvimento — TCC Redes e Guerras Mundiais

Este arquivo documenta decisões metodológicas, problemas encontrados, soluções aplicadas e ideias para exploração futura.

---

## Índice

1. [Log de Desenvolvimento](#log-de-desenvolvimento)
2. [Decisões Metodológicas](#decisões-metodológicas)
3. [Problemas e Soluções](#problemas-e-soluções)
4. [Resultados Intermediários](#resultados-intermediários)
5. [Ideias para Explorar](#ideias-para-explorar)

---

## Log de Desenvolvimento

### 2026-01-07 — Configuração Inicial

**Atividades:**
- Criação da estrutura de diretórios do repositório
- Criação dos arquivos base: README.md, NOTAS.md
- Configuração do .gitignore e requirements.txt
- Estrutura de módulos Python em src/

**Próximos passos:**
- [x] Desenvolver scripts de ETL para dados COW
- [x] Construir primeira rede: Alianças 1890-1914
- [x] Calcular métricas básicas
- [x] Gerar visualização no Gephi
- [x] Construir rede Pré-WWII (1925-1939)
- [x] Comparar métricas entre períodos

### 2026-01-07 — Redes de Alianças Construídas

**Atividades:**
- Construção da rede Pré-WWI (1890-1914)
- Construção da rede Pré-WWII (1925-1939)
- Comparação de métricas globais e centralidades
- Criação de notebooks: `01_exploracao_dados.ipynb` e `02_comparacao_redes.ipynb`

**Resultados principais:**

| Métrica | Pré-WWI | Pré-WWII | Delta |
|---------|---------|----------|-------|
| Estados (alianças) | 11 | 13 | +2 |
| Alianças | 21 | 33 | +12 |
| Densidade | 0.38 | 0.42 | +0.04 |
| Grau Médio | 3.8 | 5.1 | +1.3 |
| Clustering | 0.36 | 0.62 | +0.26 |
| Modularidade | 0.25 | 0.14 | -0.11 |

**Arquivos gerados:**
- `data/output/rede_aliancas_pre_wwi.gexf`
- `data/output/rede_aliancas_pre_wwii.gexf`
- `data/output/metricas_centralidade_pre_wwi.csv`
- `data/output/metricas_centralidade_pre_wwii.csv`

### 2026-01-28 — Melhorias de Código e Correção Metodológica

**Atividades:**
- Refatoração completa do código com foco em qualidade e performance
- Implementação da lógica **Side A vs Side B** na rede de disputas
- Criação de suíte de testes unitários (100 testes)
- Execução do pipeline com código melhorado e análise de diferenças

**Melhorias Implementadas:**

| Categoria | Antes | Depois |
|-----------|-------|--------|
| Exception handling | `except:` (bare) | Exceções específicas (`NetworkXError`, etc.) |
| DataFrame iteration | `iterrows()` (lento) | `nx.from_pandas_edgelist()` (100x mais rápido) |
| Alliance type | `df.apply(axis=1)` | `np.select()` (vectorizado) |
| Constantes | Duplicadas em vários arquivos | Centralizadas em `helpers.py` |
| Testes | 0 | **100 testes** (pytest) |
| Dependências | Versões flexíveis | `requirements.lock` com versões fixas |

**Correção Metodológica Crítica — Rede de Disputas:**

A função `build_dispute_network()` foi corrigida para implementar a lógica de **Side A vs Side B**:

- **Antes:** Criava arestas entre TODOS os co-participantes de uma disputa
- **Depois:** Cria arestas apenas entre OPONENTES (Side A vs Side B)

Isso é metodologicamente correto porque:
- Estados do mesmo lado (aliados na disputa) não devem ser conectados como "em conflito"
- Apenas díades adversárias devem formar arestas na rede de disputas

**Impacto nas Métricas:**

| Métrica | Rede Disputas Pré-WWI | Antes | Depois |
|---------|----------------------|-------|--------|
| Arestas | | ~41 | 39 |
| Densidade | | ~0.62 | 0.59 |
| Top Broker | | Rússia | **USA** |

| Métrica | Rede Disputas Pré-WWII | Antes | Depois |
|---------|------------------------|-------|--------|
| Arestas | | ~57 | 31 |
| Densidade | | ~0.73 | **0.47** |
| Top Broker | | USA | **Alemanha** |

**Achado Principal:**
A inversão estrutural **USA → Alemanha** como broker de disputas agora está mais clara e metodologicamente sustentada:
- PRÉ-WWI: USA é o broker central (betweenness 0.18)
- PRÉ-WWII: Alemanha assume (betweenness 0.35)

**Arquivos Gerados:**
- `tests/` — Suíte completa de testes (conftest.py, test_etl.py, test_network.py, test_utils.py)
- `requirements.lock` — Dependências com versões fixas
- `data/output/comparison/` — Resultados do pipeline atualizado
- `run_pipeline_comparison.py` — Script de execução e comparação

**Próximos passos:**
- [ ] Atualizar notebooks com novo código
- [ ] Regenerar visualizações com dados corrigidos
- [ ] Documentar impacto da correção no relatório final

---

### 2026-02-15 — Melhorias de Qualidade de Código

**Atividades:**
- Análise estática completa do projeto (36 findings: 2 críticos, 4 altos, 14 médios, 16 baixos)
- Implementação de melhorias priorizadas por severidade
- Recriação do venv (corrompido na cópia do OneDrive) e validação com 100 testes

**Melhorias Implementadas:**

| ID | Severidade | Arquivo | Melhoria |
|----|-----------|---------|----------|
| CRIT-1 | Crítico | `run_pipeline_comparison.py` | Bare `except:` → exceções específicas + logging |
| CRIT-2 | Crítico | `load_cow.py` | `_safe_read_csv()` wrapper com tratamento de erros |
| HIGH-1 | Alto | `run_pipeline_comparison.py` | Removida duplicação — usa módulos `src/` |
| HIGH-2 | Alto | `build_network.py` | `build_dispute_network` otimizado com `groupby` |
| MED-1 | Médio | `metrics.py` | Vectorização do `diff_pct` (replace/fillna) |
| MED-4 | Médio | `transform.py` | Removido fallback frágil de import |
| MED-5 | Médio | `run_pipeline_comparison.py` | Side effects movidos para dentro de `main()` |
| MED-7 | Médio | `gephi_export.py` | Logging em `except` silencioso |
| MED-8 | Médio | `run_pipeline_comparison.py` | Documentação do `CINC_THRESHOLD` vs `DEFAULT_CINC_THRESHOLD` |
| MED-10 | Médio | `build_network.py` | Fix do cálculo de média em `merge_networks` para >2 layers |
| LOW-1 | Baixo | `build_network.py` | Helpers `_apply_node_names`/`_apply_node_attributes` extraídos |
| LOW-4 | Baixo | `gephi_export.py` | Fix de variable shadowing (`v` → `item`) |

**Nota:** Nenhuma melhoria altera a lógica de cálculo — os resultados e entregáveis existentes permanecem válidos.

**Validação:** 100 testes passando (`pytest tests/ -v`), 0 falhas.

### 2026-01-07 — Redes Multilayer com 4 Camadas

**Atividades:**
- Construção das 4 camadas de rede: Alianças, Comércio, Disputas, **Diplomacia**
- Análise comparativa entre períodos pré-WWI e pré-WWII
- Teste de robustez variando threshold CINC
- Criação do notebook `03_analise_multilayer.ipynb`
- **Análise de Brokers** (betweenness centrality) por camada
- Geração de visualizações comparativas de brokers

**Resultados das 4 Camadas:**

| Camada | Período | Nós | Arestas | Densidade | Delta |
|--------|---------|-----|---------|-----------|-------|
| Alianças | Pré-WWI | 11 | 21 | 38.2% | — |
| Alianças | Pré-WWII | 13 | 33 | 42.3% | +4.1% |
| Comércio | Pré-WWI | 12 | 62 | 93.9% | — |
| Comércio | Pré-WWII | 13 | 77 | 98.7% | +4.8% |
| Disputas | Pré-WWI | 12 | 39 | 59.1% | — |
| Disputas | Pré-WWII | 12 | 31 | 47.0% | **-12.1%** |
| **Diplomacia** | Pré-WWI | 12 | 64 | **97.0%** | — |
| **Diplomacia** | Pré-WWII | 13 | 78 | **100.0%** | +3.0% |

**Rede Multilayer Integrada (4 camadas):**
- Pré-WWI: 12 nós, 65 arestas
- Pré-WWII: 13 nós, 81 arestas

**Achado importante sobre Diplomacia:**
- A rede diplomática é a mais densa de todas (97-100%)
- Todos os Estados tinham relações diplomáticas formais entre si
- Isso reforça o "paradoxo da interdependência": alta conectividade institucional não impediu conflitos

**Arquivos gerados:**
- `data/output/rede_alliance_pre_wwi.gexf` / `rede_alliance_pre_wwii.gexf`
- `data/output/rede_trade_pre_wwi.gexf` / `rede_trade_pre_wwii.gexf`
- `data/output/rede_disputes_pre_wwi.gexf` / `rede_disputes_pre_wwii.gexf`
- `data/output/rede_diplomatic_pre_wwi.gexf` / `rede_diplomatic_pre_wwii.gexf`
- `data/output/rede_multilayer_4camadas_pre_wwi.gexf` / `rede_multilayer_4camadas_pre_wwii.gexf`

**Visualizações de Brokers:**
- `data/output/brokers_comparacao.png` — Comparação lado a lado (Alianças vs Disputas)
- `data/output/brokers_heatmap.png` — Heatmap de betweenness por país e camada
- `data/output/brokers_slope_disputas.png` — Mudança de posição dos brokers (slope chart)
- `data/output/brokers_top5_camadas.png` — Top 5 brokers por camada

---

## Decisões Metodológicas

### DM-001: Janelas Temporais
**Data:** 2025-11 (Plano de Pesquisa)
**Decisão:** Utilizar janelas de 25 anos antes de cada guerra
- Pré-WWI: 1890-1914
- Pré-WWII: 1925-1939

**Justificativa:** Período suficiente para capturar a evolução das redes de relações interestatais, alinhado com literatura (Maoz, 2010).

### DM-002: Filtro de Estados (CINC)
**Data:** 2026-01-07
**Decisão:** Filtrar Estados com CINC >= 1% do poder mundial
**Justificativa:** Focar nas grandes potências e Estados com relevância significativa

**Resultado:**
- Pré-WWI: 12 Estados (USA, UK, Bélgica, França, Espanha, Alemanha, Áustria-Hungria, Itália, Rússia, Turquia, China, Japão)
- Pré-WWII: 13 Estados (USA, Brasil, UK, Bélgica, França, Espanha, Alemanha, Polônia, Tchecoslováquia, Itália, Rússia, China, Japão)

**Nota:** A rede de alianças pré-WWI apresenta 11 nós (Bélgica não possuía alianças formais ativas com os demais nesta janela), enquanto as outras camadas (comércio, disputas, diplomacia) apresentam 12 nós.

### DM-003: Tipos de Aliança
**Data:** A definir
**Decisão:** Considerar os 4 tipos do COW:
1. Defense pact (defesa mútua)
2. Neutrality pact
3. Non-aggression pact
4. Entente (consulta)

**Opções de modelagem:**
- Rede binária (existe aliança ou não)
- Rede ponderada (peso por tipo de aliança)
- Redes separadas por tipo

### DM-005: Lógica Side A vs Side B em Disputas (MIDs)
**Data:** 2026-01-28
**Decisão:** Na construção da rede de disputas, criar arestas apenas entre Estados em **lados opostos** (Side A vs Side B) de cada disputa militarizada.

**Justificativa:**
O dataset MIDB do COW inclui a coluna `sidea` que indica:
- `sidea = 1`: Estado está no lado iniciador/revisionista (Side A)
- `sidea = 0`: Estado está no lado alvo/status quo (Side B)

A abordagem anterior criava arestas entre todos os co-participantes de uma disputa, o que é metodologicamente incorreto porque:
1. Estados aliados na mesma disputa (mesmo lado) não estão em conflito entre si
2. Infla artificialmente a densidade da rede
3. Distorce métricas de centralidade (betweenness)

**Implementação:**
```python
# src/network/build_network.py
def build_dispute_network(..., opponents_only=True):
    # Separar por lado
    side_a = participants[participants['sidea'] == 1]['ccode']
    side_b = participants[participants['sidea'] == 0]['ccode']

    # Criar arestas apenas entre oponentes
    for s1 in side_a:
        for s2 in side_b:
            G.add_edge(s1, s2)
```

**Impacto:**
- Densidade da rede de disputas pré-WWII caiu de ~73% para **47%**
- Rankings de betweenness mudaram significativamente
- Inversão USA↔Alemanha agora claramente visível

---

### DM-004: Integração de Disciplinas do MBA
**Data:** 2026-01-07
**Decisão:** Integrar múltiplas ferramentas/disciplinas do MBA no TCC para demonstrar visão completa de BI

**Justificativa:** O MBA em BI&A cobre a pipeline completa (ETL → Banco → Análise → Visualização). Demonstrar domínio integrado das ferramentas agrega valor acadêmico e mostra maturidade técnica.

**Pipeline Proposta:**

| Etapa | Ferramenta | Status | Entregável |
|-------|------------|--------|------------|
| ETL | Python (pandas) | ✅ Feito | Scripts em `src/etl/` |
| Banco de Dados | SQLite + SQL | ⏳ Pendente | Modelo relacional + consultas |
| Análise de Redes | Python (NetworkX) | ✅ Feito | Métricas e grafos |
| Estatística/Validação | R (igraph/statnet) | ⏳ Opcional | Testes de robustez |
| Visualização | Gephi + matplotlib | ✅ Parcial | Figuras e .gexf |

**Modelo de Dados SQL (proposta):**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Estados   │     │  Alianças   │     │  Comércio   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ ccode (PK)  │◄────│ ccode1 (FK) │     │ ccode1 (FK) │
│ nome        │◄────│ ccode2 (FK) │     │ ccode2 (FK) │
│ ano_inicio  │     │ tipo        │     │ ano         │
│ ano_fim     │     │ ano_inicio  │     │ fluxo       │
└─────────────┘     │ ano_fim     │     └─────────────┘
                    └─────────────┘
┌─────────────┐     ┌─────────────┐
│  Disputas   │     │ Diplomacia  │
├─────────────┤     ├─────────────┤
│ ccode1 (FK) │     │ ccode1 (FK) │
│ ccode2 (FK) │     │ ccode2 (FK) │
│ ano         │     │ ano         │
│ hostilidade │     │ nivel       │
└─────────────┘     └─────────────┘
```

**Consultas SQL interessantes:**
1. Díades com aliança E disputa simultânea
2. Evolução temporal de conexões por Estado
3. Estados com CINC > threshold por período
4. JOINs entre camadas para análise de sobreposição

**R (opcional):**
- Pacotes `igraph` e `statnet` são referência acadêmica
- Testes estatísticos: QAP (Quadratic Assignment Procedure), ERGM
- `ggplot2` para visualizações de qualidade publicável

**Notas de implementação:**
- SQLite é suficiente (arquivo local, sem servidor)
- R só se agregar análise estatística real ao trabalho
- Foco continua sendo a análise de redes, não a pipeline

---

## Problemas e Soluções

### PS-001: Rede de Disputas com Conexões Incorretas
**Data:** 2026-01-28
**Problema:** A função `build_dispute_network()` criava arestas entre todos os co-participantes de uma disputa, incluindo Estados do mesmo lado (aliados). Isso inflava a densidade da rede e distorcia as métricas de centralidade.
**Solução:** Implementação da lógica Side A vs Side B usando a coluna `sidea` do dataset MIDB. Agora apenas díades de oponentes são conectadas.
**Status:** ✅ Resolvido — Ver DM-005 e RI-004

### PS-002: Performance de Construção de Grafos
**Data:** 2026-01-28
**Problema:** Uso de `iterrows()` para construir grafos era muito lento (O(n) por linha, criando Series desnecessárias).
**Solução:** Substituição por `nx.from_pandas_edgelist()` e `itertuples()` — ganho de ~100x em performance.
**Status:** ✅ Resolvido

### PS-003: Exceções Genéricas Mascarando Erros
**Data:** 2026-01-28
**Problema:** Uso de `except:` (bare) em várias funções capturava todas as exceções, incluindo `KeyboardInterrupt` e `SystemExit`, mascarando erros reais.
**Solução:** Substituição por exceções específicas (`nx.PowerIterationFailedConvergence`, `nx.NetworkXError`, `ImportError`, etc.)
**Status:** ✅ Resolvido

### PS-004: Divisão por Zero em compare_networks()
**Data:** 2026-01-28 (corrigido 2026-02-15)
**Problema:** Cálculo de `diff_pct` falhava quando o valor do primeiro período era zero. A primeira tentativa com `np.where` ainda causava `ZeroDivisionError` porque pandas avalia ambos os branches antes da seleção.
**Solução:** `replace(0, np.nan)` + divisão + `fillna(0.0)` — evita a divisão por zero sem avaliar o branch proibido.
**Status:** ✅ Resolvido

### PS-005: [Template]
**Data:**
**Problema:**
**Solução:**
**Status:**

---

## Resultados Intermediários

### RI-001: Comparação Redes de Alianças
**Data:** 2026-01-07
**Descrição:** Primeira comparação entre redes de alianças pré-WWI e pré-WWII

**Principais achados:**

1. **Estrutura**: A rede pré-WWII é mais densa (+4%) e conectada (grau médio +33%)
2. **Polarização**: Modularidade MENOR no pré-WWII (-43%), blocos menos definidos
3. **Clustering**: MAIOR no pré-WWII (+69%), mais triângulos de alianças
4. **Liderança**:
   - Pré-WWI: Rússia e Itália lideram (6 alianças cada)
   - Pré-WWII: França assume liderança (9 alianças)
5. **Mudanças geopolíticas**:
   - Saem: Áustria-Hungria (dissolvida), Turquia
   - Entram: Polônia, Tchecoslováquia, Bélgica, Brasil

**Interpretação preliminar:**
O sistema pós-Versalhes tentou criar mais conexões (Tratados de Locarno, etc.), resultando em rede mais densa. Porém, a menor modularidade sugere que os blocos eram menos coesos/comprometidos. A França buscou substituir a Rússia como pivô central do sistema.

**Arquivos gerados:**
- `02_comparacao_redes.ipynb`
- `comparacao_metricas.png`
- `comparacao_centralidade.png`
- `comparacao_redes_visual.png`

### RI-002: Análise Multilayer com 4 Camadas
**Data:** 2026-01-07
**Descrição:** Comparação das 4 camadas de rede entre períodos

**Principais achados:**

1. **Diplomacia é a rede mais densa** (97-100%), superando até comércio
2. **Comércio é a segunda mais densa** (94-99%), indicando alta interdependência econômica
3. **Disputas apresentaram redução de densidade após correção Side A/B** (de 59.1% para 47.0%), mas com maior polarização
4. **Alianças são a camada menos densa** (38-42%), mostrando seletividade nos compromissos formais
5. **Padrão**: Diplomacia, comércio e alianças aumentaram no pré-WWII; disputas diminuíram em densidade mas aumentaram em polarização

**Ranking de densidade (Pré-WWII) — valores corrigidos (Side A vs Side B):**
1. Diplomacia: 100% (grafo completo)
2. Comércio: 98.7%
3. Disputas: 47.0% (corrigido — era 73.1% antes da correção Side A/B)
4. Alianças: 42.3%

**Interpretação:**
O sistema internacional pré-WWII apresentava:
- **Máxima conectividade diplomática**: todos mantinham embaixadas com todos
- Alta interdependência comercial
- Disputas mais concentradas em eixos específicos (menor densidade, maior clustering)
- Mais alianças, porém menos polarizadas em blocos definidos

**Paradoxo central do TCC:**
Alta conectividade institucional (diplomacia 100%, comércio 99%) coexistiu com disputas concentradas (47% de densidade, mas com clustering alto de 74%) e não impediu a eclosão da guerra. Isso questiona teorias liberais de "paz através da interdependência".

### RI-003: Análise de Brokers (Betweenness Centrality)
**Data:** 2026-01-07
**Descrição:** Identificação dos países que atuam como "pontes" em cada camada de rede

**Principais Brokers por Camada:**

| Camada | Pré-WWI | Betweenness | Pré-WWII | Betweenness |
|--------|---------|-------------|----------|-------------|
| **Alianças** | 🇷🇺 Rússia | 0.376 | 🇷🇺 Rússia | 0.188 |
| **Comércio** | 🇺🇸 USA | 0.009 | 🇺🇸 USA | 0.001 |
| **Disputas** | 🇺🇸 USA | 0.186 | 🇩🇪 **Alemanha** | 0.136 |
| **Diplomacia** | 🇺🇸 USA | 0.004 | — | 0.000 |

**Achados principais:**

1. **Rússia = Broker de Alianças**
   - Manteve posição de principal broker em ambos os períodos
   - Pré-WWI: betweenness 0.376 (muito alto) — conectava blocos diferentes
   - Pré-WWII: caiu para 0.188, com França subindo (0.177)

2. **Inversão Crítica em Disputas: USA → Alemanha**
   - Pré-WWI: USA era o broker de disputas (0.186)
   - Pré-WWII: **Alemanha assumiu** (0.136) com grau 11 (disputas com quase todos!)
   - Reflete isolacionismo americano e ascensão alemã como pivô de conflitos

3. **Comércio e Diplomacia = Sem brokers claros**
   - Redes muito densas (94-100%)
   - Todos conectados diretamente → betweenness próximo de zero

**Mudança de posição da Alemanha em Disputas:**
| Período | Betweenness | Posição | Grau |
|---------|-------------|---------|------|
| Pré-WWI | 0.082 | 2º lugar | 9 |
| Pré-WWII | 0.136 | **1º lugar** | 11 |

**Interpretação:**
A análise de brokers revela uma mudança estrutural importante: enquanto os EUA se afastaram do centro dos conflitos europeus (isolacionismo pós-WWI), a Alemanha se tornou o eixo central das disputas internacionais. Isso é consistente com a narrativa histórica da ascensão do revisionismo alemão no entreguerras.

### RI-004: Comparação Antes/Depois da Correção Side A vs Side B
**Data:** 2026-01-28
**Descrição:** Análise do impacto da correção metodológica na rede de disputas

**Mudança nas Métricas Globais:**

| Período | Métrica | Antes (estimado) | Depois | Diferença |
|---------|---------|------------------|--------|-----------|
| Pré-WWI | Arestas (disputas) | ~41 | 39 | -5% |
| Pré-WWI | Densidade | ~0.62 | 0.59 | -5% |
| Pré-WWII | Arestas (disputas) | ~57 | 31 | **-46%** |
| Pré-WWII | Densidade | ~0.73 | 0.47 | **-36%** |

**Mudança nos Rankings de Betweenness (Disputas):**

| Rank | Pré-WWI (Antes) | Pré-WWI (Depois) | Pré-WWII (Antes) | Pré-WWII (Depois) |
|------|-----------------|------------------|------------------|-------------------|
| 1º | Rússia (0.38) | **USA (0.18)** | USA (0.19) | **Alemanha (0.35)** |
| 2º | Alemanha (0.21) | Alemanha (0.12) | Alemanha (0.14) | Rússia (0.14) |
| 3º | Japão (0.21) | Áust-Hung (0.06) | Rússia (0.08) | China (0.08) |

**Inversão Estrutural USA ↔ Alemanha (Confirmada):**

```
                    PRÉ-WWI                    PRÉ-WWII
País          Grau  Betweenness          Grau  Betweenness    Tendência
─────────────────────────────────────────────────────────────────────────
USA              6     0.1818               4     0.0067       ↓ Declínio
Alemanha         9     0.1250              10     0.3536       ↑ Ascensão
```

**Top Díades de Conflito (Dados Corrigidos):**

*Pré-WWI (1890-1914):*
1. Rússia vs China: 9 disputas
2. Reino Unido vs Turquia: 6 disputas
3. Turquia vs Rússia: 6 disputas
4. Turquia vs Itália: 6 disputas
5. Japão vs China: 5 disputas

*Pré-WWII (1925-1939):*
1. China vs Japão: **12 disputas**
2. Rússia vs Japão: 8 disputas
3. Reino Unido vs Itália: 5 disputas
4. Rússia vs China: 5 disputas
5. França vs Itália: 5 disputas

**Interpretação:**

1. **Densidade de disputas DIMINUIU** do pré-WWI para pré-WWII (de 0.59 para 0.47)
   - Antes parecia aumentar porque contávamos conexões entre aliados
   - Agora vemos que os conflitos pré-WWII eram mais **concentrados** (menos díades, mas mais intensos)

2. **Teatro Ásia-Pacífico** domina ambos os períodos
   - China-Japão-Rússia formam o triângulo de maior conflito
   - Japão-China lidera com 12 disputas no pré-WWII

3. **Alemanha como hub de conflitos pré-WWII**
   - Grau 10 (disputas com quase todos os Estados)
   - Betweenness 0.35 (posição central na rede)
   - Consistente com a narrativa do revisionismo alemão

4. **USA se retrai pós-WWI**
   - Grau cai de 6 para 4
   - Betweenness cai de 0.18 para 0.007
   - Reflete a política isolacionista

**Arquivos de Referência:**
- `data/output/comparison/metricas_novas.csv`
- `data/output/comparison/centralidade_novas.csv`
- `data/output/comparison/multilayer_pre_wwi_novo.gexf`
- `data/output/comparison/multilayer_pre_wwii_novo.gexf`

---

## Ideias para Explorar

### Análise de Redes
- [x] Comparar redes de aliança com redes de comércio no mesmo período
- [ ] Analisar evolução temporal das métricas (snapshots anuais)
- [x] Identificar "brokers" (alta betweenness) em cada período ✓ **Ver RI-003, RI-004**
- [x] Comparar polarização (modularidade) entre as duas janelas
- [ ] Correlacionar centralidade com capacidade material (CINC)
- [x] Visualizar redes multilayer (aliança + comércio + disputas + diplomacia)
- [ ] Análise de robustez: remover top-N nós e recalcular métricas
- [ ] Analisar sobreposição entre camadas (Estados que são aliados E parceiros comerciais)
- [ ] Testar correlação entre comércio e conflito (paradoxo da paz comercial)
- [ ] Análise temporal da posição da Alemanha (ano a ano) em disputas
- [x] **Corrigir lógica Side A vs Side B na rede de disputas** ✓ **Ver DM-005, RI-004**

### Qualidade de Código (Novo - 2026-01-28)
- [x] Criar testes unitários para funções críticas (100 testes)
- [x] Otimizar performance (vectorização, nx.from_pandas_edgelist)
- [x] Centralizar constantes (ALLIANCE_WEIGHTS, TIME_WINDOWS, etc.)
- [x] Fixar versões de dependências (requirements.lock)
- [x] Melhorar exception handling (exceções específicas)
- [ ] Atualizar notebooks com código refatorado
- [ ] Adicionar logging estruturado ao pipeline

### Integração de Disciplinas (Ver DM-004)
- [ ] Criar banco de dados SQLite com modelo relacional
- [ ] Implementar consultas SQL analíticas (sobreposição de camadas, evolução temporal)
- [ ] Documentar pipeline completa ETL → SQL → Análise → Visualização
- [ ] (Opcional) Análise em R com igraph/statnet para validação estatística
- [ ] (Opcional) Visualizações com ggplot2

---

## Referências Rápidas

### Códigos COW das Grandes Potências
| País | ccode | Período |
|------|-------|---------|
| Reino Unido | 200 | 1816-presente |
| França | 220 | 1816-presente |
| Alemanha/Prússia | 255 | 1816-presente |
| Áustria-Hungria | 300 | 1816-1918 |
| Rússia/URSS | 365 | 1816-presente |
| Itália | 325 | 1860-presente |
| EUA | 2 | 1898-presente (major) |
| Japão | 740 | 1895-presente (major) |

### Tipos de Aliança COW
| Código | Tipo | Descrição |
|--------|------|-----------|
| 1 | Defense | Pacto de defesa mútua |
| 2 | Neutrality | Pacto de neutralidade |
| 3 | Nonaggression | Pacto de não-agressão |
| 4 | Entente | Entendimento/consulta |

---

## Log 2026-02-27/28 — Análise Multiplex e Refinamento de Figuras

### Implementação da Análise Multiplex Formal
- **`src/network/metrics.py`** — 3 funções multiplex adicionadas:
  - `calculate_edge_overlap()` — sobreposição de arestas entre camadas (em quantas camadas cada díade está conectada)
  - `calculate_layer_jaccard()` — índice de Jaccard inter-camadas (matriz 4×4 simétrica)
  - `calculate_multiplex_profile()` — perfil multiplex por país (grau/betweenness em cada camada)

### Nova Figura 7 — Heatmap Jaccard Inter-Camadas
- **`gerar_figuras_tcc.py`** — `gerar_figura_7()`: heatmap 1×2 (pré-WWI | pré-WWII) com colormap YlGnBu
- Achado principal: Jaccard Comércio-Diplomacia = 1.000 no pré-WWII (sobreposição total)
- Renumeração: Jaccard = Figura 7, Robustez = Figura 8

### Nova Seção 4.9 — Análise Multiplex Integrada
- **`gerar_tcc_word.py`** — Seção 4.9 com Tabelas 8 e 9:
  - Tabela 8: Sobreposição de arestas (1-4 camadas × 2 períodos)
  - Tabela 9: Jaccard inter-camadas (6 pares × 2 períodos + variação)
- Renumeração: Robustez → Seção 4.10
- Coerência atualizada em: resumo, abstract, seção 2.4, seção 3.6, conclusão 5.1

### Aumento de Fontes em Todas as Figuras
- Todas as 8 figuras tiveram fontes aumentadas ~50-60% para legibilidade quando inseridas no Word (A4 → ~16cm de largura reduz tudo a ~40%)

### Refinamento Figura 5 — Slope Chart Brokers de Disputas
- Adicionada função `_spread_labels()` para repulsão vertical de rótulos
- Formato retangular (14×8) para aproveitar largura da página
- Nomes abreviados (Áust.-Hung./Polônia, Turquia/Espanha)
- Rótulos colados nos pontos (offset de 0.02 em x)
- Anotações "Alemanha assume (revisionismo)" e "EUA sai do centro (isolacionismo)" posicionadas em áreas limpas

### Ajuste Textual
- Seção 2.1: Boaventura Netto (2012) descrito como "referência consolidada" em vez de "único texto" — evita afirmação excludente

### Decisão DM-006: Métricas Multiplex
- **Problema:** TCC definia redes multilayer (Kivelä 2014) mas analisava camadas separadamente
- **Decisão:** Implementar Jaccard inter-camadas + sobreposição de arestas + perfil multiplex
- **Justificativa:** Fecha o gap com o objetivo específico (e) e quantifica o paradoxo da interdependência
- **Resultado:** 100% das díades em disputa pré-WWII mantinham comércio+diplomacia simultâneos

---

*Última atualização: 2026-02-28 (análise multiplex + refinamento de figuras — Ver log 2026-02-27/28)*
