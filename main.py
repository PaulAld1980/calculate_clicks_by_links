import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv


def is_short_link(user_url, token):
    url_parts = urlparse(user_url)
    short_link_key = url_parts.path.lstrip('/')
    api_url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.131",
        "key": short_link_key,
        "interval": "forever"
    }
    response = requests.get(api_url, params=params, timeout=20)
    response_data = response.json()
    return "error" not in response_data


def shorten_link(token, user_url):
    api_url = "https://api.vk.com/method/utils.getShortLink"
    params = {
        "access_token": token,
        "v": "5.199",
        "url": user_url,
        "private": 0
    }
    response = requests.get(api_url, params=params, timeout=20)
    response.raise_for_status()
    short_url_result = response.json()
    if "error" in short_url_result:
        error_msg = short_url_result["error"].get("error_msg", "Неизвестная ошибка")
        raise RuntimeError(f"Ошибка от VK API: {error_msg}")
    return short_url_result["response"]["short_url"]


def count_clicks(token, short_url):
    url_parts = urlparse(short_url)
    short_link_key = url_parts.path.lstrip('/')
    api_url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.131",
        "key": short_link_key,
        "interval": "forever"
    }
    response = requests.get(api_url, params=params, timeout=20)
    response.raise_for_status()
    clicks_quantity = response.json()
    if "error" in clicks_quantity:
        error_msg = clicks_quantity["error"].get("error_msg", "Ошибка получения статистики")
        raise RuntimeError(f"Ошибка от VK API: {error_msg}")
    stats_list = clicks_quantity.get("response", {}).get("stats", [])
    return sum(item.get("clicks", 0) for item in stats_list)


def main():
    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")
    if not vk_token:
        print("Ошибка: переменная VK_TOKEN не найдена.")
        return

    user_url = input("Вставь ссылку: ").strip()

    try:
        if is_short_link(user_url, vk_token):
            clicks = count_clicks(vk_token, user_url)
            print("Количество переходов по ссылке:", clicks)
        else:
            short_url = shorten_link(vk_token, user_url)
            print("Сокращённая ссылка:", short_url)
            clicks = count_clicks(vk_token, short_url)
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
