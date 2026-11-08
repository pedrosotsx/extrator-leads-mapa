Extrator de Leads - OpenStreetMap (OSM)

Este é um script em Python projetado para buscar estabelecimentos comerciais diretamente no banco de dados público do OpenStreetMap. O objetivo é identificar empresas que ainda não possuem um site registrado no mapa, criando uma lista de potenciais clientes (leads).

⚙️ Como o Sistema Funciona

Consulta à API (Overpass): O script usa o httpx de forma assíncrona para se conectar aos servidores do OpenStreetMap (via Overpass API). Ele busca por tipos específicos de comércios dentro de uma cidade predefinida (por padrão, "Fortaleza").

Sistema de Contenção de Falhas: Caso um servidor do OSM esteja fora do ar ou sobrecarregado (erros 502, 504), o script tenta usar automaticamente outros servidores espelhos, garantindo a captura dos dados.

Filtragem Estratégica: Ao receber os dados brutos, a função processar_leads:

Verifica se o local tem a tag website ou url. Se tiver, ele descarta (pois não é um lead qualificado para quem vende sites).

Captura os dados disponíveis (Nome, Endereço, Bairro e Telefone). O estabelecimento é capturado mesmo se não tiver telefone cadastrado.

Exportação: Após varrer todos os nichos, o resultado final é exportado e salvo automaticamente em uma planilha Excel (.xlsx).

🎯 Como Mudar ou Adicionar Nichos

Os nichos que o robô vai buscar ficam no topo do código, dentro do dicionário NICHOS_OSM. O OpenStreetMap funciona baseado em tags (chaves e valores).

Onde alterar:

No arquivo Python, procure por esta parte:

NICHOS_OSM = {
    "Vistoria Veicular": 'nwr["name"~"Vistoria",i]'
}


Como adicionar novos (Exemplos):

Você pode adicionar quantos nichos quiser separando-os por vírgula. Veja exemplos usando categorias oficiais do OSM (tags amenity, shop, etc.) e buscas por nome:

NICHOS_OSM = {
    # Busca pela categoria de restaurantes no mapa:
    "Restaurantes": 'nwr["amenity"="restaurant"]',
    
    # Busca pela categoria de academias:
    "Academias": 'nwr["leisure"="fitness_centre"]',
    
    # Busca por oficinas mecânicas:
    "Oficinas": 'nwr["shop"="car_repair"]',
    
    # Busca por qualquer lugar que tenha "Clínica" no nome (ignorando maiúsculas/minúsculas):
    "Clínicas": 'nwr["name"~"Clínica",i]',
    
    # Mantendo o original de vistorias:
    "Vistoria Veicular": 'nwr["name"~"Vistoria",i]'
}


Dica: Você pode consultar a OSM Map Features para encontrar as tags oficiais de quase qualquer tipo de comércio!