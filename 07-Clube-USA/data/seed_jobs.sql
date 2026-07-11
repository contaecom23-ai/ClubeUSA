-- Seed: vagas de emprego iniciais para a Fase 1.4
-- Curadas manualmente para a comunidade brasileira nos EUA.
-- Executar APÓS migration 006_jobs.sql e seed_zip_codes.sql.
--
-- Como adicionar mais vagas via API (recomendado para o dia a dia):
--   POST /admin/jobs   com header X-Admin-Key: <sua chave>
--
-- Este seed cobre as primeiras semanas antes de qualquer empresa fazer cadastro direto.

INSERT INTO jobs (title, company, description, category, job_type, zip_code, salary_range, apply_url)
VALUES

-- === MIAMI, FL (33101) ===
(
  'Auxiliar de Cozinha',
  'Restaurante Sabor Brasil',
  'Procuramos auxiliar de cozinha com experiência em culinária brasileira. '
  'Responsável por preparação de ingredientes, limpeza da cozinha e apoio ao chef. '
  'Horário: segunda a sábado, 10h às 18h. Benefícios: refeição no local.',
  'restaurante', 'full_time', '33101',
  '$15-17/hr',
  NULL
),
(
  'Motorista de Entrega (Próprio veículo)',
  'Marmitas da Família',
  'Preciso de motorista confiável para entrega de marmitas na região de Miami. '
  'Rotas fixas, pagamento por entrega. Veículo próprio necessário (reembolso de gasolina). '
  'Horário flexível, ideal para complementar renda.',
  'motorista', 'gig', '33101',
  '$18-22/hr + gorjeta',
  NULL
),
(
  'Faxineira / House Cleaner',
  'Limpeza Premium Miami',
  'Contratamos faxineiras para limpeza residencial e comercial em Miami-Dade. '
  'Treinamento fornecido, produtos da empresa. Carro próprio é diferencial. '
  'Pagamento semanal. Fala português e inglês básico.',
  'limpeza', 'part_time', '33101',
  '$16-20/hr',
  NULL
),

-- === ORLANDO, FL (32801) ===
(
  'Pedreiro / Ajudante de Construção',
  'Construtora BrasilBuilds',
  'Contratamos pedreiros e ajudantes para obras residenciais na região de Orlando. '
  'Experiência com alvenaria, reboco e acabamento. Carteira de habilitação americana desejável. '
  'Pagamento semanal. Empresa de brasileiros para brasileiros.',
  'construcao', 'full_time', '32801',
  '$20-28/hr dependendo da experiência',
  NULL
),
(
  'Babá / Cuidadora de Crianças',
  'Família Americana (referência via agência)',
  'Família americana em Orlando busca babá brasileira para crianças de 2 e 5 anos. '
  'Horário: segunda a sexta, 8h às 17h. Inglês intermediário necessário. '
  'Ambiente familiar, respeitoso. Recomendações exigidas.',
  'cuidado', 'full_time', '32801',
  '$15-18/hr',
  NULL
),

-- === BOSTON, MA (02101) ===
(
  'Manicure / Pedicure',
  'Nail Studio Boston',
  'Salão de beleza brasileiro em Boston busca manicure e pedicure experiente. '
  'Licença de cosmetologia de Massachusetts necessária (ajudamos no processo). '
  'Comissão de 40-50% + gorjetas. Clientela fidelizada.',
  'beleza', 'full_time', '02101',
  '40-50% comissão',
  NULL
),
(
  'Auxiliar Administrativo / Recepcionista',
  'Brazilian Services LLC',
  'Empresa de serviços brasileiros em Boston busca recepcionista bilíngue (PT/EN). '
  'Atendimento ao cliente, agendamentos, controle de documentos. '
  'Horário: 9h-18h, segunda a sexta. Experiência de atendimento ao público necessária.',
  'escritorio', 'full_time', '02101',
  '$18-22/hr',
  NULL
),

-- === NEW YORK, NY (10001) ===
(
  'Entregador de Bicicleta / E-bike',
  'Deliveries NY',
  'Vagas para entregadores de bicicleta/e-bike em Manhattan e Brooklyn. '
  'Trabalhe pelos apps (DoorDash, Uber Eats) ou conosco diretamente. '
  'Pagamento diário ou semanal. Bicicleta elétrica da empresa disponível (taxa de aluguel).',
  'motorista', 'gig', '10001',
  '$800-1.400/semana (média da região)',
  NULL
),
(
  'Zelador / Porter de Prédio',
  'Administradora de Condomínios NYC',
  'Procuramos zelador para prédio residencial no Astoria, Queens. '
  'Responsabilidades: limpeza das áreas comuns, coleta de lixo, pequenos reparos. '
  'Inglês básico necessário. Apartamento no prédio incluído no pacote (negociável).',
  'limpeza', 'full_time', '10001',
  '$22-26/hr + benefícios',
  NULL
),

-- === LOS ANGELES, CA (90001) ===
(
  'Garçom / Garçonete',
  'Churrascaria do Bairro',
  'Churrascaria brasileira em Los Angeles busca garçons com experiência. '
  'Inglês intermediário necessário (clientela mista). Horários de almoço e jantar. '
  'Salário base + gorjetas. Uniforme fornecido.',
  'restaurante', 'part_time', '90001',
  '$16/hr + gorjetas',
  NULL
),
(
  'Cuidadora de Idosos (CNA / HHA)',
  'BrazilCare Home Services',
  'Empresa brasileira especializada em cuidado de idosos em Los Angeles busca cuidadoras. '
  'Certificação CNA ou HHA necessária (ajudamos na obtenção). '
  'Horários flexíveis, plantões diurnos e noturnos. Pagamento semanal.',
  'cuidado', 'full_time', '90001',
  '$17-22/hr',
  NULL
),

-- === HOUSTON, TX (77001) ===
(
  'Pintor Residencial',
  'Pinturas Texas',
  'Empresa de pintura residencial em Houston contrata pintores com experiência. '
  'Trabalho interno e externo. Ferramentas e materiais fornecidos. '
  'Pagamento por projeto ou hora. CNH necessária para transporte até obra.',
  'construcao', 'contract', '77001',
  '$18-25/hr',
  NULL
),

-- === NACIONAL (sem ZIP — aparece em todas as buscas) ===
(
  'Desenvolvedor(a) Web Remoto',
  'StartupBR USA',
  'Startup brasileira nos EUA busca dev web para trabalho 100% remoto. '
  'Stack: React, Node.js, PostgreSQL. Inglês intermediário desejável. '
  'Contrato PJ. Projeto de 3-6 meses com possibilidade de extensão.',
  'tecnologia', 'contract', NULL,
  '$35-55/hr',
  NULL
),
(
  'Atendente de Telemarketing (PT/EN) — Remoto',
  'BrasilConnect Services',
  'Empresa de serviços para brasileiros nos EUA busca atendentes bilíngues (PT/EN). '
  '100% remoto. Atendimento por telefone e chat. Computador e internet de qualidade necessários. '
  'Treinamento pago. Horário flexível (turnos disponíveis).',
  'vendas', 'part_time', NULL,
  '$15-18/hr',
  NULL
)

ON CONFLICT DO NOTHING;
