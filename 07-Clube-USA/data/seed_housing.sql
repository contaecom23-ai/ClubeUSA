-- Seed: 15 anúncios de moradia curados — comunidades brasileiras nos EUA
-- Rodar APÓS migration 007_housing.sql e seed_zip_codes.sql
-- NOTA: latitudes/longitudes são populadas via aplicação ao criar; aqui ficam null
--       pois o seed vai direto no banco. Rodar update manual ou via admin API.

INSERT INTO housing (
    title, description, listing_type,
    zip_code, city, state,
    rent_monthly_cents, bedrooms, bathrooms,
    furnished, utilities_included, pets_allowed,
    available_from, contact_email, contact_phone, active
) VALUES

-- MIAMI / FORT LAUDERDALE (FL) — maior comunidade brasileira do sul da FL
(
    'Quarto em casa compartilhada — Brickell, Miami',
    'Quarto mobiliado disponível em casa com 3 quartos. Casa limpa, organizada. 2 moradores brasileiros. A/C central, Wi-Fi incluído, estacionamento. 10 minutos do metrô. Dividimos despesas de casa.',
    'quarto_disponivel',
    '33129', 'Miami', 'FL',
    120000, 1, 2.0,
    true, true, false,
    '2026-08-01T00:00:00Z', 'moradia.miami1@clubeusa.com', NULL, true
),
(
    'Procuro roommate — Little Havana, Miami',
    'Brasileira 28 anos, trabalho em restaurante, procuro roommate para dividir apartamento 2/2. Aluguel atual $2.400/mês, você paga metade. Apartamento no 3º andar, condomínio com piscina. Área segura.',
    'precisa_quarto',
    '33135', 'Miami', 'FL',
    120000, 2, 2.0,
    false, false, false,
    '2026-07-20T00:00:00Z', 'moradia.miami2@clubeusa.com', NULL, true
),
(
    'Apartamento 1/1 para alugar — Doral (região brasileira)',
    'Apartamento 1 quarto e 1 banheiro em Doral. Condomínio com piscina, academia e segurança 24h. 5 min do Walmart Supercenter. Ótima localização para brasileiros. Disponível 1º de agosto.',
    'casa_disponivel',
    '33122', 'Doral', 'FL',
    190000, 1, 1.0,
    false, false, true,
    '2026-08-01T00:00:00Z', 'moradia.doral@clubeusa.com', NULL, true
),

-- ORLANDO (FL) — segunda maior concentração brasileira na FL
(
    'Quarto disponível — Kissimmee, perto da Disney',
    'Quarto em casa de família brasileira. Casa com 4 quartos, 2 banheiros. Cozinha compartilhada, lavanderia inclusa. A/C, Wi-Fi, água e luz incluídos no aluguel. Ótimo para quem trabalha em hotel ou resort.',
    'quarto_disponivel',
    '34741', 'Kissimmee', 'FL',
    95000, 1, 2.0,
    true, true, false,
    '2026-07-15T00:00:00Z', 'moradia.kissimmee@clubeusa.com', NULL, true
),
(
    'Apartamento 2/2 para dividir — Orlando',
    'Procuro 1 pessoa para dividir apartamento 2 quartos e 2 banheiros em Orlando. Apartamento novo (2022), piscina no condomínio. Internet 1Gbps incluída. Cada um paga $900/mês + luz.',
    'precisa_quarto',
    '32801', 'Orlando', 'FL',
    90000, 2, 2.0,
    false, true, false,
    '2026-08-01T00:00:00Z', 'moradia.orlando@clubeusa.com', NULL, true
),

-- BOSTON / CAMBRIDGE (MA) — comunidade brasileira histórica no Nordeste
(
    'Quarto em Somerville — próximo ao metrô T',
    'Quarto disponível em apartamento com 3 moradores (todos brasileiros). 5 min a pé da estação Davis Square (Red Line). Bairro seguro, muitos restaurantes e cafés. Conta de luz dividida, Wi-Fi incluído.',
    'quarto_disponivel',
    '02143', 'Somerville', 'MA',
    140000, 1, 1.0,
    true, true, false,
    '2026-08-15T00:00:00Z', 'moradia.somerville@clubeusa.com', NULL, true
),
(
    'Studio para alugar — Allston (Boston)',
    'Studio reformado em Allston. Aquecimento incluído (importante no inverno de Boston!). Cozinha completa, banheiro privativo. 10 min de ônibus da Universidade de Boston e Northeastern.',
    'casa_disponivel',
    '02134', 'Boston', 'MA',
    180000, 0, 1.0,
    true, true, false,
    '2026-09-01T00:00:00Z', 'moradia.boston@clubeusa.com', NULL, true
),

-- NEWARK / ELIZABETH (NJ) — maior comunidade brasileira de NJ
(
    'Quarto disponível — Newark, NJ (perto do PATH train)',
    'Quarto mobiliado em apartamento 3/1 em Newark. 3 moradores brasileiros. PATH train a 10 min de caminhada — acesso direto ao centro de NY em 20 minutos. Ótimo custo-benefício para trabalhar em NY morando em NJ.',
    'quarto_disponivel',
    '07102', 'Newark', 'NJ',
    100000, 1, 1.0,
    true, true, false,
    '2026-07-20T00:00:00Z', 'moradia.newark@clubeusa.com', NULL, true
),
(
    'Casa 4 quartos para alugar — Elizabeth, NJ',
    'Casa com 4 quartos e 2 banheiros para família ou grupo. Garagem, quintal. Boa localização em Elizabeth — perto de supermercados, igrejas brasileiras e transporte público. Aluguel $3.200/mês. Deposito 1 mês.',
    'casa_disponivel',
    '07201', 'Elizabeth', 'NJ',
    320000, 4, 2.0,
    false, false, true,
    '2026-08-01T00:00:00Z', 'moradia.elizabeth@clubeusa.com', NULL, true
),

-- NEW YORK (NY) — comunidade brasileira significativa no Queens e Bronx
(
    'Quarto em apartamento — Astoria, Queens, NY',
    'Quarto em apartamento dividido no bairro Astoria (Queens). 2 moradores brasileiros. Metrô N/W a 5 minutos. Acesso rápido ao centro de Manhattan. Ideal para quem trabalha na cidade. Sem animais.',
    'quarto_disponivel',
    '11102', 'Astoria', 'NY',
    160000, 1, 1.0,
    true, false, false,
    '2026-08-01T00:00:00Z', 'moradia.queens@clubeusa.com', NULL, true
),
(
    'Procuro roommate — Bronx, NY',
    'Brasileiro 35 anos, trabalho em construção civil, procuro roommate sério para dividir quarto em apartamento no Bronx. Aluguel $800/mês cada. Apartamento limpo. Sem festas. Perto da linha 4/5/6.',
    'precisa_quarto',
    '10451', 'Bronx', 'NY',
    80000, 1, 1.0,
    false, false, false,
    '2026-07-15T00:00:00Z', 'moradia.bronx@clubeusa.com', NULL, true
),

-- LOS ANGELES (CA) — comunidade crescente no sul da CA
(
    'Quarto em casa — Palms, West LA',
    'Quarto em casa de 3 quartos em Palms (West LA). 2 moradores, ambiente tranquilo. Ônibus direto para Santa Monica e UCLA. Wi-Fi rápido incluído. Ideal para trabalho remoto.',
    'quarto_disponivel',
    '90034', 'Los Angeles', 'CA',
    145000, 1, 1.0,
    true, true, false,
    '2026-08-01T00:00:00Z', 'moradia.la@clubeusa.com', NULL, true
),

-- HOUSTON (TX) — comunidade brasileira crescente
(
    'Apartamento 2/2 para alugar — Galleria, Houston',
    'Apartamento 2 quartos e 2 banheiros no bairro Galleria. Condomínio com academia e piscina. Aluguel $1.700/mês + utilidades. Perto de restaurantes, shoppings e área de trabalho. Disposto a negociar para família.',
    'casa_disponivel',
    '77056', 'Houston', 'TX',
    170000, 2, 2.0,
    false, false, true,
    '2026-08-15T00:00:00Z', 'moradia.houston@clubeusa.com', NULL, true
),

-- CHICAGO (IL)
(
    'Quarto disponível — Pilsen, Chicago',
    'Quarto grande em apartamento de 2 andares em Pilsen. Bairro cultural com muita vibração. Metrô Pink Line a 3 min. Moradores: 2 brasileiros e 1 mexicano. Ambiente multicultural e acolhedor.',
    'quarto_disponivel',
    '60608', 'Chicago', 'IL',
    110000, 1, 1.5,
    false, false, false,
    '2026-07-25T00:00:00Z', 'moradia.chicago@clubeusa.com', NULL, true
),

-- ATLANTA (GA) — comunidade brasileira em crescimento
(
    'Casa 3 quartos para dividir — Gwinnett County, Atlanta',
    'Casa espaçosa em Lawrenceville (Gwinnett) para dividir com outros moradores. 3 quartos disponíveis — pode ser família ou grupo. Quintal grande. Perto de igrejas brasileiras, mercados e restaurantes da comunidade.',
    'quarto_disponivel',
    '30043', 'Lawrenceville', 'GA',
    85000, 3, 2.0,
    false, false, true,
    '2026-08-01T00:00:00Z', 'moradia.atlanta@clubeusa.com', NULL, true
);
