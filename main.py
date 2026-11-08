import asyncio
import datetime
import json
import os
import httpx
import pandas as pd

# 1. SERVIDORES ATUALIZADOS: Usando os espelhos mais potentes e removendo os que caem muito
OVERPASS_SERVERS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

NICHOS_OSM = {
    "Vistoria Veicular": 'nwr["name"~"Vistoria",i]'
}


async def buscar_no_openstreetmap(client: httpx.AsyncClient, nicho_nome: str, tag_osm: str, cidade: str):
    print(f"Buscando {nicho_nome} em {cidade}...")

    # 2. TIMEOUT AUMENTADO: Passou de 45 para 90 segundos para evitar erro 504
    query = f"""
    [out:json][timeout:90];
    area["name"="{cidade}"]["admin_level"="8"]->.searchArea;
    (
      {tag_osm}(area.searchArea);
    );
    out tags;
    """

    # 3. USER-AGENT AMIGÁVEL: Os servidores do OSM dão erro 502/429 para robôs "desconhecidos".
    headers = {
        "User-Agent": "ExtratorVistorias/1.0 (contato@scalis.com.br)",
        "Accept": "application/json"
    }

    for url in OVERPASS_SERVERS:
        for tentativa in range(1, 4):
            try:
                # O timeout do request deve ser um pouco maior que o da query (90s)
                response = await client.post(url, data={"data": query}, headers=headers, timeout=100.0)

                if response.status_code in [429, 500, 502, 503, 504]:
                    print(f"⚠️ Servidor {url} instável ({response.status_code}). Aguardando 5s (Tentativa {tentativa}/3)...")
                    await asyncio.sleep(5)
                    continue

                response.raise_for_status()
                dados = response.json()
                return nicho_nome, dados.get("elements", [])

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                # Agora o erro vai mostrar exatamente o motivo (ex: ConnectTimeout)
                print(f"Falha na tentativa {tentativa} com {url}: {type(e).__name__}")
                await asyncio.sleep(3)

    print(f"❌ Não foi possível obter dados para {nicho_nome} após tentar todos os servidores.")
    return nicho_nome, []


def processar_leads(nicho: str, elementos: list):
    leads_sem_site = []

    for el in elementos:
        tags = el.get("tags", {})

        # Ignora se já possui site
        if "website" in tags or "contact:website" in tags or "url" in tags:
            continue

        nome = tags.get("name", "Nome não informado")
        if nome == "Nome não informado":
            continue

        rua = tags.get("addr:street", "")
        numero = tags.get("addr:housenumber", "")
        bairro = tags.get("addr:suburb", "Bairro desconhecido")
        telefone = tags.get("phone", tags.get("contact:phone", ""))

        # Monta o endereço, independente de ter telefone ou não
        endereco = f"{rua}, {numero}".strip(" ,-")
        if not endereco:
            endereco = "Endereço incompleto no mapa"

        leads_sem_site.append({
            "Nicho": nicho,
            "Nome do Estabelecimento": nome,
            "Endereço": endereco,
            "Bairro": bairro,
            "Telefone": telefone if telefone else "Não informado"
        })

    return leads_sem_site


def salvar_em_excel(leads: list, nome_base="leads_fortaleza_sem_site"):
    if not leads:
        print("⚠️ Nenhum lead para salvar.")
        return

    df = pd.DataFrame(leads)
    nome_arquivo = f"{nome_base}.xlsx"

    try:
        df.to_excel(nome_arquivo, index=False, engine="openpyxl")
        print(f"\n✅ Planilha atualizada com sucesso: {os.path.abspath(nome_arquivo)}")
    except PermissionError:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        novo_nome = f"{nome_base}_{timestamp}.xlsx"
        df.to_excel(novo_nome, index=False, engine="openpyxl")
        print(f"\n⚠️ O arquivo '{nome_arquivo}' estava aberto no Excel.")
        print(f"✅ Os {len(leads)} leads foram salvos em uma nova planilha: {os.path.abspath(novo_nome)}")


async def orquestrar():
    cidade = "Fortaleza"
    todos_leads = []

    # 4. Ajustado o timeout de conexão do HTTPX
    timeout_config = httpx.Timeout(100.0, connect=20.0)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        for nicho, tag in NICHOS_OSM.items():
            _, elementos = await buscar_no_openstreetmap(client, nicho, tag, cidade)
            leads = processar_leads(nicho, elementos)
            todos_leads.extend(leads)
            print(f"-> Encontrados {len(leads)} leads SEM site para {nicho}.\n")

            await asyncio.sleep(3.0)

    print(f"--- VARREDURA CONCLUÍDA ---")
    print(f"Total de possíveis clientes mapeados na cidade: {len(todos_leads)}")

    salvar_em_excel(todos_leads)


if __name__ == "__main__":
    asyncio.run(orquestrar())