import requests
from bs4 import BeautifulSoup
import shutil
import json
from copy import deepcopy
import pandas

output_file = 'product'


def get_soup(url):
    res = requests.get(url)
    # print(res.content)
    # print(res.status_code)
    soup = BeautifulSoup(res.content, 'html.parser')

    return soup


def get_categories():
    shop_by_aisle = {}
    item_list = []
    url = 'https://www.pnp.co.za/'
    print("Getting categories:", url)
    soup = get_soup(url)
    lis = soup.find_all('li', {'class': 'yCmsComponent'})
    for li in lis:
        a_tag = li.find('a')
        title = a_tag.text
        cat_url = a_tag['href']
        cat_url_level_count = len(str(cat_url).split('/'))
        if cat_url_level_count == 8:
            if 'https://www.pnp.co.za' not in cat_url:
                cat_url = 'https://www.pnp.co.za' + str(cat_url)
                item_dict = {'title': title, 'url': cat_url}
                if item_dict not in item_list:
                    item_list.append(item_dict)

    shop_by_aisle['category'] = item_list
    # print(shop_by_aisle)
    return shop_by_aisle


def get_sub_categories(shop_by_aisle):
    shop_by_aisle_sub_cat = {}
    categories_list = shop_by_aisle['category']
    cat_sub_cat_list = []
    for category_dict in categories_list:
        cat_url = category_dict['url']
        print("Getting subcategories:", cat_url)
        soup = get_soup(cat_url)
        sub_cat_tiles = soup.find_all('div', {'class': 'col-sm-4'})
        sub_cat_list = []
        for sub_cat in sub_cat_tiles:
            a_tag = sub_cat.find('a')
            if a_tag:
                sub_cat_title = str(a_tag.text).strip()
                sub_cat_url = 'https://www.pnp.co.za' + a_tag['href']
                sub_cat_dict = {'title': sub_cat_title, 'url': sub_cat_url}
                sub_cat_list.append(sub_cat_dict)
                # print(sub_cat_title)
                # print(sub_cat_url)
        category_dict['sub_category'] = sub_cat_list
        cat_sub_cat_list.append(category_dict)
    shop_by_aisle_sub_cat['category'] = cat_sub_cat_list
    # print(shop_by_aisle_sub_cat)
    return shop_by_aisle_sub_cat


prod_urls = []


def scrape_url(url):
    print("Getting urls from a list page:", url)
    # url = 'https://www.pnp.co.za/pnpstorefront/pnp/en/pnpmerchandising/2021/March/Week-3/Smart-Price-is-Our-Best-Price/c/smart-price-is-our-best-price221752085'
    # url = 'https://www.pnp.co.za/pnpstorefront/pnp/en/All-Products/Fresh-Food/Cheese/c/cheese703655157'
    soup = get_soup(url)
    products = soup.find_all('div', {'class': 'product-card-grid'})
    for product in products:
        prod_url = 'https://www.pnp.co.za' + str(product.find('a')['href'])
        prod_urls.append(prod_url)
        # print(prod_url)

    # print("len of prod_urls:", len(prod_urls))
    next_page_block = soup.find('li', {'class': 'pagination-next'})
    # print("next_page_block:", next_page_block)
    if next_page_block:
        next_page_a = next_page_block.find('a')
        if next_page_a:
            next_page = 'https://www.pnp.co.za' + next_page_a['href']
            scrape_url(next_page)
    # else:
    #     return prod_urls


def scrape_details(prod_urls_from_function):
    sub_cat_prod_list = []
    for prod_url in prod_urls_from_function:
        print("Getting product:", prod_url)
        soup = get_soup(prod_url)
        try:
            title = str(soup.find('div', {'class': 'fed-pdp-product-details-title'}).text).strip()
        except:
            title = ''
        # print("title:", title)

        try:
            sell_price_block = soup.find('div', {'class': 'normalPrice'})

            sell_price = str(sell_price_block.text).strip()
            if sell_price:
                sell_price = sell_price[:-2] + '.' + sell_price[-2:]
                sell_price= sell_price.replace("R", "")
        except:
            sell_price = ''
        try:
            old_price_block = soup.find('div', {'class': 'oldprice'})
            old_price = str(old_price_block.text).strip()
            if old_price:
                old_price = old_price[:-2] + '.' + old_price[-2:]
                old_price = old_price.replace("R", "")
        except:
            old_price = ''

        # print("sell price:", sell_price)
        # print("old price:", old_price)

        # images_block = soup.find('div', {'class': 'owl-stage-outer'})
        try:
            zoom_images = soup.find_all('img', {'class': 'owl-lazy'})
        except:
            zoom_images = []
        images_url = []
        images_path = []
        for image in zoom_images:
            try:
                img_url = image['data-zoom-image']
                # print("image url:", img_url)
                images_url.append(img_url)
                response = requests.get(img_url, stream=True)
                file_name = str(img_url).split('/')[-1]
                image_path = 'images/' + file_name + '.png'
                images_path.append(image_path)
                with open(image_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response
            except Exception as e:
                pass
        # print(images_url)
        # print(images_path)

        product_dict = {
            'url': prod_url,
            'title': title,
            'sell_price': sell_price,
            'old_price': old_price,
            'images_url': images_url,
            'images_path': images_path
        }

        # print(product_dict)
        sub_cat_prod_list.append(product_dict)

    # print(sub_cat_prod_list)
    return sub_cat_prod_list

    # break


def scrape_all():
    shop_by_aisle_new = {}
    global prod_urls
    shop_by_aisle = get_categories()
    shop_by_aisle_sub_cat = get_sub_categories(shop_by_aisle)

    categories_list = shop_by_aisle_sub_cat['category']
    categories_new_list = []
    for category_dict in categories_list:
        category_new_dict = category_dict
        sub_categories_list = category_dict['sub_category']
        sub_categories_new_list = []
        for sub_category_dict in sub_categories_list:
            sub_category_new_dict = sub_category_dict
            prod_urls = []
            sub_cat_url = sub_category_dict['url']
            scrape_url(sub_cat_url)
            # print(prod_urls)
            # print(len(prod_urls))
            sub_cat_prod_list = scrape_details(prod_urls)
            sub_category_new_dict['product'] = sub_cat_prod_list
            sub_categories_new_list.append(sub_category_new_dict)

            break  # uncomment for single sub category

        category_new_dict['sub_category'] = sub_categories_new_list
        categories_new_list.append(category_new_dict)

        break  # uncomment for single category

    shop_by_aisle_new['category'] = categories_new_list

    with open(output_file + ".json", "w") as outfile:
        json.dump(shop_by_aisle_new, outfile)

    print(shop_by_aisle_new)


def cross_join(left, right):
    new_rows = []
    for left_row in left:
        for right_row in right:
            temp_row = deepcopy(left_row)
            for key, value in right_row.items():
                temp_row[key] = value
            new_rows.append(deepcopy(temp_row))
    return new_rows


def flatten_list(data):
    for elem in data:
        if isinstance(elem, list):
            yield from flatten_list(elem)
        else:
            yield elem


def json_to_dataframe(data_in):
    def flatten_json(data, prev_heading=''):
        if isinstance(data, dict):
            rows = [{}]
            for key, value in data.items():
                rows = cross_join(rows, flatten_json(value, prev_heading + '_' + key))
        elif isinstance(data, list):
            rows = []
            for i in range(len(data)):
                [rows.append(elem) for elem in flatten_list(flatten_json(data[i], prev_heading))]
        else:
            rows = [{prev_heading[1:]: data}]
        return rows

    return pandas.DataFrame(flatten_json(data_in))


def json_to_csv():
    with open(output_file + '.json') as json_file:
        json_data = json.load(json_file)

    df = json_to_dataframe(json_data)
    df.to_csv(output_file + '.csv', mode='w')


if __name__ == '__main__':
    scrape_all()
    json_to_csv()








# scrape_url('https://www.pnp.co.za/pnpstorefront/pnp/en/All-Products/Fresh-Food/Cheese/c/cheese703655157')
# scrape_details()
# # get_categories()
# # get_sub_categories()

