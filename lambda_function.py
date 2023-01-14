from datetime import datetime
import boto3
import requests
import json
import os

# 企业微信机器人变量
tokenUrl = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
corpid = os.getenv('corpid')
corpsecret = os.getenv('corpsecret')
agentid = os.getenv('agentid')


# 获取企微token
def get_token():
    values = {'corpid': corpid, 'corpsecret': corpsecret}
    req = requests.post(tokenUrl, params=values)
    data = json.loads(req.text)
    return data["access_token"]


sendMsg = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token="

# 发送消息到企微机器人（通过token+机器人agentid）
def send_msg(msg):
    url = sendMsg + get_token()
    print(url)
    values = """{"touser" : "@all" ,
      "msgtype":"text",
      "agentid":""" + agentid + """,
      "text":{
        "content": "%s"
      },
      "safe":"0"
      }""" % msg
    requests.post(url, values)


# 列出当前账号下超过30天的accesskey
def list_ot_accesskey():
    # Create IAM client
    iam = boto3.client('iam')

    response = iam.list_users()
    msg_aksk = ''

    # 遍历Users
    for Users in response['Users']:
        User_name = Users['UserName']
        paginator = iam.get_paginator('list_access_keys')

        for response_lsak in paginator.paginate(UserName=User_name):
            i = 0
            count_keys = len(response_lsak['AccessKeyMetadata'])

            # 遍历accesskey
            for i in range(count_keys):
                AK_Key_Id = response_lsak['AccessKeyMetadata'][i]['AccessKeyId']
                AK_Key_createDate = response_lsak['AccessKeyMetadata'][i]['CreateDate']

                # 获取当前时间
                date_now = datetime.now().date()
                AK_Key_date = AK_Key_createDate.date()

                AK_used_days = date_now - AK_Key_date
                days = int(str(AK_used_days).split(" ")[0])
                if days >= 30:
                    tmp_aksk = "\n\nAccessKey: " + AK_Key_Id + "\nIAM user: " + User_name + "\nUsage: " + str(
                        days) + " days"
                    msg_aksk = msg_aksk + tmp_aksk

    return msg_aksk


def lambda_handler(event, context):
    # 获取当前账户AccountId
    sts = boto3.client('sts')
    response_identity = sts.get_caller_identity()
    accountId = response_identity['Account']

    # 获取超过30天的accesskey
    msg_aksk = list_ot_accesskey()
    msg = "Notification Details:\nAccessKeys under your account[" + accountId + "] have been already used more than " \
                                                                                "30 days, pls check it and change " \
                                                                                "another to use.\n" + msg_aksk

    # 将消息发送到企业微信
    send_msg(msg)
    print(format(msg) + '\n')