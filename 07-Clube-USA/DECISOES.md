# DECISOES — Clube USA

> Fila de decisões que dependem do dono do produto.
> Claude NÃO age em itens desta lista sem aprovação explícita.
> Formato: contexto → pergunta → opções com prós/contras → recomendação → status

---

## Como usar

Responda a cada item pendente com sua decisão. O Claude pega o próximo item da fila na próxima rodada.

---

## Decisões Pendentes

### [2026-09-11] D-001: 30+ PRs abertos sem merge — estratégia urgente

**Contexto:** O agente criou 30+ PRs entre agosto e setembro. Nenhum foi mergeado. A main branch está sendo atualizada por commits diretos (o dono faz isso), enquanto o agente continua abrindo PRs que nunca chegam à main. Isso cria uma divergência crescente: o agente lê o código da main e trabalha baseado nele, mas as features dos PRs não existem na main. Resultado: o agente às vezes re-implementa o que já está em algum PR.

**Pergunta:** Como quer gerir os PRs acumulados?

**Opções:**
- **A — Fechar todos os PRs antigos, manter apenas os mais recentes de cada tema**: PRs de docs podem ser fechados (o estado real foi capturado no ROADMAP/DECISOES deste PR). PRs de feature precisam ser avaliados um a um. Pros: limpa a fila; Contras: pode perder features válidas.
- **B — Fazer squash-merge dos 2-3 PRs mais recentes e fechar os demais**: Só os de 2026-09 são relevantes. Pros: mantém progresso; Contras: pode conflitar com commits diretos na main.
- **C — Continuar como está, revisar quando tiver tempo**: Pros: zero esforço agora; Contras: a fila vai crescer indefinidamente, o agente fica num loop de docs sem código chegando à main.

**Recomendação:** **Opção A** + cherry-pick dos feature PRs úteis. Fechar todos os PRs de docs antigos (60–89 exceto este). Para os feature PRs (68, 65, 63, 62): revisar o diff de cada um rapidamente — se o código não conflita com a main, merge; se conflita, fechar e reimplementar.

**Minha decisão:** ___

**Status:** PENDENTE

---

### [2026-09-11] D-002: Auth por WhatsApp OTP vs email — reconciliar com ROADMAP

**Contexto:** O ROADMAP original dizia "email confirmado". O app que foi construído usa **telefone + OTP via WhatsApp** (Z-API). Várias PRs tentaram adicionar confirmação de email (PRs 84, 85, 87) — nenhuma foi mergeada. O produto atual funciona sem email obrigatório (email é campo opcional no cadastro).

**Pergunta:** Qual é a estratégia de auth definitiva?

**Opções:**
- **A — WhatsApp OTP apenas (design atual)**: Pros: simples, sem email marketing, funciona no BR onde WhatsApp é ubíquo; Contras: exige Z-API pago em produção, usuário precisa ter WhatsApp.
- **B — Email OTP como alternativa ao WhatsApp**: Pros: não depende de Z-API, mais barato; Contras: mais trabalho para implementar, email delivery tem problemas próprios (spam).
- **C — Ambos (WhatsApp principal, email como fallback)**: Pros: máxima cobertura; Contras: dobra a complexidade de auth.

**Recomendação:** **Opção A** no curto prazo (manter o que está construído). Se o Z-API virar bloqueador de custo, migrar para email OTP (B) no futuro — a abstração de `_otp_save/_otp_verify` já suporta isso. Atualizar o ROADMAP para refletir WhatsApp OTP (feito neste PR).

**Minha decisão:** ___

**Status:** PENDENTE

---

### [2026-09-11] D-003: Deploy — variáveis de ambiente necessárias

**Contexto:** O app não funciona sem as seguintes variáveis de ambiente configuradas no servidor (ex: Render):
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — banco de dados
- `ZAPI_INSTANCE` + `ZAPI_TOKEN` + `ZAPI_CLIENT_TOKEN` — WhatsApp OTP
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_VIP_PRICE_ID` — pagamentos
- `SECRET_KEY` — JWT signing
- `ADMIN_KEY` — acesso ao painel admin
- `APP_URL` — URL pública do app
- `ENVIRONMENT=production`

Sem essas variáveis, o app inicia mas falha em qualquer operação de negócio.

**Pergunta:** Essas variáveis já estão configuradas no Render (ou onde for deploiar)?

**Opções:**
- **A — Já estão configuradas**: Claude pode assumir que o deploy está funcional e focar em features.
- **B — Não estão / parcialmente**: Claude precisa saber qual serviço de deploy usar (Render? outro?) para criar `render.yaml` correto e documentar o setup.
- **C — Não há servidor ainda**: Bloqueador crítico. Precisamos de um plano de deploy antes de mais features.

**Recomendação:** Responda aqui para desbloquear o roadmap. Se C, veja `07-Clube-USA/clubeusa/DEPLOY_RENDER.md` para o plano já documentado.

**Minha decisão:** ___

**Status:** PENDENTE

---

### [2026-09-11] D-004: Formato do link de referral — `/i/{code}` vs `?ref={code}`

**Contexto:** O ROADMAP original especificava `/i/joao` como formato do link de referral (link curto amigável). O código atual usa `?ref={code}` (query param simples). Ambos funcionam tecnicamente; a diferença é UX e memorabilidade.

**Pergunta:** Qual formato quer usar?

**Opções:**
- **A — Manter `?ref={code}` (atual)**: Pros: zero esforço, já funciona; Contras: menos amigável, feio para compartilhar.
- **B — Implementar `/i/{code}` redirect**: Pros: URL limpa, profissional, rastreável; Contras: ~2h de trabalho (rota adicional + redirect para home capturando o código).

**Recomendação:** **Opção B** quando houver tempo — é simples e melhora percepção de profissionalismo para os influenciadores. Não urgente para os primeiros 1.000 usuários.

**Minha decisão:** ___

**Status:** PENDENTE

---

### [2026-09-11] D-005: Z-API (WhatsApp OTP) — plano e custo

**Contexto:** O sistema de OTP via WhatsApp depende de Z-API. Em desenvolvimento, o OTP é apenas logado (não enviado). Em produção (`ENVIRONMENT=production`), o app chama a API do Z-API. O plano gratuito do Z-API tem limites de mensagens.

**Pergunta:** O Z-API já está contratado e ativo com instância configurada?

**Opções:**
- **A — Sim, Z-API ativo**: Tudo pronto. Claude prossegue com features que dependem de WhatsApp.
- **B — Não / sem orçamento para Z-API**: Precisamos avaliar alternativas: Twilio SMS OTP (~$0.0075/SMS), email OTP (ver D-002), ou outro provedor WhatsApp.
- **C — Não sei / não decidi ainda**: Claude aguarda antes de implementar features que dependem de envio de mensagens.

**Recomendação:** Decida em conjunto com D-002 e D-003. Se o Z-API não estiver disponível, a auth inteira fica bloqueada em produção.

**Minha decisão:** ___

**Status:** PENDENTE

---

## Decisões Resolvidas

*(nenhuma ainda)*

---

*Atualizado em: 2026-09-11*
