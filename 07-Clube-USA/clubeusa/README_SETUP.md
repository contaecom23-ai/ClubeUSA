# Clube USA — Setup de Seguranca

## 1. Gerar chaves secretas

```bash
cd clubeusa
python utils/security.py
```

Cole as chaves geradas no seu `.env`.

## 2. Configurar .env

```bash
cp .env.example .env
# Edite .env com suas credenciais reais
```

## 3. Aplicar schema no Supabase

No painel do Supabase > SQL Editor:
1. Cole e execute `db/schema.sql`
2. Cole e execute `db/rpc_functions.sql`

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5. Variaveis obrigatorias

| Variavel | Onde obter |
|---|---|
| SUPABASE_URL | Supabase > Settings > API |
| SUPABASE_ANON_KEY | Supabase > Settings > API |
| SUPABASE_SERVICE_KEY | Supabase > Settings > API (nao expor no frontend) |
| ZAPI_INSTANCE | Z-API dashboard |
| ZAPI_TOKEN | Z-API dashboard |
| ZAPI_CLIENT_TOKEN | Z-API dashboard |
| ENCRYPTION_KEY | Gerado pelo script acima |
| JWT_SECRET | Gerado pelo script acima |
| APP_URL | URL publica do site (usada nos redirects do Stripe) |
| STRIPE_SECRET_KEY | Stripe > Developers > API keys |
| STRIPE_WEBHOOK_SECRET | Stripe > Developers > Webhooks (ver passo 6) |
| STRIPE_VIP_PRICE_ID | Stripe > Products > VIP ($4.99/mes) > Price ID |

## 6. Configurar o webhook do Stripe

O VIP so e ativado automaticamente quando o Stripe chama o webhook.

1. Aplique a migration: `db/stripe_migration.sql` no SQL Editor do Supabase.
2. No Stripe > Developers > Webhooks > **Add endpoint**:
   - URL: `https://SEU_DOMINIO/billing/webhook`
   - Eventos: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
3. Copie o **Signing secret** (`whsec_...`) para `STRIPE_WEBHOOK_SECRET` no `.env`.
4. Teste local com a CLI do Stripe:
   ```bash
   stripe listen --forward-to localhost:8000/billing/webhook
   stripe trigger checkout.session.completed
   ```

## Regras de seguranca que NUNCA podem ser quebradas

1. Nunca commitar .env no git
2. Nunca logar dados de PII (nome, telefone, email)
3. Nunca retornar dados criptografados para o frontend
4. Sempre validar inputs antes de qualquer operacao no banco
5. Sempre usar hash para busca — nunca buscar por dados em texto puro
6. Rotacionar ENCRYPTION_KEY e JWT_SECRET a cada 90 dias
