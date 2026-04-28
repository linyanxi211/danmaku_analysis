"""
辅助函数模块
"""
import os
import re
import requests
from typing import Dict, Optional


def get_xml_url(
        url: str,
        headers: Dict[str, str]
) -> str:
    """
    从B站视频URL获取弹幕XML的URL
    """
    bv_match = re.findall(r'(BV.{10})', url)
    if not bv_match:
        raise ValueError(f"无法从URL中提取BV号: {url}")
    bv = bv_match[0]

    response = requests.get(
        url='https://www.bilibili.com/video/' + bv,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        raise Exception(f"获取视频页面失败: {response.status_code}")

    content = response.text
    cid_match = re.findall(r'"cid":(\d+),', content)
    if not cid_match:
        raise Exception("无法获取视频CID")
    cid = cid_match[0]
    
    xml_url = f'https://comment.bilibili.com/{cid}.xml'

    return xml_url


def get_bvid_from_url(url: str) -> str:
    """
    从URL中提取BV号
    """
    match = re.search(r'BV\w+', url)
    if match:
        return match.group()
    raise ValueError(f"无法从URL中提取BV号: {url}")


def set_path(
        path: Optional[str] = None
) -> str:
    """
    设置路径
    """
    if path is None:
        path = os.getcwd()
        print('当前工作目录:', path)
    return path


def ensure_dir(path: str) -> str:
    """
    确保目录存在
    """
    os.makedirs(path, exist_ok=True)
    return path


def extract_bvid(url: str) -> str:
    """
    从URL中提取BV号（与get_bvid_from_url功能相同，保留两个名字便于兼容）
    """
    return get_bvid_from_url(url)