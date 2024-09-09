
import time
import os
import linebot.v3.messaging
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.messaging.models.push_message_request import PushMessageRequest
from linebot.v3.messaging.models.push_message_response import PushMessageResponse
from linebot.v3.messaging.rest import ApiException
from pprint import pprint
import uuid
from app_config import app_config


# Configure Bearer authorization: Bearer
configuration = linebot.v3.messaging.Configuration(
    access_token=app_config['ASSET_CONFIG']['LineAccessToken']
)


def build_add_asset_msg(assets: dict, op) -> str:
    title = "💰 新資產已新增" if op == 'insert' else "💰 資產資料更新"
    summarized_string = f"""
    {title}
    - 股票類型: {'美股' if assets['type']=='US' else '台股'}
    - 代碼: {assets['code']}
    - 數量: {assets['amount']}
    - 價值: {assets['value']}
    """
    return summarized_string


def build_asset_summary_msg(assets: dict) -> str:
    summarized_string = ''
    total_asset = 0
    for asset_type, asset_value in assets.items():
        summarized_string = f'{asset_type}:{asset_value}\n'
        total_asset += asset_value
        print('asset_value_dict', assets)
    summarized_string += f'Total Assets:{total_asset}'
    return summarized_string


def send_line_notification(user_id: str, message: str):
    if not user_id:
        print("The user line id is empty.")
        return
    # Enter a context with an instance of the API client
    with linebot.v3.messaging.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = linebot.v3.messaging.MessagingApi(api_client)
        push_message_request = linebot.v3.messaging.PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)])  # PushMessageRequest |
        x_line_retry_key = str(uuid.uuid4())

        try:
            print("Send request to line id:{user_id}")
            api_response = api_instance.push_message(
                push_message_request, x_line_retry_key=x_line_retry_key)
            print("The response of MessagingApi->push_message:\n")
            pprint(api_response)
        except Exception as e:
            print("Exception when calling MessagingApi->push_message: %s\n" % e)
