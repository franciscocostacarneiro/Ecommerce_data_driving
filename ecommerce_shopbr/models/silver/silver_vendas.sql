-- sempre referenciando a camada bronze para que seja um ciclo que se retroalimentará automaticamente.
-- aqui começa a lógica de negócio
SELECT
    v.id_venda,
    v.data_venda,
    v.id_cliente,
    v.id_produto,
    v.canal_venda,
    v.quantidade,
    v.preco_unitario::NUMERIC(10,2) as preco_venda,
    --criando uma coluna calculada
    v.quantidade * v.preco_unitario::NUMERIC(10,2) as receita_total,
    --crindo dimensões temporais
    DATE(v.data_venda::timestamp) AS data_venda_date,
    EXTRACT(YEAR FROM v.data_venda::timestamp) AS ano_venda,
    EXTRACT(MONTH FROM v.data_venda::timestamp) AS mes_venda,
    EXTRACT(DAY FROM v.data_venda::timestamp) AS dia_venda,
    EXTRACT(DOW FROM v.data_venda::timestamp) AS dia_semana,
    EXTRACT(HOUR FROM v.data_venda::timestamp) AS hora_venda,
    --classificação de faixa de preço
    CASE
        WHEN v.quantidade * v.preco_unitario::NUMERIC(10,2) < 100 THEN 'barato'
        WHEN v.quantidade * v.preco_unitario::NUMERIC(10,2) <= 500 THEN 'médio'
        ELSE 'caro'
    END AS faixa_preco
FROM {{ ref('bronze_vendas') }} as v