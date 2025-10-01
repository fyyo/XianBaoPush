# src/core/qq_pusher.py - Handles sending messages to QQ groups.
import requests
import logging

def send_group_message(api_url, group_id, message):
    """发送QQ群消息"""
    try:
        qq_message = {
            "group_id": int(group_id),
            "message": message
        }
        
        full_api_url = f"{api_url}/send_group_msg"
        response = requests.post(full_api_url, json=qq_message, timeout=10)
        response.raise_for_status()
        logging.info(f"成功推送到QQ群: {group_id}")
        return True
    except Exception as e:
        logging.error(f"推送到QQ群失败: {group_id} - {e}")
        return False
