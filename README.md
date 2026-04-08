<p align="center">
  <img src="Post 3.png" alt="Descrição" width="500"/>
</p>

## Projeto: Plataforma de Dados E-commerce (Shopbr) – Da Extração à Inteligência Artificial<br><br>
Desenvolvi uma plataforma de dados completa para o e-commerce Shopbr, com foco em centralizar dados de sistemas isolados em um Data Warehouse moderno para subsidiar decisões estratégicas das diretorias de Clientes, Pricing e Vendas . O projeto seguiu a metodologia ELT (Extract, Load, Transform), visando escalabilidade e performance. Simulei o serviço de armazenamento S3 da AWS. Para tal, vamos usar o Supabase, que usa os mesmos protocolos do AWS: parâmetros, api, endopoint e etc. Vamos usar o Boto3, que é a biblioteca oficial para trabalhar com a AWS.<br><br>

### Stack Tecnológica & Ferramentas
. Banco de Dados: PostgreSQL hospedado na nuvem via Supabase;
. Linguagens: SQL (PostgreSQL) para consultas analíticas e Python para automação de extração;
. Engenharia de Dados: dbt (Data Build Tool) para a modelagem e transformação dos dados em camadas; e
. Inteligência Artificial: Implementação de Agentes de IA para disponibilização de insights via dispositivos móveis.

### Desenvolvimento em 4 Etapas
.Etapa 1: Análise Exploratória e SQL e Pandas: Resposta a 12 perguntas de negócio críticas (como faturamento total, ticket médio e ranking de produtos) utilizando comandos avançados como Joins, Window Functions (Row Number), CTEs e Agregações;
.Etapa 2: Extração de Dados com Python: Automação da coleta de dados simulando sistemas do mundo real, incluindo integração com APIs e manipulação de arquivos nos formatos JSON e Parquet
.Etapa 3: Engenharia e Modelagem de Dados: Utilização do dbt para organizar a arquitetura de dados, transformando dados brutos em informações modeladas e persistentes no banco de dados
.Etapa 4: Inteligência Artificial: Integração de uma camada de IA Agêntica para permitir que gestores realizem consultas complexas diretamente pelo celular

### Principais Técnicas e Diferenciais
. Visão Holística: Atuação de ponta a ponta na esteira de dados, desempenhando papéis de Engenheiro, Analytics Engineer e Analista;
. Modelagem de Dados: Criação de relacionamentos entre tabelas de Fato (Vendas) e Dimensões (Produtos, Clientes, Competidores);
. Análise de Pricing: Desenvolvimento de lógica para comparação de preços com competidores do mercado; e
. Este projeto demonstra a transição de relatórios manuais e "gargalos" em planilhas para uma infraestrutura de dados automatizada, auditável e preparada para a escala de IA.
