
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
返利转链核心模块 - 基于官方文档重构
严格按照大淘客、京品库、多多进宝官方文档实现
"""

import re
import requests
import logging
import json
import hashlib
import time
from urllib.parse import urlparse, quote
from typing import Optional, Dict, Any

class AffiliateConverter:
    """返利转链处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # API配置
        affiliate_config = config.get('affiliate_config', {})
        self.dataoke_config = affiliate_config.get('dataoke', {})
        self.jingpinku_config = affiliate_config.get('jingpinku', {})
        self.pdd_config = affiliate_config.get('pdd', {})
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def convert_url(self, url: str) -> str:
        """转换单个URL - 公共接口"""
        return self._convert_single_link(url)
    
    def convert_links(self, text: str) -> str:
        """智能识别并转换文本中的商品链接"""
        if not text:
            return text
            
        # 查找所有可能的商品链接
        urls = self._extract_urls(text)
        converted_text = text
        
        # 获取批次转链限制配置
        batch_settings = self.config.get('affiliate_config', {}).get('batch_settings', {})
        convert_enabled = batch_settings.get('convert_enabled', True)
        max_convert_per_batch = batch_settings.get('max_convert_per_batch', 10)  # 默认最多10个
        
        if not convert_enabled:
            self.logger.info("转链功能已禁用")
            return converted_text
        
        # 限制转链数量
        if len(urls) > max_convert_per_batch:
            self.logger.info(f"检测到{len(urls)}个商品链接，限制转换前{max_convert_per_batch}个")
            urls = urls[:max_convert_per_batch]
        
        convert_count = 0
        for url in urls:
            converted_url = self._convert_single_link(url)
            if converted_url and converted_url != url:
                converted_text = converted_text.replace(url, converted_url)
                convert_count += 1
                self.logger.info(f"转链成功: {url} -> {converted_url}")
        
        if convert_count > 0:
            self.logger.info(f"本批次成功转换{convert_count}个商品链接")
                
        return converted_text
    
    def _extract_urls(self, text: str) -> list:
        """提取文本中的所有URL"""
        url_patterns = [
            r'https?://[^\s<>"]+',  # 标准HTTP/HTTPS链接
            r'https?://(?:s\.click\.taobao|u\.jd|p\.pinduoduo)\.com/[^\s]*'  # 短链接
        ]
        
        urls = []
        for pattern in url_patterns:
            urls.extend(re.findall(pattern, text))
        
        # 去重
        return list(set(urls))
    
    def _convert_single_link(self, url: str) -> str:
        """转换单个链接"""
        try:
            platform = self._detect_platform(url)
            
            if platform == 'taobao':
                return self._convert_taobao_link(url)
            elif platform == 'jd':
                return self._convert_jd_link(url)
            elif platform == 'pdd':
                return self._convert_pdd_link(url)
                
            return url
            
        except Exception as e:
            self.logger.error(f"转链异常: {url} - {e}")
            return url
    
    def _detect_platform(self, url: str) -> str:
        """检测链接平台"""
        if any(x in url.lower() for x in ['taobao.com', 'tmall.com', 's.click.taobao.com']):
            return 'taobao'
        elif any(x in url.lower() for x in ['pinduoduo.com', 'yangkeduo.com', 'p.pinduoduo.com']):
            return 'pdd'
        elif any(x in url.lower() for x in ['jd.com', 'u.jd.com', 'item.jd.com']):
            return 'jd'
        return 'unknown'
    
    def _convert_taobao_link(self, url: str) -> str:
        """
        大淘客转链 - 万能解析转链
        API文档: https://www.dataoke.com/kfpt/api-d.html?id=33
        """
        if not self.dataoke_config.get('enabled') or not self.dataoke_config.get('app_key'):
            self.logger.warning("大淘客配置未启用或缺少配置")
            return url
            
        try:
            api_url = "https://openapi.dataoke.com/api/tb-service/parse-content"
            
            # 生成nonce和timer
            import random
            nonce = str(random.randint(100000, 999999))  # 6位随机数
            timer = str(int(time.time() * 1000))  # 毫秒级时间戳
            
            params = {
                'appKey': self.dataoke_config['app_key'],
                'version': 'v1.0.0',
                'content': url,
                'nonce': nonce,
                'timer': timer
            }
            
            # 生成新版签名
            params['signRan'] = self._generate_dataoke_sign_new(params)
            
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0:
                    data = result.get('data', {})
                    
                    # 按优先级获取转链结果
                    converted_url = (
                        data.get('shortUrl') or           # 短链接
                        data.get('shortTpwd') or          # 短口令
                        data.get('cpsFullTpwd') or        # CPS转链长口令
                        data.get('cpsLongUrl') or         # CPS转链长链
                        data.get('itemLink')              # 商品链接
                    )
                    
                    if converted_url and converted_url != url:
                        self.logger.info(f"大淘客转链成功: {url} -> {converted_url}")
                        return converted_url
                    else:
                        self.logger.warning(f"大淘客解析成功但无转链结果: {data}")
                else:
                    self.logger.error(f"大淘客API错误: {result.get('msg')}")
            else:
                self.logger.error(f"大淘客HTTP错误: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"大淘客转链异常: {e}")
            
        return url
    
    def _convert_jd_link(self, url: str) -> str:
        """
        京品库万能转链 - 严格按照官方文档实现
        API文档: https://api.jingpinku.com/get_wire_report_link/api
        
        京品库使用万能转链接口，需要将链接作为文案内容传递
        """
        if not self.jingpinku_config.get('enabled') or not self.jingpinku_config.get('appid'):
            self.logger.warning("京品库配置未启用或缺少配置")
            return url
            
        try:
            api_url = "https://api.jingpinku.com/get_wire_report_link/api"
            
            # 按官方文档构建参数 - 万能转链接口
            params = {
                'appid': self.jingpinku_config['appid'],
                'appkey': self.jingpinku_config['appkey'],
                'union_id': self.jingpinku_config.get('union_id', ''),
                'content': url  # 将链接作为文案内容传递
            }
                
            self.logger.info(f"京品库万能转链请求: {api_url} with params: {params}")
            
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"京品库万能转链响应: {result}")
                
                # 按官方文档，成功时返回格式包含content字段
                if result.get('code') == 0:
                    content = result.get('content', '')
                    official = result.get('official', '')
                    
                    # 万能转链成功，优先使用official文案（包含完整推广信息）
                    if official:
                        # 从official文案中提取转链后的京东链接
                        import re
                        jd_links = re.findall(r'https://u\.jd\.com/[A-Za-z0-9]+', official)
                        if jd_links:
                            converted_url = jd_links[0]
                            self.logger.info(f"京品库万能转链成功: {url} -> {converted_url}")
                            return converted_url
                        else:
                            self.logger.info(f"京品库万能转链成功，返回官方文案: {official}")
                            return official
                    elif content:
                        # 如果没有official文案，使用content
                        import re
                        jd_links = re.findall(r'https://u\.jd\.com/[A-Za-z0-9]+', content)
                        if jd_links:
                            converted_url = jd_links[0]
                            if converted_url != url:  # 确保转链结果不同
                                self.logger.info(f"京品库万能转链成功: {url} -> {converted_url}")
                                return converted_url
                        
                        # 如果content与原链接相同，说明API成功但没有转链
                        self.logger.info(f"京品库万能转链API调用成功，内容: {content}")
                        return content
                    else:
                        self.logger.warning(f"京品库万能转链响应为空")
                        return url
                else:
                    # 处理错误响应
                    error_msg = result.get('msg', result.get('message', '未知错误'))
                    self.logger.error(f"京品库万能转链API错误: {error_msg}")
                    return url
            else:
                self.logger.error(f"京品库万能转链HTTP错误: {response.status_code} - {response.text}")
                return url
                
        except Exception as e:
            self.logger.error(f"京品库万能转链异常: {e}")
            return url
    
    def _convert_pdd_link(self, url: str) -> str:
        """
        拼多多转链 - 多多进宝API
        使用推广链接生成接口
        """
        if not self.pdd_config.get('enabled') or not self.pdd_config.get('client_id'):
            self.logger.warning("拼多多配置未启用或缺少配置")
            return url
            
        try:
            api_url = "https://gw-api.pinduoduo.com/api/router"
            timestamp = str(int(time.time()))
            
            # 使用最简参数，按照调试成功的版本
            params = {
                'type': 'pdd.ddk.goods.zs.unit.url.gen',
                'client_id': self.pdd_config['client_id'],
                'access_token': '',
                'timestamp': timestamp,
                'data_type': 'JSON',
                'version': 'V1',
                'pid': self.pdd_config.get('pid', ''),
                'source_url': url
            }
            
            # 生成签名
            params['sign'] = self._generate_pdd_sign(params)
            
            response = self.session.post(api_url, data=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('error_response'):
                    error_msg = result['error_response'].get('error_msg', '未知错误')
                    self.logger.error(f"拼多多API错误: {error_msg}")
                    return url
                
                goods_response = result.get('goods_zs_unit_generate_response', {})
                
                # 直接从响应中获取转链结果，而不是从goods_list数组
                converted_url = (
                    goods_response.get('multi_group_mobile_short_url') or
                    goods_response.get('mobile_short_url') or
                    goods_response.get('short_url') or
                    goods_response.get('multi_group_short_url') or
                    goods_response.get('url') or
                    goods_response.get('mobile_url')
                )
                
                if converted_url and converted_url != url:
                    self.logger.info(f"拼多多转链成功: {url} -> {converted_url}")
                    return converted_url
                else:
                    self.logger.warning("拼多多API未返回有效的转链结果")
            else:
                self.logger.error(f"拼多多HTTP错误: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"拼多多转链异常: {e}")
            
        return url
    
    def _extract_pdd_goods_id(self, url: str) -> Optional[str]:
        """提取拼多多商品ID"""
        patterns = [
            r'goods_id=(\d+)',
            r'/goods/(\d+)',
            r'goods\.html.*?goods_id=(\d+)',
            r'/(\d{10,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 尝试解析短链接
        try:
            response = self.session.head(url, allow_redirects=True, timeout=5)
            if response.url != url:
                return self._extract_pdd_goods_id(response.url)
        except:
            pass
            
        return None
    
    def _generate_dataoke_sign_new(self, params: Dict[str, Any]) -> str:
        """
        生成大淘客API新版签名 (2020年5月升级版本)
        签名算法: appKey=xxx&timer=xxx&nonce=xxx&key=xxx
        """
        # 构造签名字符串: appKey=xxx&timer=xxx&nonce=xxx&key=xxx
        sign_string = f"appKey={params['appKey']}&timer={params['timer']}&nonce={params['nonce']}&key={self.dataoke_config['app_secret']}"
        
        # MD5加密并转大写
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
    
    def _generate_pdd_sign(self, params: Dict[str, Any]) -> str:
        """
        生成拼多多API签名
        签名算法: MD5(client_secret + 排序参数字符串 + client_secret).upper()
        """
        # 按key排序
        sorted_params = sorted(params.items())
        
        # 拼接参数: key1value1key2value2...
        param_string = ''.join([f'{k}{v}' for k, v in sorted_params])
        
        # 构造签名字符串: secret + params + secret
        sign_string = f"{self.pdd_config['client_secret']}{param_string}{self.pdd_config['client_secret']}"
        
        # MD5加密并转大写
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()