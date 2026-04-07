SELECT
    pc.id_produto,
    pc.nome_concorrente,
    pc.preco_concorrente,
    pc.data_coleta,
    -- coluna calculada: data sem hora
    DATE(pc.data_coleta::timestamp) AS data_coleta_date
FROM {{ ref('bronze_preco_competidores') }} pc
