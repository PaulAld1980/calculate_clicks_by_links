import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


def correct_address(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return 'https://' + url
    return url


def is_shorten_link(url):
    parsed = urlparse(url)
    return parsed.netloc == "vk.cc"


def check_url_exists(url):
    response = requests.get(url, timeout=5)
    response.raise_for_status()


def request_shorten_link(token, original_url):
    api_url = "https://api.vk.com/method/utils.getShortLink"
    params = {
        "access_token": token,
        "v": "5.199",
        "url": original_url,
        "private": 0
    }
    return requests.get(api_url, params=params, timeout=10)


def extract_short_url(response):
    data = response.json()
    if "error" in data:
        error_msg = data["error"].get("error_msg", "Неизвестная ошибка")
        raise RuntimeError(f"Ошибка от VK API: {error_msg}")
    return data["response"]["short_url"]


def parse_short_url(short_url):
    parsed = urlparse(short_url)
    return parsed.path.lstrip('/')


def request_link_stats(token, key):
    url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.131",
        "key": key,
        "interval": "forever"
    }
    return requests.get(url, params=params, timeout=10)


def extract_clicks(response):
    data = response.json()
    if "error" in data:
        error_msg = data["error"].get("error_msg", "Ошибка получения статистики")
        raise RuntimeError(f"Ошибка от VK API: {error_msg}")
    stats = data.get("response", {}).get("stats", [])
    return sum(item.get("clicks", 0) for item in stats)


def main():
    vk_token = os.getenv("VK_TOKEN")
    if not vk_token:
        print("Ошибка: переменная VK_TOKEN не найдена.")
        return

    user_input = input("Вставь ссылку: ").strip()
    corrected_url = correct_address(user_input)

    try:
        if is_shorten_link(corrected_url):
            key = parse_short_url(corrected_url)
            stats_response = request_link_stats(vk_token, key)
            stats_response.raise_for_status()
            clicks = extract_clicks(stats_response)
            print("Количество переходов по ссылке:", clicks)

        else:
            check_url_exists(corrected_url)

            shorten_response = request_shorten_link(vk_token, corrected_url)
            shorten_response.raise_for_status()
            short_url = extract_short_url(shorten_response)
            print("Сокращённая ссылка:", short_url)

            key = parse_short_url(short_url)
            stats_response = request_link_stats(vk_token, key)
            stats_response.raise_for_status()
            clicks = extract_clicks(stats_response)
            print("Количество переходов по ссылке:", clicks)

    except requests.exceptions.HTTPError as http_error:
        print("HTTP ошибка:", http_error)
    except requests.exceptions.ConnectionError:
        print("Ошибка соединения: проверь URL или подключение к интернету.")
    except requests.exceptions.Timeout:
        print("Превышено время ожидания ответа от сервера.")
    except Exception as general_error:
        print("Неизвестная ошибка:", general_error)


if __name__ == "__main__":
    main()
