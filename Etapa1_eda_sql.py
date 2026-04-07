"""Conceito: Conectar com DataLake usando boto3 e ler arquivos Parquet
Pergunta: Como ler dados de um DataLake usando a API S3?
"""

# Instalar boto3: pip install boto3
import boto3

# Configurações do DataLake
S3_ENDPOINT_URL = "https://XXXX.storage.supabase.co/storage/v1/s3"
AWS_REGION = "us-west-2"
AWS_ACCESS_KEY_ID = "XXXX"
AWS_SECRET_ACCESS_KEY = "XXXXX"
BUCKET_NAME = "XXXX"

# Criar cliente S3
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Listar arquivos no bucket
response = s3.list_objects(Bucket=BUCKET_NAME)
arquivos = [obj["Key"] for obj in response["Contents"]]

# Instalar pandas: pip install pandas pyarrow
import pandas as pd
# Trabalha com dados "em memória" transforma um bytes
import io

# Baixar arquivo Parquet
FILE_KEY = "vendas.parquet"
response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
parquet_bytes = response["Body"].read()

# Converter Parquet para DataFrame
df_vendas = pd.read_parquet(io.BytesIO(parquet_bytes))


# ============================================
# EXPLORANDO DADOS COM SQL - APENAS DEMONSTRANDO
# O QUE FOI FEITO NO SUPABASE
# ============================================

# --PROJETO DE IMPLEMENTAÇÃO DE PIPELINE DE DADOS EM ECOMMERCE
# --ANÁLISE EXPLORATÓRIA DE DADOS

# -- Conhecendo as tabelas e as variáveis

# SELECT column_name, data_type
# FROM information_schema.columns
# WHERE table_name = 'clientes';

# SELECT column_name, data_type
# FROM information_schema.columns
# WHERE table_name = 'preco_competidores';

# SELECT column_name, data_type
# FROM information_schema.columns
# WHERE table_name = 'produtos';

# SELECT column_name, data_type
# FROM information_schema.columns
# WHERE table_name = 'vendas';

# --Quais são os produtos que temos no catálogo?

# SELECT id_produto, nome_produto
# FROM produtos;

# --Quais são os produtos mais caros da base?

# SELECT id_produto, nome_produto, preco_atual
# FROM produtos
# ORDER BY preco_atual DESC
# LIMIT 5;

# --Quais produtos custam mais de R$ 500?

# SELECT id_produto, nome_produto, preco_atual
# FROM produtos
# WHERE preco_atual > 500
# ORDER BY preco_atual DESC;

# --Quanto a empresa faturou no total (receita total)?

# SELECT ROUND(SUM(CAST(quantidade * preco_unitario AS DECIMAL)), 2)
# FROM vendas;

# --Quanto fatura cada categoria de produto?

# SELECT produtos.categoria, ROUND(SUM(CAST(vendas.quantidade * vendas.preco_unitario AS DECIMAL)) ,2) AS faturamento
# FROM vendas
# INNER JOIN produtos ON vendas.id_produto = produtos.id_produto
# GROUP BY produtos.categoria;

# --Quais categorias geram mais dinheiro para o cliente?

# SELECT produtos.categoria, ROUND(SUM(CAST(vendas.quantidade * vendas.preco_unitario AS DECIMAL)) ,2) AS faturamento
# FROM vendas
# INNER JOIN produtos ON vendas.id_produto = produtos.id_produto
# GROUP BY produtos.categoria
# ORDER BY faturamento DESC;

# --Quais produtos compuseram cada uma das vendas realizadas?

# SELECT produtos.nome_produto, ROUND(SUM(CAST(vendas.quantidade * vendas.preco_unitario AS decimal)) ,2) AS faturamento_por_produto
# FROM vendas
# INNER JOIN produtos ON vendas.id_produto = produtos.id_produto
# GROUP BY produtos.nome_produto
# ORDER BY faturamento_por_produto DESC;

# --Quais foram as maiores vendas registradas (em valor)?

# SELECT produtos.nome_produto, ROUND(SUM(CAST(vendas.quantidade * vendas.preco_unitario AS decimal)) ,2) AS faturamento_por_produto
# FROM vendas
# INNER JOIN produtos ON vendas.id_produto = produtos.id_produto
# GROUP BY produtos.nome_produto
# ORDER BY faturamento_por_produto DESC
# LIMIT 5;

# --Qual o número total de vendas realizadas pelo e-commerce?

# SELECT COUNT(id_venda)
# FROM vendas;

# --Qual o ticket médio das transações?

# SELECT ROUND(AVG(CAST(quantidade * preco_unitario AS DECIMAL)) ,2)
# FROM vendas;

# --Como as vendas se distribuem por canal de venda (e-commerce vs. loja física)?

# SELECT canal_venda, ROUND(SUM(CAST(quantidade * preco_unitario AS DECIMAL)) ,2) AS faturamento_por_canal
# FROM vendas
# GROUP BY canal_venda
# ORDER BY faturamento_por_canal DESC;

# --Qual a performance de vendas por mês (análise temporal de receita)?

# SELECT 
#     CONCAT(EXTRACT(YEAR FROM data_venda), '-', EXTRACT(MONTH FROM data_venda)) AS ano_mes,
#     ROUND(SUM(CAST(quantidade * preco_unitario AS DECIMAL)),2) AS faturamento
# FROM vendas
# GROUP BY CONCAT(EXTRACT(YEAR FROM data_venda), '-', EXTRACT(MONTH FROM data_venda))
# ORDER BY ano_mes;

