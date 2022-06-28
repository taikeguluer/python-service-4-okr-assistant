import logging
import requests


class FeishuApiClient(object):

    TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
    MESSAGE_URI = "/open-apis/im/v1/messages"
    CHATS_URI = "/open-apis/im/v1/chats"
    CHATS_MEMBERS_URI = "/open-apis/im/v1/chats/:chat_id/members"
    CREATE_TASK_URI = "/open-apis/task/v1/tasks"
    ADD_FOLLOWS_ON_TASK_URI = "/open-apis/task/v1/tasks/:task_id/followers"
    ADD_COLLABORATORS_ON_TASK_URI = "/open-apis/task/v1/tasks/:task_id/collaborators"
    COPY_FILE_URI = "/open-apis/drive/explorer/v2/file/copy/files/:fileToken"
    FILE_PERMISSION_URI = "/open-apis/drive/v1/permissions/:token/members"
    CODE_2_SESSION_URI = "/open-apis/mina/v2/tokenLoginValidate"
    USER_INFO_URI = "/open-apis/contact/v3/users/:user_id"
    ROOT_FOLDER_URI = "/open-apis/drive/explorer/v2/root_folder/meta"
    FOLDER_URI = "/open-apis/drive/explorer/v2/folder/:folderToken"
    ROBOT_INFO_URI = "/open-apis/bot/v3/info"
    INVITE_TO_CHAT_URI = "/open-apis/im/v1/chats/:chat_id/members"
    ME_JOIN_URI = "/open-apis/im/v1/chats/:chat_id/members/me_join"
    ENTERPRISE_URI = "/open-apis/tenant/v2/tenant/query"
    DEP_URI = "/open-apis/contact/v3/departments/:department_id"

    def __init__(self, lark_host, app_id, app_secret):
        self._lark_host = lark_host
        self._app_id = app_id
        self._app_secret = app_secret
        self._tenant_access_token = ""

    @property
    def tenant_access_token(self):
        return self._tenant_access_token

    # recoding

    def copy_file_from_template(self, template_token, file_type, folder_token, new_name, auth_needed=False, user_access_token=None):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(self._lark_host, self.COPY_FILE_URI.replace(":fileToken", template_token))
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        if user_access_token is not None:
            headers["Authorization"] = "Bearer " + user_access_token
        req_body = {
            "type": file_type,
            "dstFolderToken": folder_token,
            "dstName": new_name,
            "commentNeeded": "true"
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)
        result = {
            "url": resp.json()["data"]["url"],
            "token": resp.json()["data"]["token"]
        }
        return result

    def set_perm_on_file(self, file_token, file_type, perm, open_ids, member_type="openid", auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}?type={}".format(self._lark_host, self.FILE_PERMISSION_URI.replace(":token", file_token), file_type)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        for open_id in open_ids:
            req_body = {
                "member_type": member_type,
                "member_id": open_id,
                "perm": perm
            }
            resp = requests.post(url=url, headers=headers, json=req_body)
            FeishuApiClient._check_error_response(resp)

    def create_task(self, task_content, due_time, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}?user_id_type=open_id".format(
            self._lark_host, self.CREATE_TASK_URI
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        req_body = {
            "summary": task_content,
            "due": {
                "time": due_time,
                "timezone": "Asia/Shanghai"
            },
            "origin": {
                "platform_i18n_name": "{\"zh_cn\": \"团队助理\", \"en_us\": \"Team Assistant\"}"
            },
            "can_edit": "true"
        }
        if len(task_content) >= 256:
            req_body = {
                "summary": task_content[:255],
                "description": task_content,
                "due": {
                    "time": due_time,
                    "timezone": "Asia/Shanghai"
                },
                "origin": {
                    "platform_i18n_name": "{\"zh_cn\": \"团队助理\", \"en_us\": \"Team Assistant\"}"
                },
                "can_edit": "true"
            }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)
        return resp.json()["data"]["task"]["id"]

    def set_task_stakeholders(self, task_id, open_ids, is_follower=False, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}?user_id_type=open_id".format(
            self._lark_host, self.ADD_COLLABORATORS_ON_TASK_URI.replace(":task_id", task_id)
        )
        if is_follower:
            url = "{}{}?user_id_type=open_id".format(
                self._lark_host, self.ADD_FOLLOWS_ON_TASK_URI.replace(":task_id", task_id)
            )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        for open_id in open_ids:
            req_body = {
                "id": open_id
            }
            resp = requests.post(url=url, headers=headers, json=req_body)
            FeishuApiClient._check_error_response(resp)

    def get_open_ids_with_chat_id(self, chat_id, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}?member_id_type=open_id&page_size=100".format(
            self._lark_host, self.CHATS_MEMBERS_URI.replace(":chat_id", chat_id)
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        result = {}
        for item in resp.json()["data"]["items"]:
            result[item["name"]] = item["member_id"]
        return result

    def get_chat_groups(self, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.CHATS_URI
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        result = {}
        for item in resp.json()["data"]["items"]:
            result[item["name"]] = item["chat_id"]
        return result

    def send(self, receive_id_type, receive_id, content, msg_type="text", auth_needed=False):
        # send message to user, implemented based on Feishu open apiclient capability. doc link:
        # https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}?receive_id_type={}".format(
            self._lark_host, self.MESSAGE_URI, receive_id_type
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }

        req_body = {
            "receive_id": receive_id,
            "content": content,
            "msg_type": msg_type
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)

    def get_session_from_code(self, code, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.CODE_2_SESSION_URI
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }

        req_body = {
            "code": code
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)

        return resp.json()

    def get_user_info(self, open_id, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.USER_INFO_URI.replace(":user_id", open_id)
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        result = resp.json()
        result["data"]["user"]["dep_info"] = self.get_dep_info(result["data"]["user"]["department_ids"][0])
        result["data"]["user"]["enterprise_info"] = self.get_enterprise_info()
        return result["data"]["user"]

    def get_dep_info(self, open_dep_id, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.DEP_URI.replace(":department_id", open_dep_id)
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)

        return resp.json()["data"]["department"]

    def get_enterprise_info(self, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.ENTERPRISE_URI
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)

        return resp.json()["data"]["tenant"]


    def get_root_folder(self, auth_needed=False, user_access_token=None):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.ROOT_FOLDER_URI
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        if user_access_token is not None:
            headers["Authorization"] = "Bearer " + user_access_token
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        return resp.json()

    def create_folder(self, parent_token, title, auth_needed=False, user_access_token=None):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.FOLDER_URI.replace(":folderToken", parent_token)
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        if user_access_token is not None:
            headers["Authorization"] = "Bearer " + user_access_token

        req_body = {
            "title": title
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)
        return resp.json()

    def get_robot_info(self, auth_needed=False):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.ROBOT_INFO_URI
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
        }
        resp = requests.get(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        return resp.json()

    def invite_on_to_chat(self, chat_id, open_ids, auth_needed=False, user_access_token=None):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.INVITE_TO_CHAT_URI.replace(":chat_id", chat_id)
        )
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer " + self.tenant_access_token
        }
        if user_access_token is not None:
            headers["Authorization"] = "Bearer " + user_access_token

        req_body = {
            "id_list": open_ids
        }
        resp = requests.post(url=url, headers=headers, json=req_body)
        FeishuApiClient._check_error_response(resp)
        return resp.json()

    def me_join_chat(self, chat_id, auth_needed=False, user_access_token=None):
        if auth_needed:
            self._authorize_tenant_access_token()
        url = "{}{}".format(
            self._lark_host, self.ME_JOIN_URI.replace(":chat_id", chat_id)
        )
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token
        }
        if user_access_token is not None:
            headers["Authorization"] = "Bearer " + user_access_token

        resp = requests.patch(url=url, headers=headers)
        FeishuApiClient._check_error_response(resp)
        return resp.json()


    def _authorize_tenant_access_token(self):
        # get tenant_access_token and set, implemented based on Feishu open apiclient capability. doc link:
        # https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = "{}{}".format(self._lark_host, self.TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self._app_id, "app_secret": self._app_secret}
        response = requests.post(url, req_body)
        FeishuApiClient._check_error_response(response)
        self._tenant_access_token = response.json().get("tenant_access_token")


    @staticmethod
    def _check_error_response(resp):
        # check if the response contains error information
        response_dict = resp.json()
        if resp.status_code != 200:
            logging.error(response_dict)
            resp.raise_for_status()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise LarkException(code=code, msg=response_dict.get("msg"))


class LarkException(Exception):
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__
