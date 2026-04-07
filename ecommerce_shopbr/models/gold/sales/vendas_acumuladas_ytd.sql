-- Vendas acumuladas mês a mês (YTD - Year To Date)
-- Mostra a receita mensal e o acumulado progressivo dentro de cada ano
WITH vendas_mensais AS (
    SELECT
        v.ano_venda,
        v.mes_venda,
        SUM(v.receita_total) AS receita_mensal,
        SUM(v.quantidade) AS quantidade_mensal,
        COUNT(DISTINCT v.id_venda) AS total_vendas_mensal,
        COUNT(DISTINCT v.id_cliente) AS total_clientes_mensal
    FROM {{ ref('silver_vendas') }} v
    GROUP BY v.ano_venda, v.mes_venda
)

SELECT
    ano_venda,
    mes_venda,
    receita_mensal,
    quantidade_mensal,
    total_vendas_mensal,
    total_clientes_mensal,
    -- Acumulado YTD usando window function
    SUM(receita_mensal) OVER (
        PARTITION BY ano_venda
        ORDER BY mes_venda
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS receita_acumulada_ytd,
    SUM(quantidade_mensal) OVER (
        PARTITION BY ano_venda
        ORDER BY mes_venda
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS quantidade_acumulada_ytd,
    SUM(total_vendas_mensal) OVER (
        PARTITION BY ano_venda
        ORDER BY mes_venda
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS vendas_acumuladas_ytd
FROM vendas_mensais
ORDER BY ano_venda, mes_venda
