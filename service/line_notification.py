
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
import configparser


config = configparser.ConfigParser()
config.read('config.ini')


# Configure Bearer authorization: Bearer
configuration = linebot.v3.messaging.Configuration(
    access_token = config['ASSET_CONFIG']['LineAccessToken']
)

def send_line_notification(user_id:str, message:str):
    if not user_id:
        return
    # Enter a context with an instance of the API client
    with linebot.v3.messaging.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = linebot.v3.messaging.MessagingApi(api_client)
        push_message_request = linebot.v3.messaging.PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]) # PushMessageRequest | 
        x_line_retry_key = str(uuid.uuid4())

        try:
            api_response = api_instance.push_message(push_message_request,x_line_retry_key=x_line_retry_key)
            print("The response of MessagingApi->push_message:\n")
            pprint(api_response)
        except Exception as e:
            print("Exception when calling MessagingApi->push_message: %s\n" % e)