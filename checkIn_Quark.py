import os 
import re 
import sys 
import requests 

cookie_list = os.getenv("COOKIE_QUARK").split('\n|&&')

# 替代 notify 功能
def send(title, message):
    print(f"{title}: {message}")

# 获取环境变量 
def get_env(): 
    # 判断 COOKIE_QUARK是否存在于环境变量 
    if "COOKIE_QUARK" in os.environ: 
        # 读取系统变量以 \n 或 && 分割变量 
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK')) 
    else: 
        # 标准日志输出 
        print('❌未添加COOKIE_QUARK变量') 
        send('夸克自动签到', '❌未添加COOKIE_QUARK变量') 
        # 脚本退出 
        sys.exit(1) 

    return cookie_list 

class Quark:
    '''
    Quark类封装了签到、领取签到奖励的方法
    '''
    def __init__(self, user_data):
        '''
        初始化方法
        :param user_data: 用户信息，用于后续的请求
        '''
        self.param = user_data

    def convert_bytes(self, b):
        '''
        将字节转换为 MB GB TB
        :param b: 字节数
        :return: 返回 MB GB TB
        '''
        units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while b >= 1024 and i < len(units) - 1:
            b /= 1024
            i += 1
        return f"{b:.2f} {units[i]}"

    def get_growth_info(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        response = requests.get(url=url, params=querystring).json()
        return response.get("data", False)

    def get_growth_sign(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {
            "pr": "ucpro",
            "fr": "android",
            "kps": self.param.get('kps'),
            "sign": self.param.get('sign'),
            "vcode": self.param.get('vcode')
        }
        data = {"sign_cyclic": True}
        response = requests.post(url=url, json=data, params=querystring).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response.get("message", "未知错误")

    def queryBalance(self):
        '''
        查询抽奖余额
        '''
        url = "https://coral2.quark.cn/currency/v1/queryBalance"
        querystring = {
            "moduleCode": "1f3563d38896438db994f118d4ff53cb",
            "kps": self.param.get('kps'),
        }
        response = requests.get(url=url, params=querystring).json()
        return response.get("data", {}).get("balance", response.get("msg", "查询失败"))

    def do_sign(self):
        '''
        执行签到任务
        :return: 返回一个元组，包含success（布尔值）和log字符串
        '''
        log = ""
        # 每日领空间
        growth_info = self.get_growth_info()
        if growth_info:
            log += (
                f" {'88VIP' if growth_info['88VIP'] else '普通用户'} {self.param.get('user')}\n"
                f"💾 网盘总容量：{self.convert_bytes(growth_info['total_capacity'])}，"
                f"签到累计容量：")
            if "sign_reward" in growth_info['cap_composition']:
                log += f"{self.convert_bytes(growth_info['cap_composition']['sign_reward'])}\n"
            else:
                log += "0 MB\n"
            if growth_info["cap_sign"]["sign_daily"]:
                log += (
                    f"✅ 签到日志: 今日已签到+{self.convert_bytes(growth_info['cap_sign']['sign_daily_reward'])}，"
                    f"连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})\n"
                )
                return True, log
            else:
                sign, sign_return = self.get_growth_sign()
                if sign:
                    log += (
                        f"✅ 执行签到: 今日签到+{self.convert_bytes(sign_return)}，"
                        f"连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})\n"
                    )
                    return True, log
                else:
                    log += f"❌ 签到异常: {sign_return}\n"
                    return False, log
        else:
            log += f"❌ 签到异常: 获取成长信息失败\n"
            return False, log


def main():
    '''
    主函数
    :return: 返回一个字符串，包含签到结果
    '''
    msg = ""
    has_error = False
    cookie_quark = get_env()

    print("✅ 检测到共", len(cookie_quark), "个夸克账号\n")

    i = 0
    while i < len(cookie_quark):
        # 获取user_data参数
        user_data = {}  # 用户信息
        for a in cookie_quark[i].replace(" ", "").split(';'):
            if not a == '':
                user_data.update({a[0:a.index('=')]: a[a.index('=') + 1:]})
        # 开始任务
        log_prefix = f"🙍🏻‍♂️ 第{i + 1}个账号"
        msg += log_prefix
        # 登录
        success, log = Quark(user_data).do_sign()
        msg += log + "\n"
        if not success:
            has_error = True
        i += 1

    # 发送通知
    send('夸克自动签到', msg)
    
    # 如果有错误，退出并返回非零码
    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
