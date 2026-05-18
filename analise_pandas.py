"""Autor: Thierry Vanden Broucke | Data: 2026-05-18 | Versao: 1.0.3."""

import json
from datetime import datetime

import pandas as pd

AUTOR = "Thierry Vanden Broucke"
DATA_VERSAO = "2026-05-18"
VERSAO = "1.0.3"

ARQUIVO_CSV = "transacoes.csv"
ARQUIVO_RELATORIO_PRINCIPAL = "relatorio.json"
LIMITE_SUSPEITO = 10000.00


def carregar_transacoes_pandas(caminho_csv):
    df = pd.read_csv(caminho_csv)
    df = df.copy()

    for coluna in ["cliente_id", "tipo", "descricao", "categoria", "data", "id", "valor"]:
        df[coluna] = df[coluna].fillna("").astype(str).str.strip()

    df["id_numerico"] = pd.to_numeric(df["id"], errors="coerce")
    df["valor_numerico"] = pd.to_numeric(df["valor"], errors="coerce")
    df["data_convertida"] = pd.to_datetime(df["data"], format="%Y-%m-%d", errors="coerce")
    df["tipo_normalizado"] = df["tipo"].str.lower()

    mascara_valida = (
        df["id"].str.fullmatch(r"\d+")
        & (df["cliente_id"] != "")
        & df["data_convertida"].notna()
        & df["tipo_normalizado"].isin(["credito", "debito"])
        & df["valor_numerico"].notna()
        & (df["valor_numerico"] > 0)
    )

    df_valido = df.loc[mascara_valida].copy()
    df_invalido = df.loc[~mascara_valida].copy()

    df_valido["id_numerico"] = df_valido["id_numerico"].astype(int)
    df_valido["mes"] = df_valido["data_convertida"].dt.strftime("%Y-%m")
    df_valido["suspeita"] = df_valido["valor_numerico"] > LIMITE_SUSPEITO

    duplicados = int(df_valido.duplicated(subset=["id_numerico"]).sum())
    if duplicados:
        df_valido = df_valido.drop_duplicates(subset=["id_numerico"], keep="first")

    resumo_limpeza = {
        "total_lidas": int(len(df)),
        "total_validas": int(len(df_valido)),
        "total_invalidas": int(len(df_invalido) + duplicados),
        "total_duplicadas": duplicados,
    }

    return df_valido, resumo_limpeza


def gerar_relatorio_pandas(df_valido, resumo_limpeza):
    resumo_mensal = (
        df_valido.groupby("mes")
        .apply(
            lambda grupo: pd.Series(
                {
                    "quantidade": int(len(grupo)),
                    "total_credito": float(grupo.loc[grupo["tipo_normalizado"] == "credito", "valor_numerico"].sum()),
                    "total_debito": float(grupo.loc[grupo["tipo_normalizado"] == "debito", "valor_numerico"].sum()),
                    "maior_valor": float(grupo["valor_numerico"].max()),
                    "menor_valor": float(grupo["valor_numerico"].min()),
                }
            ),
            include_groups=False,
        )
        .sort_index()
    )

    resumo_mensal["saldo"] = resumo_mensal["total_credito"] - resumo_mensal["total_debito"]
    resumo_mensal["media"] = (
        resumo_mensal["total_credito"] + resumo_mensal["total_debito"]
    ) / resumo_mensal["quantidade"]

    if not df_valido.empty:
        data_inicial = df_valido["data_convertida"].min()
        data_final = df_valido["data_convertida"].max()
        periodo_analisado = {
            "data_inicial": data_inicial.strftime("%Y-%m-%d"),
            "data_final": data_final.strftime("%Y-%m-%d"),
            "dias_entre_datas": int((data_final - data_inicial).days),
        }
    else:
        periodo_analisado = {
            "data_inicial": None,
            "data_final": None,
            "dias_entre_datas": 0,
        }

    transacoes_suspeitas = (
        df_valido.loc[df_valido["suspeita"], ["id_numerico", "cliente_id", "data_convertida", "valor_numerico"]]
        .rename(
            columns={
                "id_numerico": "id",
                "data_convertida": "data",
                "valor_numerico": "valor",
            }
        )
        .assign(data=lambda d: d["data"].dt.strftime("%Y-%m-%d"))
        .to_dict(orient="records")
    )

    return {
        "gerado_em": datetime.now().strftime("%Y-%m-%d"),
        "total_transacoes_validas": resumo_limpeza["total_validas"],
        "total_transacoes_invalidas": resumo_limpeza["total_invalidas"],
        "total_transacoes_lidas": resumo_limpeza["total_lidas"],
        "total_transacoes_duplicadas": resumo_limpeza["total_duplicadas"],
        "periodo_analisado": periodo_analisado,
        "resumo_mensal": resumo_mensal.to_dict(orient="index"),
        "transacoes_suspeitas": transacoes_suspeitas,
    }


def comparar_com_relatorio_principal(relatorio_pandas, caminho_relatorio_principal):
    with open(caminho_relatorio_principal, "r", encoding="utf-8") as arquivo:
        relatorio_principal = json.load(arquivo)

    comparacoes = {
        "total_transacoes_validas": relatorio_pandas["total_transacoes_validas"] == relatorio_principal["total_transacoes_validas"],
        "total_transacoes_invalidas": relatorio_pandas["total_transacoes_invalidas"] == relatorio_principal["total_transacoes_invalidas"],
        "total_transacoes_lidas": relatorio_pandas["total_transacoes_lidas"] == relatorio_principal["total_transacoes_lidas"],
        "total_transacoes_duplicadas": relatorio_pandas["total_transacoes_duplicadas"] == relatorio_principal["total_transacoes_duplicadas"],
        "periodo_analisado": relatorio_pandas["periodo_analisado"] == relatorio_principal["periodo_analisado"],
        "quantidade_suspeitas": len(relatorio_pandas["transacoes_suspeitas"]) == len(relatorio_principal["transacoes_suspeitas"]),
        "meses": list(relatorio_pandas["resumo_mensal"].keys()) == list(relatorio_principal["resumo_mensal"].keys()),
    }

    for mes, dados_principais in relatorio_principal["resumo_mensal"].items():
        dados_pandas = relatorio_pandas["resumo_mensal"].get(mes, {})
        for chave, valor_principal in dados_principais.items():
            valor_pandas = dados_pandas.get(chave)
            if isinstance(valor_principal, float):
                igual = abs(valor_principal - float(valor_pandas)) < 1e-9
            else:
                igual = valor_principal == valor_pandas
            comparacoes[f"{mes}.{chave}"] = igual

    return comparacoes


def exibir_resultado(relatorio_pandas, comparacoes):
    print("===== ANÁLISE COM PANDAS =====")
    print(f"Linhas lidas: {relatorio_pandas['total_transacoes_lidas']}")
    print(f"Linhas válidas: {relatorio_pandas['total_transacoes_validas']}")
    print(f"Linhas inválidas: {relatorio_pandas['total_transacoes_invalidas']}")
    print(f"Transações suspeitas: {len(relatorio_pandas['transacoes_suspeitas'])}")
    print(f"Período: {relatorio_pandas['periodo_analisado']['data_inicial']} -> {relatorio_pandas['periodo_analisado']['data_final']}")
    print()
    print("===== COMPARAÇÃO COM A SOLUÇÃO PRINCIPAL =====")
    for chave, status in comparacoes.items():
        print(f"{chave}: {'OK' if status else 'DIVERGENTE'}")


def main():
    df_valido, resumo_limpeza = carregar_transacoes_pandas(ARQUIVO_CSV)
    relatorio_pandas = gerar_relatorio_pandas(df_valido, resumo_limpeza)
    comparacoes = comparar_com_relatorio_principal(relatorio_pandas, ARQUIVO_RELATORIO_PRINCIPAL)
    exibir_resultado(relatorio_pandas, comparacoes)


if __name__ == "__main__":
    main()
