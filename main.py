import json
from dataclasses import asdict, dataclass
from typing import Generator

import aiohttp
from bs4 import BeautifulSoup, ResultSet

import asyncio

URL = 'https://quotes.toscrape.com'

URL_PER_TIME = 10
MAX_PAGES = 50


@dataclass
class Author:
    name: str
    url: str


@dataclass
class Tag:
    tag_name: str
    tag_url: str


@dataclass
class Quote:
    text: str
    author: Author
    tags: list[Tag]


async def get_html(url: str) -> str:
    """Coroutine to get html document"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                return await response.text()
            except aiohttp.ClientError:
                print("For some reason server not reachable. Come back later")


async def gather_quotes(quotes: ResultSet) -> list[Quote] | None:
    """Gather quotes from parsed html document"""
    results = []
    for quote in quotes:
        results.append(
            Quote(
                text=quote.find('span', class_='text').text.strip(),
                author=Author(
                    name=quote.find('small', class_='author').text.strip(),
                    url=URL + quote.find('span', class_='').find('a')['href']
                ),
                tags=[
                    Tag(
                        tag_name=tag.text.strip(),
                        tag_url=URL + tag.get("href")
                    ) for tag in quote.find_all('a', class_='tag')
                ]
            )
        )

    return results


async def get_data(url) -> list[Quote] | None:
    """Parse html document and return list if quotes objects if page have quotes"""
    async with asyncio.Semaphore(URL_PER_TIME):
        html = await get_html(url)
        data = BeautifulSoup(html, 'html.parser').find_all(class_='quote')
        if not data:
            return None
        return await gather_quotes(data)


def save_to_json(data: list[Quote]):
    """Save data to json file"""
    try:
        with open('collected_data.json', 'w') as f:
            json.dump([asdict(quote) for quote in data], f, indent=4)
    except Exception as e:
        print(f"Error writing JSON file: {e}")


def get_next_urls(max_pages=MAX_PAGES) -> Generator[str, None, None]:
    """Generates next page"""
    start = 1
    while start <= max_pages:
        yield [URL + f"/page/{i}" for i in range(start, start + URL_PER_TIME)]
        start += URL_PER_TIME


async def main():
    """Main script function collect data and save to json file"""
    data = []
    for urls in get_next_urls():
        batch_data = await asyncio.gather(*(get_data(url) for url in urls))
        if None in batch_data:
            data.extend([item for item in batch_data if item is not None])
            break
        for item in batch_data:
            data.extend(item)

    save_to_json(data)
if __name__ == '__main__':
    asyncio.run(main())

