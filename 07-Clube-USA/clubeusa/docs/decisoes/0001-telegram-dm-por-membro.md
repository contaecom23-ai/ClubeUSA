# ADR 0001 — Telegram: broadcast por canal, sem DM por membro

- **Status:** Aceita
- **Data:** 2026-07-20
- **Contexto do time:** Clube USA

## Contexto

O `dealscanner2/scheduler.py` chama `_send_message(..., recipient=member["phone"], lang=...)`
para envios "por membro". No modo `MESSENGER="telegram"`, surgiu a pergunta:
deveríamos entregar deals em **DM individual** no Telegram (um `chat_id` por
membro), em vez de publicar apenas nos canais broadcast PT/ES?

## Restrição técnica determinante

No Telegram **não é possível enviar mensagem para um usuário pelo número de
telefone**. A Bot API só envia para um `chat_id`, e esse `chat_id` **só passa a
existir depois que o próprio usuário inicia conversa com o bot** (`/start`). Não
há lookup por telefone.

Isso difere do WhatsApp/Z-API, onde o número **é** o endereço de entrega. Logo,
`recipient=member["phone"]` nunca funciona como DM no Telegram — é limitação da
plataforma, não do código.

## Estado atual (o gap)

| Componente          | Situação                                                        |
|---------------------|-----------------------------------------------------------------|
| Modelo `members`    | Baseado em telefone (`phone_hash`, `phone_enc`). Sem colunas Telegram |
| Cadastro            | OTP via WhatsApp (`member_service.register_member`)             |
| Telegram hoje       | Apenas canais broadcast PT/ES (`TELEGRAM_CHANNEL_PT/ES`)        |
| Bot handler         | Inexistente (sem `/start`, webhook ou `getUpdates`)            |

## O que DM por membro exigiria

1. Coluna `telegram_chat_id` (+ `telegram_username`) em `members` — nova migration.
2. Webhook FastAPI recebendo updates do bot (`setWebhook`).
3. Fluxo de vínculo `/start` com deep link (`t.me/Bot?start=<token>`) ligando o
   `chat_id` ao `member.id`.
4. Ponto de entrada "conecte seu Telegram" no onboarding (hoje é WhatsApp).
5. Ajuste no `_send_message` para usar `member["telegram_chat_id"]` como destino.
6. Fallback para membros não vinculados (permanecem só no broadcast).

## Decisão

**Manter o modelo de broadcast por canal de idioma no Telegram. Não implementar
DM por membro no momento.**

Personalização individual permanece responsabilidade do **WhatsApp**, que já é DM
nativo por telefone e está funcionando.

## Justificativa

- **Fricção de conversão alta:** cada membro precisaria dar `/start` no bot só
  para receber DM — adoção baixa na prática.
- **Redundância de canal:** WhatsApp (DM real) + canais Telegram broadcast já
  cobrem os casos de uso; DM individual no Telegram não abre um novo.
- **Custo alto vs. valor incerto:** webhook + migration + fluxo de vínculo +
  mudança no onboarding para ganho marginal.

## Quando reabrir esta decisão

O gatilho que justificaria DM no Telegram é uma **migração do canal principal de
WhatsApp para Telegram** (custo menor, sem limites de API do Z-API). Nesse
cenário o `/start` deixa de ser fricção extra e passa a ser o próprio onboarding.

Ordem sugerida se reabrir: (1) webhook + fluxo `/start` com deep link para captar
o `chat_id`; (2) migration da coluna; (3) roteamento de envio.

## Consequências

- `_send_message` no modo `telegram` ignora `recipient` e publica no canal do
  idioma — comportamento documentado e intencional (ver `dealscanner2/sender.py`).
- Nenhuma coluna Telegram é adicionada ao schema por enquanto.
