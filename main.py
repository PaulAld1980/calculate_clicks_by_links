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
        "v": "5.199",
        "key": short_link_key,
        "interval": "forever"
    }
    response = requests.get(api_url, params=params, timeout=20)
    response.raise_for_status()
    link_stats_response = response.json()
    return not "error" in link_stats_response


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
    if "error" in shortened_link_response:
        raise requests.exceptions.HTTPError(f"Ошибка от VK API: {shortened_link_response['error'].get('error_msg', 'Неизвестная ошибка')}")
    return shortened_link_response["response"]["short_url"]


def count_clicks(token, short_url):
    short_link_key = urlparse(short_url).path.lstrip('/')
    api_url = "https://api.vk.com/method/utils.getLinkStats"
    params = {
        "access_token": token,
        "v": "5.199",
        "key": short_link_key,
        "interval": "forever"
    }
    response = requests.get(api_url, params=params, timeout=20)
    response.raise_for_status()
    click_stats_response = response.json()
    if "error" in click_stats_response:
        raise requests.exceptions.HTTPError(f"Ошибка от VK API: {click_stats_response['error'].get('error_msg', 'Ошибка получения статистики')}")
    stats = click_stats_response.get("response", {}).get("stats", [])
    return sum(item.get("clicks", 0) for item in stats)


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
            user_url = shorten_link(vk_token, user_url)
            print("Сокращённая ссылка:", user_url)
            print("Количество переходов по ссылке: 0")
    except requests.exceptions.ConnectionError:
        print("Ошибка соединения: проверь URL или подключение к интернету.")
    except requests.exceptions.Timeout:
        print("Превышено время ожидания ответа от сервера.")
    except requests.exceptions.HTTPError as http_error:
        print("HTTP ошибка:", http_error)
    except ValueError as value_error:
        print("Ошибка парсинга ответа API:", value_error)
    except Exception as general_error:
        print("Неизвестная ошибка:", general_error)


if __name__ == "__main__":
    main()
