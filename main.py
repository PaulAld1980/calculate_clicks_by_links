import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv


def is_short_link(user_url, token):
    parsed_url = urlparse(user_url)
    domain_name = parsed_url.netloc
    short_link_key = parsed_url.path.lstrip('/')
    if domain_name != "vk.cc" or not short_link_key:
        return False
    api_url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.131",
        "key": short_link_key,
        "interval": "forever"
    }
    try:
        response = requests.get(api_url, params=params, timeout=20)
        response.raise_for_status()
        link_stats_response = response.json()
        if link_stats_response.get("error"):
            return False
        return True
    except (requests.exceptions.RequestException, ValueError):
        return False


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
    shortened_link_response = response.json()
    error = shortened_link_response.get("error")
    if error:
        raise RuntimeError(f"Ошибка от VK API: {error.get('error_msg', 'Неизвестная ошибка')}")
    return shortened_link_response["response"]["short_url"]


def count_clicks(token, short_url):
    short_link_key = urlparse(short_url).path.lstrip('/')
    api_url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.131",
        "key": short_link_key,
        "interval": "forever"
    }
    response = requests.get(api_url, params=params, timeout=20)
    response.raise_for_status()
    click_stats_response = response.json()
    error = click_stats_response.get("error")
    if error:
        raise RuntimeError(f"Ошибка от VK API: {error.get('error_msg', 'Ошибка получения статистики')}")
    stats = click_stats_response.get("response", {}).get("stats", [])
    return sum(item.get("clicks", 0) for item in stats)


def main():
    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")
    if not vk_token:
        print("Ошибка: переменная VK_TOKEN не найдена.")
        return
    user_url = input("Вставь ссылку: ").strip()
    if not urlparse(user_url).scheme:
        user_url = "https://" + user_url
    try:
        if is_short_link(user_url, vk_token):
            clicks = count_clicks(vk_token, user_url)
        else:
            user_url = shorten_link(vk_token, user_url)
            print("Сокращённая ссылка:", user_url)
            clicks = count_clicks(vk_token, user_url)
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
