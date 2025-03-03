import os
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


def clearIfNecessary(item):
    return re.sub(r'[\\/*?:"<>|]', '_', item)


def scrape_list(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    items = []
    headers = []

    if table:
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

        indices = [0, 1, 5, 6]

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if cells and len(cells) >= 7:
                language = clearIfNecessary(cells[4].get_text(strip=True))
                info_parts = []
                for i in indices:
                    cell_text = cells[i].get_text(strip=True)
                    if headers and i < len(headers) + 1:
                        if i == 5:
                            label = headers[4]
                        elif i == 6:
                            label = headers[5]
                        else:
                            label = headers[i]
                        info_parts.append(f"{label}: {cell_text}")
                    else:
                        info_parts.append(cell_text)
                extra_info = " | ".join(info_parts)
                items.append({"name": language, "extra_info": extra_info})
    return items


def search_additional_info(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=1)
        if results:
            result = results[0]
            description = result.get('body', '') or result.get('snippet', '')
            link = result.get('href', result.get('url', ''))
            info = {
                "description": description,
                "link": link,
                "image": result.get('image', '')
            }
            return info
    return {"description": "Brak opisu", "link": "", "image": ""}


def generate_markdown(items, topic, output_dir='docs'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    subpages_dir = os.path.join(output_dir, "items")
    if not os.path.exists(subpages_dir):
        os.makedirs(subpages_dir)

    index_md = f"# {topic}\n\n" \
               f"The TIOBE Programming Community index is an indicator of the popularity of programming languages. The index is updated once a month. The ratings are based on the number of skilled engineers world-wide, courses and third party vendors. Popular web sites Google, Amazon, Wikipedia, Bing and more than 20 others are used to calculate the ratings. It is important to note that the TIOBE index is not about the best programming language or the language in which most lines of code have been written.'\n\n" \
               f"## List of languages\n\n"

    for item in items:
        name = item["name"]
        extra_info = item["extra_info"]

        duck_info = search_additional_info(name)
        duck_description = duck_info.get("description", "Brak opisu")
        duck_link = duck_info.get("link", "")
        duck_image = duck_info.get("image", "")

        safe_name = clearIfNecessary(name)
        subpage_content = f"# {name}\n\n" \
                          f"---\n\n" \
                          f"**Additional informations (DuckDuckGo):**\n\n" \
                          f"**Description:** {duck_description}\n\n" \
                          f"**Link:** [{duck_link}]({duck_link})\n\n"
        if duck_image:
            subpage_content += f"![{name}]({duck_image})\n\n"

        subpage_path = os.path.join(subpages_dir, f"{safe_name}.md")
        with open(subpage_path, "w", encoding="utf-8") as f:
            f.write(subpage_content)

        index_md += f"### {name}\n\n" \
                    f"**Informations:** {extra_info}\n\n" \
                    f"[Duck Duck Go search](items/{safe_name}.md)\n\n" \
                    f"---\n\n"

    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_md)


def main():
    topic = "Programming languages"
    url = "https://www.tiobe.com/tiobe-index/"

    items = scrape_list(url)

    if items:
        generate_markdown(items, topic)
        print(f"Strona została wygenerowana w katalogu '{os.path.abspath('docs')}'.")
    else:
        print(
            "Nie znaleziono elementów do zescrapowania. Upewnij się, że selektory odpowiadają strukturze HTML strony.")


if __name__ == "__main__":
    main()
