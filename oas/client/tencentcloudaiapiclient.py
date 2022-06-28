import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tbp.v20190627 import tbp_client, models


class TencentcloudaiApiClient(object):

    def __init__(self, tencent_cloud_ai_host,
                 tencent_cloud_api_secretid, tencent_cloud_api_secretkey, tencent_cloud_ai_botid):
        self._tencent_cloud_ai_host = tencent_cloud_ai_host
        self._tencent_cloud_api_secretid = tencent_cloud_api_secretid
        self._tencent_cloud_api_secretkey = tencent_cloud_api_secretkey
        self._tencent_cloud_ai_botid = tencent_cloud_ai_botid

    def get_ai_response(self, terminal_id, content):
        try:
            cred = credential.Credential(self._tencent_cloud_api_secretid, self._tencent_cloud_api_secretkey)
            http_profile = HttpProfile()
            http_profile.endpoint = self._tencent_cloud_ai_host

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client = tbp_client.TbpClient(cred, "", client_profile)

            req = models.TextProcessRequest()
            params = {
                "BotId": self._tencent_cloud_ai_botid,
                "BotEnv": "release",
                "TerminalId": terminal_id,
                "InputText": content
            }
            req.from_json_string(json.dumps(params))

            resp = client.TextProcess(req)
            response = json.loads(resp.to_json_string())
            return response["ResponseMessage"]["GroupList"][0]["Content"]

        except TencentCloudSDKException as err:
            print(err)
