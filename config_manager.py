# -*- coding: utf-8 -*-
"""
DeskHelperGUI 配置管理模块
管理用户配置的读取和保存
"""

import os
import sys
import json
from pathlib import Path


class ConfigManager:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'language': 'zh',           # 语言设置
        'last_feature': 'quick_compress',  # 上次使用的功能
        'save_path': '',            # 全局保存路径
        'compress': {
            'format': 'ZIP',        # 压缩格式
            'level': 2,             # 压缩级别索引 (0-4)
            'encrypt': False,       # 是否加密
        },
        'hash_checker': {
            'mode': 'SHA256',       # 哈希模式
        }
    }

    def __init__(self, config_file='config.json'):
        """初始化配置管理器"""
        # 配置文件路径（在用户AppData目录下）
        self.config_path = self._get_config_path(config_file)
        self.config = self._load_config()

    def _get_config_path(self, config_file):
        """获取配置文件路径（保存在用户AppData目录下）"""
        # 使用用户AppData目录
        appdata_path = os.environ.get('APPDATA')
        if appdata_path:
            config_dir = os.path.join(appdata_path, 'DeskHelperGUI')
        else:
            # 回退到用户主目录
            config_dir = os.path.join(os.path.expanduser('~'), '.DeskHelperGUI')
        
        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        return os.path.join(config_dir, config_file)

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（确保新增的配置项存在）
                return self._merge_config(self.DEFAULT_CONFIG, config)
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def _merge_config(self, default, loaded):
        """合并配置，保留默认值"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_config(result[key], value)
                else:
                    result[key] = value
        return result

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_language(self):
        """获取语言设置"""
        return self.get('language', 'zh')

    def set_language(self, lang):
        """设置语言"""
        self.set('language', lang)
        self.save_config()

    def get_last_feature(self):
        """获取上次使用的功能"""
        return self.get('last_feature', 'quick_compress')

    def set_last_feature(self, feature):
        """设置上次使用的功能"""
        self.set('last_feature', feature)
        self.save_config()

    def get_compress_settings(self):
        """获取压缩设置"""
        return self.get('compress', {})

    def set_compress_settings(self, settings):
        """设置压缩设置"""
        self.set('compress', settings)
        self.save_config()

    def get_save_path(self):
        """获取全局保存路径"""
        return self.get('save_path', '')

    def set_save_path(self, path):
        """设置全局保存路径"""
        self.set('save_path', path)
        self.save_config()