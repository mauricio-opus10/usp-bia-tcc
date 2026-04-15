# Resumo Executivo — Resultados Preliminares

**TCC MBA Business Intelligence & Analytics — USP/ECA**

**Título:** Teoria dos Grafos e Ciência de Redes na Comparação de Padrões Estruturais que Antecederam as Guerras Mundiais

**Aluno:** Maurício Gonçalves
**Orientador:** Prof. Paulo Henrique Assis Feitosa
**Data:** Janeiro/2026

---

## 1. Objetivo da Pesquisa

Aplicar técnicas de Business Intelligence e teoria dos grafos para comparar padrões estruturais nas redes de relações interestatais (alianças, comércio, disputas e diplomacia) nos períodos que antecederam a Primeira e a Segunda Guerra Mundial, identificando diferenças mensuráveis sem inferir causalidade.

**Pergunta de pesquisa:**
> Quais padrões estruturais mensuráveis nas redes interestatais diferenciam as janelas pré-1914 e pré-1939?

---

## 2. Metodologia

### 2.1 Janelas Temporais
| Período | Intervalo | Evento Final |
|---------|-----------|--------------|
| Pré-WWI | 1890–1914 | Primeira Guerra Mundial |
| Pré-WWII | 1925–1939 | Segunda Guerra Mundial |

### 2.2 Fontes de Dados
- **Correlates of War (COW):** Alianças v4.1, Comércio v4.0, MIDs v5.0, NMC v5.0
- **Intercâmbio Diplomático COW v2006.1**

### 2.3 Filtro de Estados
- Critério: CINC (Composite Index of National Capability) ≥ 1%
- Pré-WWI: 12 Estados | Pré-WWII: 13 Estados

### 2.4 Modelagem de Redes (4 Camadas)
| Camada | Nós | Arestas | Descrição |
|--------|-----|---------|-----------|
| **Alianças** | Estados | Pactos formais | Peso por tipo (defesa=4, entente=1) |
| **Comércio** | Estados | Fluxos bilaterais | Peso = volume comercial |
| **Disputas** | Estados | MIDs | Peso = nº de disputas |
| **Diplomacia** | Estados | Embaixadas | Peso = nível diplomático |

---

## 3. Resultados Principais

### 3.1 Métricas Globais das 4 Camadas

| Camada | Pré-WWI | Pré-WWII | Variação |
|--------|---------|----------|----------|
| **Alianças** | 38.2% densidade | 42.3% densidade | +4.1 pp |
| **Comércio** | 93.9% densidade | 98.7% densidade | +4.8 pp |
| **Disputas** | 59.1% densidade | 47.0% densidade | **-12.1 pp** |
| **Diplomacia** | 97.0% densidade | 100.0% densidade | +3.0 pp |

**Observação:** Todas as camadas apresentaram aumento de densidade no período pré-WWII, exceto Disputas, que após a correção metodológica (Side A vs Side B) mostrou redução de densidade com maior polarização.

### 3.2 Ranking de Conectividade (Pré-WWII)

```
1º Diplomacia ████████████████████████████████████████ 100%
2º Comércio   ███████████████████████████████████████  98.7%
3º Disputas   ███████████████████                      47.0%
4º Alianças   █████████████████                       42.3%
```

### 3.3 Análise de Brokers (Betweenness Centrality)

| Camada | Pré-WWI | Pré-WWII | Mudança |
|--------|---------|----------|---------|
| **Alianças** | Rússia (0.376) | Rússia (0.188) | Manteve liderança |
| **Disputas** | USA (0.186) | **Alemanha (0.136)** | **Inversão crítica** |
| **Comércio** | — | — | Sem brokers (rede densa) |
| **Diplomacia** | — | — | Sem brokers (grafo completo) |

**Destaque:** A Alemanha passou de 2º para 1º lugar como broker de disputas, enquanto os EUA saíram do centro dos conflitos.

---

## 4. Achados-Chave

### 4.1 O Paradoxo da Interdependência
O sistema internacional pré-WWII apresentava **máxima conectividade institucional**:
- Diplomacia: 100% (todos mantinham embaixadas com todos)
- Comércio: 98.7% (quase todos comerciavam entre si)

**Porém**, a rede de disputas apresentou densidade significativa (59.1% pré-WWI, 47.0% pré-WWII) com maior polarização no período pré-WWII (clustering +15%, modularidade +34%). Alta interdependência não impediu a escalada de conflitos — questionando teorias liberais de "paz pelo comércio".

### 4.2 Inversão Estrutural USA ↔ Alemanha

| País | Pré-WWI | Pré-WWII | Interpretação |
|------|---------|----------|---------------|
| **USA** | Broker central de disputas | Periférico | Isolacionismo pós-WWI |
| **Alemanha** | 2º em disputas | **Broker central** | Ascensão revisionista |

Esta mudança estrutural é consistente com a narrativa histórica e foi identificada objetivamente pelas métricas de rede.

### 4.3 Rússia: O Broker de Alianças
A Rússia manteve posição de principal intermediário na rede de alianças em ambos os períodos, conectando blocos diferentes do sistema. Seu betweenness caiu de 0.376 para 0.188, indicando menor papel de "ponte" no entreguerras.

---

## 5. Visualizações Geradas

| Arquivo | Descrição |
|---------|-----------|
| `brokers_comparacao.png` | Comparação lado a lado de brokers (Alianças vs Disputas) |
| `brokers_slope_disputas.png` | Mudança de posição dos países como brokers |
| `brokers_heatmap.png` | Heatmap de betweenness por país e camada |
| `brokers_top5_camadas.png` | Top 5 brokers em cada camada |

**Redes exportadas para Gephi:** 10 arquivos `.gexf` (4 camadas × 2 períodos + 2 multilayer)

---

## 6. Limitações

1. **Amostra pequena:** 12-13 Estados (grandes potências) — limita inferências estatísticas
2. **Agregação temporal:** Métricas agregadas por período, não capturam dinâmicas intra-período
3. **Dados históricos:** Possíveis vieses de registro em dados de disputas e comércio
4. **Sem causalidade:** Comparação estrutural descritiva, não explicativa

---

## 7. Próximos Passos

| Tarefa | Prioridade | Status |
|--------|------------|--------|
| Análise temporal ano a ano (snapshots) | Alta | Pendente |
| Teste de robustez (remover top-N nós) | Média | Pendente |
| Correlação CINC × centralidade | Média | Pendente |
| Análise de sobreposição entre camadas | Média | Pendente |
| Redação do capítulo de resultados | Alta | Pendente |

---

## 8. Conclusão Preliminar

A análise de redes multilayer revela diferenças estruturais mensuráveis entre os períodos pré-WWI e pré-WWII:

1. **Maior conectividade geral** no pré-WWII em todas as camadas
2. **Paradoxo da interdependência**: máxima integração coexistiu com aumento de disputas
3. **Mudança de brokers**: Alemanha substituiu USA como pivô de disputas

Estes achados demonstram a utilidade de técnicas de BI e ciência de redes para análise histórica estrutural, oferecendo uma perspectiva quantitativa complementar às narrativas tradicionais.

---

## Anexo: Dados Técnicos

### Estados Analisados

**Pré-WWI (12):** USA, Reino Unido, Bélgica, França, Espanha, Alemanha, Áustria-Hungria, Itália, Rússia, Turquia, China, Japão

**Pré-WWII (13):** USA, Brasil, Reino Unido, Bélgica, França, Espanha, Alemanha, Polônia, Tchecoslováquia, Itália, Rússia/URSS, China, Japão

### Ferramentas Utilizadas
- **Python:** pandas, networkx, matplotlib, seaborn
- **Visualização:** Gephi (arquivos .gexf)
- **Controle:** Git

---

*Documento gerado em Janeiro/2026*
*TCC MBA BI&A — USP/ECA*
