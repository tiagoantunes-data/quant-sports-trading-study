# Trading Desportivo Quantitativo — Proposta Técnica Fase 1

**Para:** Tiago Antunes
**Natureza:** Investigação quantitativa. Não é uma atividade recreativa.
**Pergunta central:** Existe uma vantagem estatística explorável e sustentável? Se não, encerramos.
**Data:** 17 de junho de 2026
**Postura:** Crítica. O objetivo não é validar a ideia — é tentar destruí-la com dados. Se sobreviver, talvez valha a pena.

---

## 0. Conclusão antecipada (lê isto primeiro)

Antes de qualquer entusiasmo, três verdades duras que condicionam tudo o resto:

**1. Em Portugal, o modelo de exchange é proibido.** Nenhuma exchange (Betfair Exchange, Smarkets, Matchbook) tem licença do SRIJ. O modelo de "troca" entre apostadores não está regulado e, por isso, não é autorizado. Aceder via VPN é possível, mas significa operar num site não-licenciado: perdes proteção do consumidor, arriscas o congelamento/não-recuperação de fundos, e — ponto fiscal importante — os ganhos deixam de estar isentos. Em plataformas com licença SRIJ os ganhos do jogador são isentos de IRS; em sites ilegais os ganhos podem ser tratados como rendimento tributável. Ou seja: **o caminho de dinheiro real com exchange, a partir de Portugal, esbarra num muro legal e fiscal antes sequer de discutirmos matemática.**

**2. O mercado é, na prática, eficiente.** A linha de fecho (closing line), sobretudo da Pinnacle, é o melhor estimador conhecido da probabilidade real. Erros óbvios são arbitrados em segundos. Qualquer edge que exista é pequena, rápida e tem de ser sistemática. A comissão da exchange (2% a 6%) come grande parte — ou a totalidade — de uma edge fina.

**3. Com 200–500 operações, o lucro simulado é estatisticamente ruído.** Isto é matemática, não opinião (demonstro na secção 6). Uma amostra desse tamanho **não consegue** confirmar uma edge de 2–4%. Por isso a Fase 1 **não** pode ter o ROI como métrica principal de decisão. A métrica principal tem de ser o **CLV (Closing Line Value)**, que dá sinal em cada aposta independentemente do resultado.

**Implicação prática:** A Fase 1 é legítima e vale a pena fazer — **mas como experiência puramente intelectual, em simulação, sem qualquer conta de exchange e sem qualquer dinheiro.** Não tem exposição legal nenhuma porque não há aposta real. Serve para responder a uma única pergunta honesta: *o meu modelo consegue, de forma sistemática e fora-da-amostra, obter preços melhores do que a linha de fecho?* Se a resposta for não, paramos — e poupámos tempo e dinheiro. Se for sim, aí sim discutimos se há sequer um caminho legal para o explorar.

A burden of proof está toda do lado da ideia. Vamos desenhar a Fase 1 para que ela possa ser **falsificada**.

---

## 1. Como funciona o acesso de residentes portugueses a exchanges

O regulador é o SRIJ (Serviço de Regulação e Inspeção de Jogos, sob a Inspeção-Geral de Jogos). Desde a lei de 2015 e a emissão de licenças a partir de 2016, todos os operadores online precisam de licença local. As exchanges nunca pediram autorização porque o **modelo de exchange (apostador contra apostador, com a casa a cobrar comissão) não está previsto no regime português** — só está previsto o modelo de odds fixas (sportsbook). A Betfair fechou o acesso a utilizadores portugueses; a marca opera em Portugal apenas como sportsbook licenciado, não como exchange.

Consequência: a partir de Portugal, **não existe acesso legal a uma exchange.** As únicas vias são:

- **VPN / endereço estrangeiro:** tecnicamente possível, mas viola os termos do operador e o enquadramento português. Risco real de bloqueio de conta e não-pagamento de levantamentos, sem recurso junto de autoridade portuguesa.
- **Conta noutra jurisdição (residência fiscal estrangeira):** fora do âmbito deste projeto.

Para a **Fase 1 isto é irrelevante**, porque não vamos abrir conta nem apostar. Mas é decisivo para qualquer fase posterior, e é por isso que aparece logo no topo.

## 2. Enquadramento legal e fiscal (síntese)

- **Apostas em operador com licença SRIJ:** legais; ganhos do jogador **isentos de IRS** (o operador paga o IEJO — 8% sobre apostas desportivas). Não há obrigação de declarar.
- **Apostas em site sem licença (inclui exchanges via VPN):** atividade não autorizada; ganhos podem ser considerados rendimento e ficar **sujeitos a IRS**; sem proteção do consumidor; risco de fundos.
- **Exchange = modelo não regulado em PT:** não há sequer um operador de exchange licenciado a quem recorrer.

Tradução: o sistema fiscal português, paradoxalmente, **pune o caminho da exchange** (o teoricamente mais eficiente) e **premeia o sportsbook licenciado** (onde a edge é mais difícil porque a margem da casa é maior e as contas vencedoras são limitadas). Esta tensão tem de estar consciente desde o início.

## 3. Exchanges mais usadas por profissionais (e o custo real)

| Exchange | Comissão padrão | Notas |
|---|---|---|
| **Betfair Exchange** | ~6% (desde jun. 2026), desce até 2% em alto volume | A maior liquidez do mundo. Em jan. 2025 acabou com a Premium Charge e introduziu a *Expert Fee*: 20% sobre lucros £25k–100k, 40% acima de £100k. Penaliza precisamente quem ganha de forma consistente. |
| **Smarkets** | 2% (Pro 1%) | Comissão baixa e previsível; liquidez menor que Betfair. |
| **Matchbook** | 2% (UK/IE), 4% fora | Sem Premium Charge — atrativa para vencedores consistentes; liquidez seletiva por mercado. |

**Leitura crítica:** a comissão não é um detalhe — é o adversário estrutural. Se o teu yield bruto for, digamos, +3%, uma comissão de 2–5% sobre os ganhos pode reduzir o líquido a perto de zero. Além disso, as estruturas tipo Expert Fee da Betfair existem **exatamente para confiscar a edge de quem a tem.** Qualquer modelo financeiro tem de assumir a comissão no pior cenário realista (assumir 2% Smarkets como base e testar a 5% Betfair como stress test).

## 4. Recolha automatizada de odds

Para testar a hipótese precisamos de duas coisas em cada jogo: **(a) odds disponíveis antes do fecho** (onde apostaríamos) e **(b) odds de fecho**, idealmente da Pinnacle (a referência "sharp"). Sem a linha de fecho não há CLV, e sem CLV não há Fase 1 honesta.

**Fontes recomendadas (por ordem de prioridade para arrancar):**

1. **football-data.co.uk** — histórico gratuito de várias ligas (incl. Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Liga Portugal) com odds de abertura e fecho de várias casas, incluindo Pinnacle. Ideal para o backtest inicial sem custo nem scraping.
2. **The Odds API** (the-odds-api.com) — API limpa para odds pré-jogo em tempo quase real, plano gratuito ~500 pedidos/mês; planos pagos baratos. Boa para a simulação *forward* (em tempo real).
3. **Pinnacle (odds devigadas)** como benchmark de probabilidade "justa".
4. Scraping (OddsPortal e afins) — só se necessário; mais frágil e legalmente cinzento. Evitar enquanto as duas primeiras chegarem.

**Princípio LUXAR aplicado:** nenhum dado é assumido. Cada odd guardada tem timestamp, fonte e snapshot. Se não conseguimos explicar de onde veio, não entra na base.

## 5. Do mercado ao sinal: como se identifica value

### 5.1 O modelo de probabilidade
Há duas filosofias. Recomendo começar pela primeira porque é a mais defensável e a mais difícil de auto-enganar:

**Opção A — Benchmark de mercado (devig da Pinnacle). [RECOMENDADA PARA ARRANCAR]**
A Pinnacle é empiricamente o estimador mais afiado. Tira-se a margem ("vig") das suas odds para obter a probabilidade justa. O "modelo" é, portanto, o próprio mercado sharp. Um value bet existe quando **outra casa/exchange oferece odds superiores às odds justas da Pinnacle**. Lógica: se nem conseguires bater a Pinnacle usando a própria Pinnacle como verdade, um modelo caseiro quase de certeza não a vai bater.

- Probabilidade justa: `p_justa = (1/odd_pinn) / soma_das_inversas` (remove o vig, método multiplicativo; testar também shin/aditivo).
- Sinal de value: `edge = p_justa × odd_oferecida − 1`. Aposta-se quando `edge > limiar` (ex. > 2–3% para cobrir comissão e ruído).

**Opção B — Modelo estatístico próprio (Dixon-Coles / Poisson bivariada, ou Elo / xG).**
Estimar diretamente a probabilidade dos resultados a partir de golos, xG, força das equipas. Mais ambicioso, muito mais fácil de overfit. **Só faz sentido depois** de a Opção A mostrar que a infraestrutura funciona — e mesmo aí, a vara de medir é sempre se bate a Pinnacle.

### 5.2 As tuas regras, traduzidas em filtros de código
1. Banca total perdida → STOP definitivo. → *kill-switch* no sistema.
2. Máx. 2% por operação. → staking plano a 2% ou Kelly fracionado **com teto rígido em 2%**.
3. Zero decisão emocional/discricionária. → nenhuma aposta sem sinal do sistema; sem overrides manuais.
4. Só oportunidades matematicamente favoráveis. → `edge > limiar` obrigatório.
5. Odds entre 1.65 e 2.50. → filtro duro (prob. implícita ~40%–60.6%; zona onde os modelos têm mais margem e a margem proporcional da casa tende a ser menor).
6. Nunca múltiplas. → só singles. (Concordo tecnicamente: múltiplas multiplicam a margem da casa e a variância.)

## 6. Por que 200–500 operações não chega para provar lucro (e o que fazer)

Este é o ponto mais importante de toda a proposta. **Não o ignores.**

O lucro/prejuízo de uma aposta a odd ~2.0 tem desvio-padrão de ~1.0 unidade de stake por aposta (ganhas +1 ou perdes −1). Para detetar um yield verdadeiro de 3% com significância estatística (95%):

```
n ≈ (z · σ / efeito)²  ≈  (1.96 × 1.0 / 0.03)²  ≈  4.270 apostas
```

Ou seja: para *confirmar* uma edge de 3% pelo ROI, precisarias de **milhares** de apostas, não 300. Com 300 apostas, um yield simulado de +5% ou de −5% é perfeitamente compatível com uma edge real de zero. **O ROI numa amostra pequena é ruído com aparência de sinal — e é exatamente assim que apostadores se auto-enganam.**

**Solução — usar o CLV como métrica primária.** O CLV mede, em cada aposta, se obtiveste um preço melhor do que a linha de fecho. Tem duas propriedades decisivas:
- Dá sinal **em todas as apostas**, não só nas que ganham → muito menos variância → exige amostra muito menor.
- É o **único preditor empiricamente robusto** de lucro a longo prazo. Bater a linha de fecho em ~2% tende a corresponder a ~4% de ROI no longo prazo.

Se em 200–500 apostas simuladas o teu CLV médio for **positivo e estatisticamente distinguível de zero**, tens evidência preliminar de edge. Se for ≤ 0, **não há edge — e paramos, sem drama.**

**Detalhe crítico anti-auto-engano:** o teste só vale se for *out-of-sample / forward*. Backtest em dados históricos sobreajusta-se trivialmente. O verdadeiro teste é: o sistema regista a aposta com o preço disponível **antes** do fecho, e só **depois** observamos a odd de fecho e o resultado. Sem olhar para o futuro.

## 7. Arquitetura do sistema Fase 1 (simulação, zero dinheiro)

Reaproveita a mentalidade do pipeline LUXAR: recolha agendada, base de dados, snapshots, métricas, tudo auditável.

```
┌─ 1. COLETOR ──────────────────────────────────────────────┐
│  Cron diário. The Odds API + football-data (histórico).   │
│  Guarda snapshot: jogo, casa, mercado, odd, timestamp,    │
│  fonte. Inclui odd Pinnacle (benchmark) + odd "alvo".     │
└───────────────────────────────────────────────────────────┘
                          │
┌─ 2. BASE DE DADOS (SQLite) ───────────────────────────────┐
│  matches · odds_snapshots · signals · paper_bets ·        │
│  results · clv_log                                        │
└───────────────────────────────────────────────────────────┘
                          │
┌─ 3. MOTOR DE PROBABILIDADE ───────────────────────────────┐
│  Devig Pinnacle → p_justa (Opção A). Módulo trocável      │
│  para futuro modelo próprio (Opção B).                    │
└───────────────────────────────────────────────────────────┘
                          │
┌─ 4. GERADOR DE SINAIS ────────────────────────────────────┐
│  edge = p_justa × odd_alvo − 1                            │
│  Filtros: odd∈[1.65,2.50] · edge>limiar · só singles      │
│  Stake = 2% (teto rígido).                                │
└───────────────────────────────────────────────────────────┘
                          │
┌─ 5. SETTLEMENT + CLV ─────────────────────────────────────┐
│  Após o jogo: regista resultado e odd de FECHO.           │
│  CLV = (odd_apostada / odd_fecho) − 1  (ajustado p/ vig). │
│  P/L simulado com comissão (2% base; 5% stress).          │
└───────────────────────────────────────────────────────────┘
                          │
┌─ 6. PAINEL DE MÉTRICAS ───────────────────────────────────┐
│  CLV médio (+IC bootstrap) ◄ MÉTRICA PRIMÁRIA            │
│  Yield · ROI · Max Drawdown · hit rate · nº apostas       │
│  Quebra por liga e por janela temporal (robustez).        │
│  Liga ao LUXAR_Trading_Dashboard.xlsx existente.          │
└───────────────────────────────────────────────────────────┘
```

**Stack:** Python (já tens via Anaconda), `requests`, `pandas`, `numpy`, `scipy` (testes), SQLite, e o teu Excel existente como camada de visualização. Sem infraestrutura nova pesada.

## 8. Métricas e definições exatas

- **CLV (primária):** média de `(odd_apostada / odd_fecho_justa) − 1`. Sucesso: média > 0 com intervalo de confiança 95% (bootstrap) **a excluir o zero**. Alvo mínimo de interesse: **+1.5%**.
- **Yield:** lucro líquido / total apostado (já com comissão). Secundária — indicativa, não conclusiva nesta amostra.
- **ROI:** lucro líquido / banca. Secundária.
- **Max Drawdown:** maior queda pico-a-vale da banca simulada. Mede tolerabilidade psicológica e de risco de ruína.
- **Robustez:** a edge tem de aparecer em mais do que uma liga e não estar concentrada em 5 apostas sortudas. Teste: remover o top 5% de apostas por lucro e ver se o CLV se mantém positivo.

## 9. Critério de decisão Go / No-Go (definido ANTES de correr)

Definir os critérios antes de ver os resultados é o que separa ciência de auto-engano. Comprometemo-nos a isto agora:

**PARAR (encerrar o projeto) se, após 200–500 apostas forward:**
- CLV médio ≤ 0, **ou**
- CLV positivo mas com IC 95% a incluir o zero (i.e., indistinguível de sorte), **ou**
- A edge só existe antes da comissão e desaparece com 2% de comissão.

→ Conclusão escrita, honesta: *"Não existe vantagem comprovável. Encerramos."* Sem reinvestir, sem "mais uma tentativa".

**CONTINUAR para Fase 2 (planeamento) apenas se:**
- CLV médio ≥ +1.5% com IC 95% acima de zero, **e**
- robusto entre ligas e janelas temporais, **e**
- yield simulado positivo líquido de 2% de comissão, **e** — separadamente — existir um caminho legal/fiscal viável (o muro da secção 1 tem de ser resolvido antes de um único euro real).

## 10. Plano faseado

**Fase 1 — Validação sem dinheiro (4–8 semanas de recolha + análise).** Construir o sistema das secções 7–8. Backtest histórico (football-data) para calibrar e *depois* simulação forward (The Odds API) para o teste real de CLV. Decisão Go/No-Go pela secção 9.

**Fase 2 — Só se Fase 1 passar: replicação e resolução do muro legal.** Aumentar a amostra para milhares de apostas em paper trading (para o ROI ganhar significância), e — em paralelo — esclarecer o enquadramento legal/fiscal. Sem caminho legal limpo, o projeto pode estar *intelectualmente validado mas ser inexecutável em Portugal* com exchange. É preciso dizer isto sem rodeios.

**Fase 3 — Só se Fase 2 passar: micro-stakes reais.** Banca pequena, stake real ≤ 2%, durante meses, a comparar resultados reais com a simulação. A execução real introduz fricções que o paper trading ignora (nem sempre és emparelhado ao preço, impacto de mercado, latência). Espera-se que o resultado real seja **pior** que o simulado.

## 11. Riscos que podem matar o projeto (e devemos querer descobri-los cedo)

1. **Regulatório/fiscal (PT):** o mais provável de inviabilizar dinheiro real. Já discutido.
2. **Eficiência de mercado:** a edge pode simplesmente não existir para um operador retail. É o resultado mais provável a priori — e está tudo bem, é o que queremos testar.
3. **Comissão:** mesmo com edge bruta, o líquido pode ser ≤ 0.
4. **Expert Fee / limitação de contas:** as plataformas confiscam ou limitam vencedores consistentes.
5. **Execução vs. simulação:** paper trading com CLV positivo **não garante** lucro real — sobrestima sempre.
6. **Amostra pequena:** o risco de concluir "tenho edge" a partir de ruído. Mitigado por usar CLV e fixar critérios à priori.

---

## Veredicto honesto

A pergunta que fizeste — *"existe ou não edge matemática sustentável?"* — é exatamente a pergunta certa, e a postura de encerrar sem drama se a resposta for não é a postura certa. A maioria das pessoas neste domínio perde precisamente por não a fazer.

A minha previsão, antes de correr o sistema: a probabilidade de encontrares uma edge *líquida de comissão, legalmente explorável a partir de Portugal* é **baixa**. O mercado é eficiente, a comissão é alta, e o enquadramento PT é hostil ao único modelo (exchange) onde a edge seria mais plausível.

Mas isso é uma previsão, não um facto — e o custo de a testar em simulação é só tempo de engenharia, zero dinheiro e zero risco legal. Por isso vale a pena fazer a Fase 1, **desde que** aceites de antemão o critério de paragem e que a métrica de decisão é o CLV, não o lucro simulado. Se o CLV não aparecer, dizemo-lo em voz alta e seguimos para outra coisa — provavelmente com mais leverage — sem olhar para trás.
