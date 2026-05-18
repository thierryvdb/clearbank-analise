# clearbank-analise
Projeto de análise financeira em Python para leitura, validação e processamento de transações bancárias em CSV. A solução gera métricas mensais, identifica movimentações suspeitas, exporta os resultados em JSON e inclui uma visualização com `matplotlib`.

Autor: Thierry Vanden Broucke  
Data: 2026-05-18  
Versão: 1.0.3

## Objetivo do projeto
Este projeto foi desenvolvido para:
- ler um arquivo `transacoes.csv`
- validar registros inválidos sem interromper a execução
- agrupar as transações por mês
- calcular métricas financeiras mensais
- sinalizar transações acima do limite suspeito
- exportar o relatório final em `relatorio.json`

## Arquivos principais
- `desafio-final.ipynb`: notebook principal com a solução obrigatória
- `transacoes.csv`: base de dados utilizada na análise
- `relatorio.json`: saída gerada pela análise principal
- `grafico.png`: visualização mensal de crédito, débito e saldo
- `analise_pandas.py`: versão opcional da análise usando `pandas`

## Como executar
Abra o arquivo `desafio-final.ipynb` no Google Colab ou Jupyter Notebook e execute as células na ordem em que aparecem.

Se for rodar localmente com os opcionais instalados, use:

```bash
pip install -r requirements.txt
```

Para executar a versão opcional com `pandas`, rode:

```bash
python analise_pandas.py
```

## Saídas geradas
Ao final da execução, o notebook:
- exibe um resumo da limpeza dos dados
- mostra o relatório mensal no terminal
- identifica transações suspeitas
- gera o arquivo `relatorio.json`
- gera o arquivo `grafico.png` com visualização mensal de crédito, débito e saldo

## Tecnologias utilizadas
- Python 3
- `csv`
- `json`
- `datetime`
- `matplotlib`
- `pandas` na implementação opcional
