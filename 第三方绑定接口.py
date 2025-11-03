import requests
import sys
import urllib.parse
import time
import hashlib
import json
from urllib.parse import urlencode, quote
import uuid
from urllib.parse import unquote 

# ==================== 必须手动获取 ====================
# 1. 从真实手机抓包获取（不能用浏览器）
#    用 Charles + iPhone 代理，登录支付宝 App → 触发授权 → 复制以下内容

COOKIES_STR = r"""zone=RZ54A; spanner=mQNnFkafEI7touOsffShTz78gDNCVbuX; ALIPAYJSESSIONID=RZ54KNoFVZT6bDG0ihsrDX0acvB4OW41mobilegwRZ54; devKeySet={"apdidToken":"Wkx5lKWxUsAdda8JZH5\/aKw985qCOkE8IXw7ZLkzEZb7cj\/yjJ9DmgEB"}; session.cookieNameId=ALIPAYJSESSIONID; ctoken=bLvzra5bByr4GpgtCq1WAxtt""".strip()

def test_apptoken(apptoken):
    url = "https://api-mifit-cn3.zepp.com/v2/users/me/events"

    #8D2CE5A9-6876-4D61-B6D9-589A566C96B7  1759212397122   phn
    
    params = {
        "eventType": "phn",
        "limit": "200",    
    }
    
    headers = {
        "User-Agent": "Zepp/9.13.0 (iPhone; iOS 26.1; Scale/3.00)",
        "apptoken": apptoken
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        return r.status_code == 200
    except:
        return False

def test_band(apptoken,userid):


    headers = {
        'Host': 'weixin.amazfit.com',
        'Connection': 'keep-alive',
        'hm-privacy-ceip': 'false',
        'Accept': '*/*',
        'channel': 'appstore',
        'apptoken': apptoken,
        'appname': 'com.huami.midong',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'timezone': 'Asia/Shanghai',
        'X-Request-Id': '9726A384-E00F-4182-9041-BA13193EBAD5',
        'cv': '1403_8.9.1',
        'lang': 'zh_CN',
        'User-Agent': 'Zepp/8.9.1 (iPhone; iOS 17.3; Scale/3.00)',
        'appplatform': 'ios_phone',
        'country': 'CN',
        'v': '2.0',
        'hm-privacy-diagnostics': 'false',
    }

    params = {
        'brandName': 'amazfit',
        'userid': userid,
        'wxname': 'md',
    }

    response = requests.get('https://weixin.amazfit.com/v1/bind/qrcode.json', params=params, headers=headers).json()
    
    data = response # 获取 JSON 数据
    return data['data']['ticket']


def test_band_v2(apptoken,userid):
    headers = {
    "Host": "api-mifit-cn3.zepp.com",
    "User-Agent": "Zepp/9.13.0 (iPhone; iOS 26.1; Scale/3.00)",
    "Connection": "keep-alive",
    "appname": "com.huami.midong",
    "apptoken":  apptoken,
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br"
    }
    url = "https://api-mifit-cn3.zepp.com/v1/thirdParties/auth.json"
    params = {

        "userid": userid
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()  # 获取 JSON 数据
    print(data['data']['authInfo'])
    return build_alipay_url(data['data']['authInfo'])  # 获取指定字段

def build_alipay_url(info_str):
    # 解析info字符串为字典
    params_dict = urllib.parse.parse_qs(info_str)
    
    # 从info中提取需要的参数
    app_id = params_dict.get('app_id', [''])[0]
    sign = params_dict.get('sign', [''])[0]
    biz_type = params_dict.get('biz_type', [''])[0]
    auth_type = params_dict.get('auth_type', [''])[0]
    api_name = params_dict.get('apiname', [''])[0]
    scope = params_dict.get('scope', [''])[0]
    target_id = params_dict.get('target_id', [''])[0]
    product_id = params_dict.get('product_id', [''])[0]
    pid = params_dict.get('pid', [''])[0]
    
    # 构建基础URL（保留原有结构）
    url = 'https://authweb.alipay.com/auth?v=h5'
    
    # 添加从info中提取的参数
    if app_id: url += f'&app_id={app_id}'
    if sign: url += f'&sign={urllib.parse.quote(sign)}'
    if biz_type: url += f'&biz_type={biz_type}'
    if auth_type: url += f'&auth_type={auth_type}'
    if api_name: url += f'&apiname={api_name}'
    if scope: url += f'&scope={scope}'
    if target_id: url += f'&target_id={target_id}'
    if product_id: url += f'&product_id={product_id}'
    if pid: url += f'&pid={pid}'
    
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    url += f'&mqpNotifyName=CashierAuth_{timestamp}'
    url += f'&clientTraceId={timestamp}'
    
    # 添加固定参数
    url += '&bundle_id=com.huami.watch'
    url += '&app_name=mc'
    url += '&msp_type=embeded-ios'
    url += '&method='
    
    #return urllib.parse.quote(url)
    return url



# 2. 提取 apdidToken
def extract_apdid_token(cookie_str):
    for part in cookie_str.split(';'):
        if 'devKeySet' in part:
            try:
                json_str = part.split('=', 1)[1]
                data = json.loads(json_str)
                return data.get('apdidToken')
            except:
                pass
    return None

# 3. 生成 sign
def generate_sign(ts, trace_id, apdid_token):
    raw = f"{ts}{trace_id}{apdid_token}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest().lower()


def moni_alipay(url):
    # 1. 从传入的URL中提取clientTraceId
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    cookie_dict = {item.split('=')[0]: item.split('=')[1] for item in COOKIES_STR.split('; ') if '=' in item}
    # 获取clientTraceId，如果不存在则使用当前时间戳
    if 'clientTraceId' in query_params:
        trace_id = query_params['clientTraceId'][0]
    else:
        trace_id = str(int(time.time() * 1000))


    # 5. 动态参数
    ts = str(int(time.time() * 1000) + 300)
    
    apdid_token = extract_apdid_token(COOKIES_STR)

    if not apdid_token:
        raise ValueError("无法提取 apdidToken")

    sign = generate_sign(ts, trace_id, apdid_token)
    

    # 6. 构造 headers（必须与真实 App 一致）
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/23B5073a Ariver/1.1.0 AliApp(AP/10.6.80.6000) Nebula WK RVKType(1) AlipayDefined(nt:WIFI,ws:393|788|3.0) AlipayClient/10.6.80.6000 Language/zh-Hans Region/CN NebulaX/1.0.0 DTN/2.0',
        'ts': ts,
        'sign': sign,
        'Cookie': COOKIES_STR,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Connection': 'Keep-Alive',
        'Host': 'authweb.alipay.com',
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=15,
            verify=True  # 必须验证 SSL
        )
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        #print(f"Response: {response.text}")

        # 1. 检查响应文本中的<title>是否为"登录"
        if "<title>登录</title>" in response.text:
            print("检测到登录页面，cookie已过期，请重新获取")
            return None, None, None, None  # 返回4个None
        
        # 更新Cookie：将响应头中的Set-Cookie更新到Cookie字典
        if 'Set-Cookie' in response.headers:
            for cookie in response.headers['Set-Cookie'].split(','):
                if ';' in cookie:
                    cookie_item = cookie.split(';')[0].strip()
                    if '=' in cookie_item:
                        key, value = cookie_item.split('=', 1)
                        cookie_dict[key] = value
        # 2. 提取<script>window.context = 的JSON值
        start_str = "<script>window.context ="
        end_str = ";</script>"
        
        start_idx = response.text.find(start_str)
        if start_idx == -1:
            print("未找到window.context脚本")
            return None, None, None, None  # 返回4个None
            
        end_idx = response.text.find(end_str, start_idx)
        if end_idx == -1:
            print("window.context脚本格式不正确")
            return None, None, None, None  # 返回4个None
            
        # 提取JSON字符串
        json_str = response.text[start_idx + len(start_str):end_idx].strip()
        
        try:
            # 解析JSON
            context_data = json.loads(json_str)
            # 3. 获取contextToken的值
            context_token = context_data.get("contextToken")
            
            if context_token:
                print(f"成功获取contextToken: {context_token}")
                updated_cookie = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                return context_token, updated_cookie, trace_id, url
            else:
                print("JSON中未找到contextToken字段")
                return None, None, None, None  # 返回4个None
                
        except json.JSONDecodeError:
            print("解析JSON失败")
            return None, None, None, None  # 返回4个None

    except Exception as e:
        print(f"请求异常: {e}")
        return None, None, None, None  # 返回4个None

def simulate_auth_post(context_token, updated_cookie, trace_id, url):
    """
    模拟支付宝授权POST请求
    :param context_token: 从moni_alipay获取的contextToken
    :param updated_cookie: 从moni_alipay获取的更新后的Cookie
    :param trace_id: 从moni_alipay获取的trace_id (clientTraceId)
    :return: 请求响应对象
    """
    # 构造请求URL
    url = "https://authweb.alipay.com/auth"
    # 从更新后的cookie中提取ctoken
    cookie_dict = {item.split('=')[0]: item.split('=')[1] for item in updated_cookie.split('; ') if '=' in item}
    ctoken = cookie_dict.get('ctoken', '')

    # 构造请求头
    headers = {
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Alipay-Client-Session': 'check',
        'Sec-Fetch-Site': 'same-origin',
        'Origin': 'https://authweb.alipay.com',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/23B5073a Ariver/1.1.0 AliApp(AP/10.6.80.6000) Nebula WK RVKType(1) AlipayDefined(nt:WIFI,ws:393|788|3.0) AlipayClient/10.6.80.6000 Language/zh-Hans Region/CN NebulaX/1.0.0 DTN/2.0',
        'Sec-Fetch-Mode': 'cors',
        'Cookie': updated_cookie,
        'Referer': url,
        'Host': 'authweb.alipay.com',
        'x-allow-afts-limit': 'true',
        'Accept': '*/*',
    }
    
    # 构造请求体
    env_data = {
        "bioMetaInfo": "4.12.0:1628342034496,32774,2088802520255575",
        "appVersion": "10.6.80.6000",
        "appName": "com.alipay.iphoneclient",
        "deviceType": "ios",
        "osVersion": "iOS 26.1",
        "viSdkVersion": "3.6.80.100",
        "deviceModel": "iPhone15,4"
    }
    
    data = {
        "contextToken": context_token,
        "oauthScene": "AUTHACCOUNT",
        "ctoken": ctoken,  # 从cookie中提取
        "token": "undefined",
        "mqpNotifyName": f"CashierAuth_{trace_id}",
        "envData": json.dumps(env_data),
        "channel": "SECURITYPAY"
    }
    
    # 发送POST请求
    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=15,
            verify=True
        )
        print(f"POST Status: {response.status_code}")
        print(f"Response: {response.text}")
            # 解析响应
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                # 提取并解析authDestUrl中的result参数
                if 'authDestUrl' in response_data:
                    from urllib.parse import urlparse, parse_qs
                    import base64
                    
                    # 解析URL中的查询参数
                    parsed_url = urlparse(response_data['authDestUrl'])
                    query_params = parse_qs(parsed_url.query)
                    
                    # 获取并解码result参数
                    if 'result' in query_params:
                        result_b64 = query_params['result'][0]
                        try:
                            # Base64解码
                            decoded_result = base64.b64decode(result_b64).decode('utf-8')
                            print(f"解码后的result参数: {decoded_result}")
                            decoded_result = unquote(decoded_result)
                            print(f"URL解码后的result参数: {decoded_result}")
                            # 可选：进一步解析解码后的内容
                            # 示例格式: 'success=true&result_code=200&app_id=...'
                            result_params = parse_qs(decoded_result)
                            print(f"解析后的result参数: {result_params}")
                                                    # 将列表值转换为单个值（如果只有一个元素）
                            for key in result_params:
                                if len(result_params[key]) == 1:
                                    result_params[key] = result_params[key][0]
                        

                            return result_params
                        except Exception as e:
                            print(f"Base64解码失败: {e}")
                            return None
                
                
            except json.JSONDecodeError:
                print("响应不是有效的JSON格式")
                return None

    except Exception as e:
        print(f"POST请求发生异常: {e}")
        return None

def bind_alipay_account(auth_result, userid, apptoken):
    """
    使用从支付宝授权结果中提取的auth_code绑定支付宝账号
    
    参数:
    auth_result - simulate_auth_post返回的解析结果
    userid - 用户ID
    apptoken - 应用token
    
    返回:
    绑定操作的结果
    """
    # 1. 从授权结果中提取auth_code
    if 'auth_code' not in auth_result:
        return {"error": "授权结果中缺少auth_code参数"}
    
    auth_code = auth_result['auth_code']
    print(f"auth_code: {auth_code}")
    # 2. 构造请求URL
    url = f"https://api-mifit-cn3.zepp.com/v1/thirdParties/auth.json?r={uuid.uuid4()}"
    
    # 3. 构造请求头
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Request-Id': str(uuid.uuid4()).upper(),
        'Host': 'api-mifit-cn3.zepp.com',
        'lang': 'zh_CN',
        'appplatform': 'ios_phone',
        'country': 'CN',  # 根据实际情况调整
        'channel': 'appstore',
        'Connection': 'keep-alive',
        'hm-privacy-ceip': 'false',
        'Accept-Language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
        'User-Agent': 'ZeppLife/6.14.0 (iPhone; iOS 26.1; Scale/3.00)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'v': '2.0',
        'appname': 'com.huami.midong',  # 根据实际情况调整
        'Accept': '*/*',
        'timezone': 'Asia/Shanghai',
        'cv': '319_6.14.0',  # 客户端版本
        'hm-privacy-diagnostics': 'false',
        'apptoken': apptoken
    }
    
    # 4. 构造请求体
    data = {
        "authCode": auth_code,
        "userid": userid
    }
    
    # 5. 发送请求
    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=10
        )
        
        # 检查响应状态
        if response.status_code != 200:
            return {
                "error": f"请求失败，状态码: {response.status_code}",
                "response": response.text
            }
        print(f"绑定结果: {response.text}")
        # 返回解析后的JSON响应
        return response.json()
    
    except Exception as e:
        return {
            "error": f"请求异常: {str(e)}"
        }


if __name__ == "__main__":

    apptoken = "ZQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAAItFxG8Tfsuh3GJFVA8d2szrL59eOylrJjMw6syLC0x1l0bbX0PW_zZcQJKVk9RNzAK8EMCqXkVHzUexfVg9TouD160e_Mta6xzHHibann69NE-NFDKrZCG3qFdAohyh2SNG_9lD9T9WYFCZ0EncC-2J06of0JfTY3fo14RsXBsHwczBSv-w09D7fXKXqFJN_A"
    userid = "1128782417"
    success = test_apptoken(apptoken)
    print(f"token: {'有效' if success else '无效'}")
    if success:
        #result1=test_band(apptoken,userid)
        result=test_band_v2(apptoken,userid)
        print(result)
        context_token, updated_cookie, trace_id, url = moni_alipay(result)
        if context_token:
            response = simulate_auth_post(context_token, updated_cookie, trace_id, url)
            bind_alipay_account(response, userid, apptoken)
