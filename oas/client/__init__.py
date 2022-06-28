from oas import config_map
from oas.client.feishuapiclient import FeishuApiClient
from oas.client.tencentcloudaiapiclient import TencentcloudaiApiClient


def create_apiclients(config_name):
    config_class = config_map.get(config_name)
    fac = FeishuApiClient(config_class.LARK_HOST, config_class.APP_ID, config_class.APP_SECRET)
    tac = TencentcloudaiApiClient(config_class.TENCENT_CLOUD_AI_HOST,
                                  config_class.TENCENT_CLOUD_API_SECRETID,
                                  config_class.TENCENT_CLOUD_API_SECRETKEY,
                                  config_class.TENCENT_CLOUD_AI_BOTID)
    return fac, tac


feishu_api_client, tencentcloudai_api_client = create_apiclients("dev")
