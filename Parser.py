import os
import time
import requests
from bs4 import BeautifulSoup, PageElement
import json
from typing import *
import re


def is_base_dns_correct(foo: Callable) -> int or str:
    """
    :param foo: check is a dns url correct
    :return:
    """

    def wrapper(*args, **kwargs):
        pattern = re.compile(f"^{BASE_DNS}")
        if "url" not in kwargs.keys():
            return foo(*args, **kwargs)
        if pattern.match(kwargs["url"]):
            return foo(*args, **kwargs)
        else:
            return "invalid url"

    return wrapper


def string_to_dict(string: str) -> dict or str:
    """
    This function will help to convert the copied cookies from the browser into a dictionary that will be used in the
     request.
    :param string: the string to be converted to a dictionary    :return: dictionary
    """
    result_dict = {}
    if not string:
        return "empty line"
    try:
        keys_with_values_list = string.split("; ")
        for case in keys_with_values_list:
            c = case.split("=")
            result_dict[c[0]] = c[1]
    except ValueError:
        raise "Invalid cookies value"
    return result_dict


# DNS site host and prefix of all site URLs
BASE_DNS = "https://www.dns-shop.ru"

# Changes periodically
COOKIES = string_to_dict(
    "phonesIdent=3cc9692a991b8df291d4c66b9b1ecd683c049ff0a765378795f3ad43eb74410ea%3A2%3A%7Bi%3A0%3Bs%3A11%3A%22phonesIdent%22%3Bi%3A1%3Bs%3A36%3A%22c73dbed1-42cd-44c7-b5db-d30ec08da927%22%3B%7D; ipp_uid=1670052047669/WM9bE0ovZ77HEIOB/RFPZFiAYYIZxOJsaeuaCkA==; guest_default_shop=d49d7ba5-268a-4c51-9615-a48124fd2918; current_path=cd696e88b11355116e4e64e21c3f9645727cbd331e57bc9031771a93efec8d27a%3A2%3A%7Bi%3A0%3Bs%3A12%3A%22current_path%22%3Bi%3A1%3Bs%3A109%3A%22%7B%22city%22%3A%22cd1f0fe4-3292-11e1-9afa-001517c526f0%22%2C%22cityName%22%3A%22%5Cu0422%5Cu0432%5Cu0435%5Cu0440%5Cu044c%22%2C%22method%22%3A%22manual%22%7D%22%3B%7D; date-user-last-order-v2=8d584d4ecd75968dcfbf3ba7c0decdc5bf797fba72900bf459b1fc50f7e288d7a%3A2%3A%7Bi%3A0%3Bs%3A23%3A%22date-user-last-order-v2%22%3Bi%3A1%3Bi%3A1677587925%3B%7D; spid=1678462357059_0fe35a50079f9052742137490c994e42_e4perrin1pcawwap; ipp_sign=2e0fa55818d31fb6185643b7994bdf67_2088042140_b6a6d964f6c4390c02c07e1d4559106c; cartUserCookieIdent_v3=733ec86910ae542a8bb561ffe789e3227ffe36119064d43e31df809ef3c75d5ba%3A2%3A%7Bi%3A0%3Bs%3A22%3A%22cartUserCookieIdent_v3%22%3Bi%3A1%3Bs%3A36%3A%22d83b9d54-de81-37b9-bf59-48457ed8af81%22%3B%7D; cookieImagesUploadId=010b289b2139d61211016a61171558e1a7c10eed0e0ea889f2ec73aa5a19024da%3A2%3A%7Bi%3A0%3Bs%3A20%3A%22cookieImagesUploadId%22%3Bi%3A1%3Bs%3A36%3A%22e3aa7846-61d9-49ac-8bdc-935526b38f01%22%3B%7D; PHPSESSID=a3b223ab16fd62cda20af74b1e929e94; lang=ru; city_path=tver; qrator_jsr=1690567735.818.MfFYKZaRRi0oL1VY-kosn7so0b0kmp7cjrqt51r1gfkadjch4-00; qrator_jsid=1690567735.818.MfFYKZaRRi0oL1VY-69rnc5pe6mskrggg4vlbuun5i00uims4")

# May not be changed
HEADERS = {"User-Agent":
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.4.674 Yowser/2.5 Safari/537.36",
           }

# registered companies dictionary {"title": True - if the company is registered
#                                           Lies - otherwise }
REGISTER_BRAND = {}

@is_base_dns_correct
def parser_section(url: str, path: str) -> int or str:
    """
    :param path: relative path to the section folder
    :param url: url
    :return: Returns status response code or error description
    """
    response = requests.get(url=url, headers=HEADERS, cookies=COOKIES)
    status_code = response.status_code
    if status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        product_list = soup.find('div', {'class': 'products-list'}).find_all('div', {
            'class': 'catalog-product ui-button-widget'})
        if product_list is None:
            return "no list"
        for product in product_list:
            status_code = parser_product(path=path, product=product)
            if status_code != 200:
                return status_code
            time.sleep(2)
    return status_code


@is_base_dns_correct
def parser_brand(url: str) -> dict or int:
    """
    Parses the following data:
        - logo
        - description if it exists
    :param url:  url
    :return: a dictionary if the status response code is 200.
    """
    brand_response = requests.get(url=url, headers=HEADERS, cookies=COOKIES)
    status_code = brand_response.status_code
    soup_brand = BeautifulSoup(brand_response.content, 'html.parser')
    brand_dict = {}
    if status_code == 200:
        img = soup_brand.find('img', {'class': 'brands-page__logo_image'})
        if img is None:
            brand_dict["img"] = None
        else:
            brand_dict["img"] = img.get("src")
        brand_dict["title"] = ""
        description = soup_brand.find('div', {'class': 'description__show-more'})
        if description is None:
            brand_dict["description"] = None
        else:
            brand_dict["description"] = description.text
        return brand_dict
    return status_code


@is_base_dns_correct
def parser_product(path: str, product: PageElement) -> int or str:
    """
    This function stores the following information about the product:
        - the product number and its full name in the product_number_main.json file.
        - Image with the name product_number.jpg.
        - Characteristics in the product_number_characteristic.json file.
        - Product description in the file product_number_description.txt
        Directory to write to section_name\\product_number
    also stores the following brand information:
        - Name
        - image
        - description
    :param path: relative path to the section folder
    :param product: page element containing product information
    :return: Returns status response code or error description
    """
    product_number = product.get("data-code")
    product_url = "https://www.dns-shop.ru" + product.find('a', {'class': 'catalog-product__image-link'}).get(
        "href") + "characteristics/"

    product_response = requests.get(url=product_url, headers=HEADERS, cookies=COOKIES)
    status_code = product_response.status_code
    soup_product = BeautifulSoup(product_response.content, 'html.parser')
    if status_code == 200:
        # checking if there is content
        if soup_product.find('div', {'class': 'product-card-top__name'}) is None:
            return "no product"

        # BRAND
        title = None
        brand_soup = soup_product.find('li', {'class': 'breadcrumb-list__item initial-breadcrumb initial-breadcrumb_manufacturer'})
        if brand_soup is not None:
            brand_soup = brand_soup.find('a', {'class': 'ui-link ui-link_black'})
            if brand_soup is not None:
                title = brand_soup.get("href").split("=")[1]
                if title not in REGISTER_BRAND.keys():
                    brand = parser_brand(url=BASE_DNS + "/brand/" + title)
                    brand["title"] = title
                    os.mkdir(f"{path}/{title}")
                    # parse image
                    if brand["img"] is not None:
                        brand_img_response = requests.get(url=brand["img"], headers=HEADERS, cookies=COOKIES)
                        status_code = product_response.status_code
                        if status_code != 200:
                            return status_code

                        # save the brand logo
                        if brand_img_response.status_code == requests.codes.OK:
                            with open(f'{path}/{title}/{title}.jpg', 'wb') as f:
                                for chunk in brand_img_response:
                                    f.write(chunk)

                    # this dictionary will store the main information about the brand
                    main_info_producer = {"producer_title": brand["title"], "producer_description": brand["description"]}

                    # save it in json format, the file will be stored in the folder with the product number
                    with open(f"{path}/{title}/{product_number}_main.json", "w", encoding='utf-8') as write_file:
                        json.dump(main_info_producer, write_file, ensure_ascii=False)
                    REGISTER_BRAND[title] = True

        #PRODUCT
        product_name = soup_product.find('div', {'class': 'product-card-top__name'}).text
        link_product_image = soup_product.find('div', {'class': 'product-images-slider'}).find('img').get('src')

        # creating a directory
        path += f"/{product_number}"
        os.mkdir(path)
        # this dictionary will store the main information about the product
        main_info_product = {"product_number": product_number, "product_name": product_name, "product_brand": title}

        # save it in json format, the file will be stored in the folder with the product number
        with open(f"{path}/{product_number}_main.json", "w", encoding='utf-8') as write_file:
            json.dump(main_info_product, write_file, ensure_ascii=False)

        # parse image
        brand_img_response = requests.get(url=link_product_image, headers=HEADERS, cookies=COOKIES)
        status_code = product_response.status_code
        if status_code != 200:
            return status_code
        # save the product image
        if brand_img_response.status_code == requests.codes.OK:
            with open(f'{path}/{product_number}.jpg', 'wb') as f:
                for chunk in brand_img_response:
                    f.write(chunk)
        product_characteristics = soup_product.find('div', {'class': 'product-characteristics-content'}).find_all('div',
                                                                                                                  {
                                                                                                                      'class': 'product-characteristics__group'})
        characteristics = {}
        """
        go through all the characteristics of the product and write them down in the dictionary.
        The key is the name of a special section, the value is a dictionary: the key is the name of the characteristic
                                                                             the value is its value
        """
        for group in product_characteristics:
            dict_items = {}
            for item in group.find_all('div', {'class': 'product-characteristics__spec'}):
                dict_items[item.find('div', {'class': 'product-characteristics__spec-title'}).text] = item.find('div', {
                    'class': 'product-characteristics__spec-value'}).text
            characteristics[group.find('div', {'class': 'product-characteristics__group-title'}).text] = dict_items

        # save it in json format
        with open(f"{path}/{product_number}_characteristics.json", "w", encoding='utf-8') as write_file:
            json.dump(characteristics, write_file, ensure_ascii=False)

        # reads the description and writes it to a file
        description = soup_product.find('div', {'class': 'product-card-description-text'}).find("p").text

        with open(f"{path}/{product_number}_description.txt", "w", encoding='utf-8') as write_file:
            write_file.write(description)
    return status_code


@is_base_dns_correct
def parser_catalog(url: str = BASE_DNS) -> int or str:
    """
    This function queries the main categories of the catalog and creates a folder for each of them.
    :param url: url
    :return: Returns status response code or error description
    """
    directory_to_save = "Каталог"
    os.mkdir(directory_to_save)
    response = requests.get(url=url, headers=HEADERS, cookies=COOKIES)
    status_code = response.status_code
    if status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        sections = soup.find_all('div', {'class': "catalog-menu__root-item"})
        if sections is None:
            return "incorrect page"
        for section in sections:
            url_section = section.find('a', {'class': "catalog-menu__link-wrapper"}).get("href")
            title = section.find('a', {'class': "catalog-menu__root-item-info catalog-menu__root-item-title"}).text
            os.mkdir(directory_to_save + "/" + title)
            status_code = subcategory_parser(url=BASE_DNS + url_section, path=directory_to_save + "/" + title)
    return status_code


@is_base_dns_correct
def subcategory_parser(url: str, path: str = "") -> int or str:
    """
    This function will recursively go through all sections and create directories according to their hierarchy.
     If you reach the list of products, it will launch parser_section
    :param path: A string that stores the path where the files will be saved
    :param url: url
    :return: Returns status response code or error description
    """
    response = requests.get(url=url, headers=HEADERS, cookies=COOKIES)
    status_code = response.status_code
    if status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        if soup.find('div', {'class': "subcategory"}) is None:
            status_code = parser_section(url=url, path=path)
            if status_code != 200:
                return status_code

        list_subcategory = soup.find_all('a', {'class': "subcategory__item ui-link ui-link_blue"})
        for subcategory in list_subcategory:
            time.sleep(2)
            title = subcategory.find('span', {'class': 'subcategory__title'}).text
            temp_path = path + f"/{title}"
            os.mkdir(temp_path)
            url_img = subcategory.find('img', {'class': "subcategory__image-content"}).get('data-src')
            catalog_img_response = requests.get(url=url_img, headers=HEADERS, cookies=COOKIES)
            status_code = catalog_img_response.status_code
            # save the catalog image

            if status_code == 200:
                with open(f'{temp_path}/{title}.jpg', 'wb') as f:
                    for chunk in catalog_img_response:
                        f.write(chunk)
            else:
                return status_code
            status_code = subcategory_parser(url=BASE_DNS + subcategory.get('href'), path=temp_path)
            if status_code != 200:
                return status_code
    return status_code


if __name__ == '__main__':
    parser_catalog()
