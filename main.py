import datetime
import os
import requests
from flask import jsonify
import pandas as pd
import numpy as np
from typing import Optional
from typing import Dict
from bs4 import BeautifulSoup
import requests
from flask import abort
import pandas as pd
import re
from dataclasses import dataclass
from flask import Flask, render_template
import lxml
from flask import request
from api import Session
from api.models import AssetValue, MyAsset, User
from sqlalchemy.dialects.mysql import insert
import datetime
from service.line_notification import send_line_notification, build_asset_summary_msg, build_add_asset_msg
from service.user import get_user
from collections import defaultdict
from app_config import app_config
import jwt
from flask import request

app = Flask(__name__)


def get_us_etf(stock_code: str) -> Optional[Dict]:
    url = f'https://finance.yahoo.com/quote/{stock_code}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    stock_name_element = soup.select_one('main .main .top h1')
    if not stock_name_element:
        return
    stock_name = stock_name_element.text.strip()

    closing_price_element = soup.select_one(
        'main .main .bottom .price .container fin-streamer span')

    closing_price = closing_price_element.text.strip()
    return {'Close': closing_price, 'Name': stock_name}


def get_us_stock(stock_code: str) -> Optional[Dict]:
    trimmed_code = stock_code.strip().upper()
    first_char = trimmed_code[0]
    url = f"https://eoddata.com/stocklist/NASDAQ/{first_char}.htm"
    res = requests.get(url)
    if not res:
        print('1Get empty content from stock:{stock_code}')
        return
    soup = BeautifulSoup(res.text, features="lxml")

    data = []
    for row in soup.select('#ctl00_cph1_divSymbols table tr:has(td)'):
        d = dict(zip(soup.select_one(
            '#ctl00_cph1_divSymbols table tr:has(th)').stripped_strings, row.stripped_strings))
        if d.get('Code') == trimmed_code:
            return d
    return get_us_etf(stock_code)


def get_currency_rate(code: Optional[str] = None) -> pd.DataFrame:
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    resp = requests.get(url)
    if not resp:
        print('3Get empty content from stock:{stock_code}')
        return
    resp.encoding = 'utf-8'

    html = BeautifulSoup(resp.text, "lxml")

    cash_buy_list = []
    cash_sell_list = []
    currency_list = []
    currency_code = []

    rate_table = html.find('table', attrs={'title': '牌告匯率'}).find(
        'tbody').find_all('tr')
    for rate in rate_table:
        # print(rate)
        prices = rate.find_all("td")
        # print(prices[1].text)
        cash_buy_list.append(prices[1].text)
        # print(prices[2].text)
        cash_sell_list.append(prices[2].text)

        currency_name = rate.find_all(class_="visible-phone print_hide")
        # print(currency_name[1].text.strip())
        currency_name = currency_name[1].text.strip()
        currency_list.append(currency_name)

        extracted_code = re.search(r"\([^)]+\)", currency_name)
        currency_code.append(extracted_code.group(0)[1:-1])

    df = pd.DataFrame()
    df["currency"] = currency_list
    df["code"] = currency_code
    df["buy"] = cash_buy_list
    df["sell"] = cash_sell_list
    if not code:
        return df
    else:
        trimmed_code = code.strip().upper()
        return df[df["code"] == trimmed_code]


def get_tw_stock(code: str) -> pd.DataFrame:
    link = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data'
    data = pd.read_csv(link)
    data.columns = ['STOCK_SYMBOL', 'NAME', 'TRADE_VOLUME', 'TRADE_VALUE',
                    'OPEN', 'HIGH', 'LOW', 'CLOSE', 'PRICE_CHANGE', 'TRANSACTION']


def get_etf_price(code: str):
    trimmed_code = code.strip().upper()
    div_url = f'https://www.moneydj.com/ETF/X/Basic/Basic0002.xdjhtm?etfid={trimmed_code}.TW'
    r = requests.get(div_url)
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.findAll("table", class_="DataTable")[0]
    row_td = [i.text for i in table.find_all('td')]
    return row_td[1]


def calculate_value(propert: dict):

    value = 0

    if propert["type"] == "cash":
        value = propert["amount"]
    else:
        # Stock
        if propert["market"] == "US":
            stock = get_us_stock(propert["code"])
            if not stock:
                return propert["type"],0
            stock_price = float(stock['Close'])
            currency_rate = float(get_currency_rate('USD').loc[0, 'buy'])
            stock_price = stock_price * currency_rate
            print("stock_price", stock_price, type(stock_price))
            print("currency_rate", currency_rate, type(currency_rate))
            value = int(stock_price * int(propert["amount"]))

        else:
            if propert["code"].startswith("00"):
                bond_etf_price = float(get_etf_price(propert["code"]))
                value = int(bond_etf_price * propert["amount"])
            else:
                stock = get_tw_stock(propert["code"])
                if not stock:
                    return propert["type"],0
                stock_price = float(stock['CLOSE'])
                value = int(stock_price * int(propert["amount"]))
        print("value", value)
    return propert["type"], value


def upsert_current_value(session, _aid: int, _value: int):

    try:
        stmt = insert(AssetValue).values(aid=_aid, value=_value)

        stmt = stmt.on_duplicate_key_update(
            {"Value": _value,
             "Aid": _aid,
             "UpdatedAt": datetime.datetime.now()})

        session.execute(stmt)
        session.commit()
    except Exception as err:
        print(err)
    finally:
        session.rollback()


def token_decode(token: str) -> dict:
    return jwt.decode(token, app_config['ASSET_CONFIG']['JWT_TOKEN_KEY'], algorithms=['HS256'])


def get_request_auth(header_token: str) -> dict:
    try:
        if os.environ.get('RUN_ENV') == 'dev':
            return {'iss': 'PaulChen', 'exp': 1725604979, 'id': '0', 'name': 'chun-fu chen'}
        else:
            print("Request token:", header_token)
            data = token_decode(header_token)
            print("Token decode", data)
            return data
    except Exception as exc:
        print(exc)
        abort(400)


@app.route("/assets/recalculate", methods=["GET"])
def regular_recalculate_task():

    session = Session()
    try:
        users = session.query(User).all()
        for user in users:
            u = user.to_dict()
            assets = session.query(MyAsset).filter(
                MyAsset.uid == u['uid']).all()
            asset_value_dict = defaultdict(float)
            for asset in assets:
                asset_dict = asset.to_dict()
                print(f"Recalculate asset: {asset_dict}")
                type, current_value = calculate_value({
                    'type': asset_dict['asset_type'],
                    'code': asset_dict['code'],
                    'amount': asset_dict['amount'],
                    'market': asset_dict['market']
                })
                print('current_value', current_value)
                upsert_current_value(session, asset.aid, current_value)
                asset_value_dict[type] += current_value
            content = build_asset_summary_msg(asset_value_dict)

            send_line_notification(user.line_id, content)
    except Exception as err:
        print(err)
    finally:
        session.rollback()
    return ''


@app.route("/current_value", methods=["GET"])
def query_value():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.

    user = get_request_auth(request.headers.get('Token'))
    propert = request.get_json()
    _, value = calculate_value(propert)
    operation = request.args.get('op', None)

    if operation in ['insert', 'update']:
        propert['value'] = value
        user = get_user(user['id'])
        msg = build_add_asset_msg(propert, operation)
        print('msg', msg)
        send_line_notification(user.line_id, msg)
    return jsonify({"current_value": value})


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
