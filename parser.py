import json
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup

YEAR_URLS = {
    1941: "https://yandex.ru/archive/catalog/4b29b52e-1776-4d64-9eb6-4c4439cc7890/years/2061922a-998d-4b77-99ef-8f5d6ef0dafe",
    1942: "https://yandex.ru/archive/catalog/4b29b52e-1776-4d64-9eb6-4c4439cc7890/years/a32ce5e2-8dd5-4f90-b614-95cb0f10d2ec",
    1943: "https://yandex.ru/archive/catalog/4b29b52e-1776-4d64-9eb6-4c4439cc7890/years/0a2f650c-83d5-4ca3-a562-9ab2ae9029a9",
    1944: "https://yandex.ru/archive/catalog/4b29b52e-1776-4d64-9eb6-4c4439cc7890/years/eda22010-2a45-43f9-a78e-55deedc9481b",
    1945: "https://yandex.ru/archive/catalog/4b29b52e-1776-4d64-9eb6-4c4439cc7890/years/c0657fb1-6fee-41d4-885c-e56354665421"
}

BASE_URL = "https://yandex.ru"

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


class YandexArchiveParser:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False
            }
        )

        self.scraper.headers.update({
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Referer": "https://yandex.ru/archive/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 YaBrowser/26.4.0.0 Safari/537.36"
            ),
        })

    def get_html(self, url: str) -> str:

        print(f"[GET] {url}")

        response = self.scraper.get(url, timeout=60)

        if response.status_code != 200:
            raise Exception(
                f"HTTP {response.status_code} for {url}"
            )

        return response.text

    def get_soup(self, url: str) -> BeautifulSoup:
        html = self.get_html(url)
        return BeautifulSoup(html, "lxml")

    def find_issue_by_date(self, year_url: str, target_date: str):
        soup = self.get_soup(year_url)

        target_dt = datetime.strptime(target_date, "%Y-%m-%d")

        issue_cards = soup.select("div.Issues_ImageWrapper__XkXEo")

        print(f"Найдено карточек: {len(issue_cards)}")

        if len(issue_cards) == 0:
            return None

        for card in issue_cards:
            date_el = card.select_one(
                "div.Issues_ImageDate__8xfq9"
            )

            link_el = card.select_one("a[href]")

            if not date_el or not link_el:
                continue

            raw_date = date_el.get_text(" ", strip=True)

            match = re.search(
                r"(\d+)\s+([а-я]+)\s+(\d{4})",
                raw_date.lower()
            )

            if not match:
                continue

            day = int(match.group(1))
            month_name = match.group(2)
            year = int(match.group(3))

            month = MONTHS.get(month_name)

            if not month:
                continue

            parsed_date = datetime(year, month, day)

            if parsed_date.date() == target_dt.date():
                issue_url = urljoin(
                    BASE_URL,
                    link_el["href"]
                )

                return {
                    "date": target_date,
                    "issue_url": issue_url
                }

        return None

    def extract_ocr_text(self, soup: BeautifulSoup):
        lines = soup.select(
            "p.MarkupTextsViewer_RegionsListItem_Readonly__g3lYR"
        )

        result = []
        for line in lines:
            text = line.get_text(" ", strip=True)
            if text:
                result.append(text)

        return "\n".join(result)

    def parse_page(self, page_url: str):
        soup = self.get_soup(page_url)
        text = self.extract_ocr_text(soup)
        return {
            "url": page_url,
            "text": text
        }

    def parse_issue_by_date(self, year_url: str, target_date: str):
        for i in range(1, 8):
            issue = self.find_issue_by_date(
                year_url + f"?pageNum={i}",
                target_date
            )
            if issue:
                break

        else:
            print(f"Выпуск за {target_date} не найден")
            return

        issue_url = issue["issue_url"]

        print(f"Найден выпуск:", issue_url)

        page_urls = []

        for page_num in range(1, 2):  # Будем читать только 1 страницу (и так много контента)
            page_urls.append(f"{issue_url}/{page_num}")

        result = {
            "date": target_date,
            "issue_url": issue_url,
            "pages": []
        }

        for i, page_url in enumerate(page_urls, start=1):
            print(f"Парсим страницу {i}")

            try:
                page_data = self.parse_page(page_url)
                result["pages"].append({
                    "page": i,
                    "url": page_url,
                    "text": page_data["text"]
                })

                time.sleep(1)

            except Exception as e:
                print(f"Ошибка страницы {i}: {e}")

        return result


if __name__ == "__main__":
    parser = YandexArchiveParser()

    target_date = datetime(1942, 5, 12)

    data = parser.parse_issue_by_date(
        YEAR_URLS[target_date.year],
        target_date.strftime("%Y-%m-%d")
    )

    filename = f"Izvestia/izvestia_{target_date.strftime('%Y-%m-%d')}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\nСохранено в {filename}")
