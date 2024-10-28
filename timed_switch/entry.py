import time
import os
from datetime import datetime, timedelta
from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'timed_switch',
    'version': '1.0.0',
    'name': 'Timed Server Switch',
    'description': 'A plugin to schedule server start and stop times in MCDReforged',
    'author': 'xunfeng'
}

CONFIG_PATH = os.path.join('config', 'timed_switch_config.json')

class TimedSwitchPlugin:
    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.load_config()

    def load_config(self):
        """加载插件配置"""
        default_config = {
            'shutdown_time': '00:00',  # 默认关闭时间
            'restart_time': '20:00',  # 默认重启时间
            'warning_minutes': 5,      # 提前5分钟警告
            'warning_seconds': 10     # 提前10秒每秒警告
        }
        self.config = self.server.load_config_simple(CONFIG_PATH, default_config)

    def check_time(self, now):
        """检查服务器时间并执行相应任务"""
        shutdown_time = datetime.strptime(self.config['shutdown_time'], "%H:%M").replace(
            year=now.year, month=now.month, day=now.day)
        restart_time = datetime.strptime(self.config['restart_time'], "%H:%M").replace(
            year=now.year, month=now.month, day=now.day)

        if (shutdown_time < restart_time):
            shutdown_time += timedelta(days=1)

        if (now >= restart_time and now <= shutdown_time):
            pass
        elif (now >= restart_time - timedelta(days=1) and now <= shutdown_time - timedelta(days=1)):
            pass
        else:
            if (self.server.is_server_startup()):
                self.server.logger.info('Server is not in scheduled time range, stopping server...')
                self.server.stop()

        # 如果时间已过，则移至次日
        if now >= shutdown_time:
            shutdown_time += timedelta(days=1)
        if now >= restart_time:
            restart_time += timedelta(days=1)
        
        if (equal_time(now, shutdown_time - timedelta(minutes=self.config['warning_minutes']))):
            self.shutdown_warning()
        
        if (equal_time(now, shutdown_time - timedelta(seconds=self.config['warning_seconds']))):
            self.start_countdown()

        if (equal_time(now, shutdown_time)):
            self.server.logger.info('Server is scheduled to shutdown, stopping server...')
            self.shutdown_server()
        elif (equal_time(now, restart_time)):
            self.server.logger.info('Server is scheduled to restart, restarting server...')
            self.restart_server()

    def shutdown_warning(self):
        """关闭前的警告"""
        self.server.say("§c服务器将于5分钟后关闭!")

    @new_thread("timed_switch_countdown_task")
    def start_countdown(self):
        """开始10秒倒计时"""
        for i in range(10, 0, -1):
            self.server.say(f"§c服务器将于{i}秒后关闭!")
            time.sleep(1)

    def shutdown_server(self):
        """关闭服务器"""
        self.server.logger.info("Server is shutting down...")
        self.server.stop()

    def restart_server(self):
        """重启服务器"""
        self.server.logger.info("Server is restarting...")
        self.server.start()

@new_thread("timed_switch_task")
def on_load(server: PluginServerInterface, old_module):
    plugin = TimedSwitchPlugin(server)
    while True:
        now = datetime.now()
        plugin.check_time(now)
        time.sleep(1)

def equal_time(time1, time2):
    """判断两个时间是否相等"""
    return time1.hour == time2.hour and time1.minute == time2.minute and time1.second == time2.second