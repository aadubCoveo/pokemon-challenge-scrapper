import os

import requests
from bs4 import BeautifulSoup
from coveopush import CoveoConstants
from coveopush import CoveoPermissions
from coveopush import CoveoPush
from coveopush import Document
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def find_gen(index):
    if 1 <= index <= 151:
        return '1'
    if 152 <= index <= 251:
        return '2'
    if 252 <= index <= 386:
        return '3'
    if 387 <= index <= 493:
        return '4'
    if 494 <= index <= 649:
        return '5'
    if 650 <= index <= 721:
        return '6'
    if 722 <= index <= 809:
        return '7'
    if 810 <= index <= 898:
        return '8'


def scrap():
    pokemon_list_page = requests.get('https://pokemondb.net/pokedex/national')
    soup_pokemon_list_page = BeautifulSoup(pokemon_list_page.content, 'html.parser')
    results = soup_pokemon_list_page.find(id='main')
    info_cards = results.find_all('div', class_='infocard')

    coveo_source_id = os.environ.get("COVEO_SOURCE_ID")
    coveo_api_key = os.environ.get("COVEO_API_KEY")
    coveo_org_id = os.environ.get("COVEO_ORG_ID")

    push = CoveoPush.Push(coveo_source_id, coveo_org_id, coveo_api_key)
    push.Start(True, True)
    push.SetSizeMaxRequest(150 * 1024 * 1024)

    user_email = os.environ.get("USER_EMAIL")
    my_permissions = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "",
                                                         user_email)

    for info_card in info_cards:
        pokemon_name = info_card.find('a', class_='ent-name').text
        pokemon_page_url = 'https://pokemondb.net' + info_card.find('a', class_='ent-name')['href']

        document = Document(pokemon_page_url)

        pokemon_picture_url = info_card.find('span', class_='img-fixed img-sprite')

        if pokemon_picture_url is None:
            pokemon_picture_url = info_card.find('span', class_='img-fixed img-sprite img-sprite-v18')['data-src']
        else:
            pokemon_picture_url = info_card.find('span', class_='img-fixed img-sprite')['data-src']

        pokemon_number = info_card.find('small').text[1:]
        pokemon_gen = find_gen(int(pokemon_number))
        pokemon_types = []
        pokemon_types_tags = info_card.find_all('small')[1].find_all('a')

        print('scrapping pokemon: ' + pokemon_name + ' | index : ' + pokemon_number)

        for pokemon_type_tag in pokemon_types_tags:
            pokemon_types.append(pokemon_type_tag.text)

        pokemon_page = requests.get(pokemon_page_url)
        soup_pokemon_page = BeautifulSoup(pokemon_page.content, 'html.parser')
        results = soup_pokemon_page.find(id='main')
        tables = results.find_all('table', class_='vitals-table')

        pokemon_species = tables[0].find_all('tr')[2].find('td').text
        pokemon_height = tables[0].find_all('tr')[3].find('td').text
        pokemon_weight = tables[0].find_all('tr')[4].find('td').text

        base_stats = {}
        base_stats_tags = tables[3].find_all('tr')

        for base_stat_tag in base_stats_tags:
            base_stats[base_stat_tag.find('th').text] = base_stat_tag.find('td').text

        defense = {}
        defenses_tables = results.find_all('table', class_='type-table type-table-pokedex')

        for defense_table in defenses_tables:
            for x in range(0, len(defense_table.find_all('tr')[0].find_all('th'))):
                defense[defense_table.find_all('tr')[0].find_all('th')[x].find('a').text] = \
                    defense_table.find_all('tr')[1].find_all('td')[x].text
                document.AddMetadata(defense_table.find_all('tr')[0].find_all('th')[x].find('a').text,
                                     defense_table.find_all('tr')[1].find_all('td')[x].text)

        document.Title = pokemon_name
        document.SetData(pokemon_page.text)
        document.FileExtension = ".html"
        document.AddMetadata('name', pokemon_name)
        document.AddMetadata('url', pokemon_page_url)
        document.AddMetadata('number', pokemon_number)
        document.AddMetadata('generation', pokemon_gen)
        document.AddMetadata('types', pokemon_types)
        document.AddMetadata('specie', pokemon_species)
        document.AddMetadata('weight', pokemon_weight)
        document.AddMetadata('weight_int', pokemon_weight[0:pokemon_weight.index('kg') - 1])
        document.AddMetadata('height', pokemon_height)
        document.AddMetadata('height_int', pokemon_height[0:pokemon_height.index('m') - 1])
        document.AddMetadata('hp', base_stats.get('HP'))
        document.AddMetadata('hp_int', base_stats.get('HP'))
        document.AddMetadata('attack', base_stats.get('Attack'))
        document.AddMetadata('attack_int', base_stats.get('Attack'))
        document.AddMetadata('defense', base_stats.get('Defense'))
        document.AddMetadata('defense_int', base_stats.get('Defense'))
        document.AddMetadata('sp_atk', base_stats.get('Sp.Atk'))
        document.AddMetadata('sp_def', base_stats.get('Sp.Def'))
        document.AddMetadata('speed', base_stats.get('Speed'))
        document.AddMetadata('speed_int', base_stats.get('Speed'))
        document.AddMetadata('picture_url', pokemon_picture_url)
        document.SetAllowedAndDeniedPermissions([my_permissions], [], True)

        print('Send: ' + pokemon_name + ' | index : ' + pokemon_number + ' to the PUSH API')
        push.Add(document)
        print('Sent: ' + pokemon_name + ' | index : ' + pokemon_number + ' to the PUSH API')

    push.End(True, True)


if __name__ == '__main__':
    scrap()
