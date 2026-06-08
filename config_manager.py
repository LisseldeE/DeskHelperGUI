# -*- coding: utf-8 -*-
"""
DeskHelperGUI 配置管理模块
管理用户配置的读取和保存
"""

import os
import json
from pathlib import Path


class ConfigManager:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        'language': 'zh',           # 语言设置
        'last_feature': 'quick_compress',  # 上次使用的功能
        'compress': {
            'format': 'ZIP',        # 压缩格式
            'level': 2,             # 压缩级别索引 (0-4)
            'save_path': '',        # 保存路径
            'encrypt': False,       # 是否加密
        }
    }

    def __init__(self, config_file='config.json'):
        """初始化配置管理器"""
        # 配置文件路径（在程序目录下）
        self.config_path = self._get_config_path(config_file)
        self.config = self._load_config()

    def _get_config_path(self, config_file):
        """获取配置文件路径"""
        # 尝试获取程序所在目录
        try:
            # PyInstaller打包后的路径
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_path = os.getcwd()

        return os.path.join(base_path, config_file)

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
        """获取保存路径"""
        return self.get('compress.save_path', '')

    def set_save_path(self, path):
        """设置保存路径"""
        self.set('compress.save_path', path)
        self.save_config()


# 导入sys模块（用于获取程序路径）
import sys