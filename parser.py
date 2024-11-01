import asyncio
from dataclasses import dataclass
from typing import Optional

from bs4 import ResultSet


@dataclass
class Author:
    """Class for storing author data"""
    name: str
    url: str


@dataclass
class Tag:
    """Class for storing Tag data"""
    tag_name: str
    tag_url: str


@dataclass
class Quote:
    """Class for storing Quote data"""
    text: str
    author: Author
    tags: list[Tag]


async def get_text(quote):
    """Coroutine for getting text from quote"""
    return quote.find('span', class_='text').text.strip()


async def get_author_name(quote):
    """Coroutine for getting author name from quote"""
    return quote.find('small', class_='author').text.strip()


async def get_author_url(quote, url: str):
    """Coroutine for getting author url from quote using url + relative path"""
    return url + quote.find('span', class_='').find('a')['href']


async def get_author(quote: str, url: str):
    """Coroutine for getting author object from collected data"""
    return Author(*await asyncio.gather(get_author_name(quote), get_author_url(quote, url)))


async def get_tag_name(tag) -> str:
    """Coroutine for getting tag name from quote"""
    return tag.text.strip()


async def get_tags_url(tag, url: str) -> str:
    """Coroutine for getting relative url from quote using url + relative path"""
    return url + tag.get("href")


async def get_tag_list(quote, url):
    """Coroutine for getting tags list"""
    tag_list = []
    for tag in quote.find_all('a', class_='tag'):
        tag_list.append(Tag(*await asyncio.gather(get_tag_name(tag), get_tags_url(tag, url))))
    return tag_list


async def gather_quotes(quotes: ResultSet, url: str) -> Optional[list[Quote]]:
    """Gather quotes from parsed html document"""
    results = []
    for quote in quotes:
        results.append(
            Quote(
                *await asyncio.gather(
                    get_text(quote),
                    get_author(quote, url),
                    get_tag_list(quote, url)
                )
            )
        )

    return results
