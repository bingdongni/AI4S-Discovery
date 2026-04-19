#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据加密模块
提供AES-256加密/解密功能，用于保护敏感数据
"""

import os
import base64
import hashlib
import secrets
from typing import Union, Optional
from pathlib import Path
from loguru import logger
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from src.core.config import settings


class EncryptionManager:
    """AES-256加密管理器"""

    def __init__(self, key: Optional[str] = None):
        """
        初始化加密管理器

        Args:
            key: 加密密钥（如果为None，则从环境变量或配置文件读取）
        """
        self.key = self._get_or_generate_key(key)
        self.backend = default_backend()
        logger.info("加密管理器初始化完成")

    def _get_or_generate_key(self, key: Optional[str]) -> bytes:
        """
        获取或生成加密密钥

        Args:
            key: 用户提供的密钥

        Returns:
            32字节的加密密钥
        """
        if key:
            # 使用用户提供的密钥
            return self._derive_key(key)

        # 尝试从环境变量读取
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            return self._derive_key(env_key)

        # 尝试从密钥文件读取
        key_file = self._get_key_file()
        if key_file.exists():
            try:
                with open(key_file, 'r') as f:
                    stored_key = f.read().strip()
                    if stored_key:
                        return self._derive_key(stored_key)
            except Exception:
                pass

        # 生成新密钥
        logger.warning("未找到加密密钥，生成新密钥")
        new_key = secrets.token_urlsafe(32)

        # 保存密钥到文件
        key_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(key_file, 'w') as f:
                f.write(new_key)
            # 设置文件权限为仅所有者可读（Unix系统）
            try:
                os.chmod(key_file, 0o600)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"无法保存密钥文件: {e}")

        logger.info(f"新密钥已保存至: {key_file}")
        logger.warning("请妥善保管密钥文件，丢失将无法解密数据！")

        return self._derive_key(new_key)

    def _get_key_file(self) -> Path:
        """获取密钥文件路径"""
        return Path(settings.DATA_DIR) / '.encryption_key'

    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        从密码派生密钥

        Args:
            password: 密码字符串
            salt: 盐值（如果为None，使用随机盐值）

        Returns:
            32字节的密钥
        """
        if salt is None:
            # 生成随机盐值
            salt = secrets.token_bytes(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )

        return kdf.derive(password.encode('utf-8'))

    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        加密数据

        Args:
            plaintext: 明文（字符串或字节）

        Returns:
            Base64编码的密文（包含盐值）
        """
        try:
            # 转换为字节
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')

            # 生成随机IV（初始化向量）
            iv = os.urandom(16)

            # 创建加密器
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()

            # PKCS7填充
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext) + padder.finalize()

            # 加密
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # 组合IV和密文，然后Base64编码
            encrypted_data = iv + ciphertext
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        解密数据

        Args:
            ciphertext: Base64编码的密文

        Returns:
            明文字符串
        """
        try:
            # Base64解码
            encrypted_data = base64.b64decode(ciphertext.encode('utf-8'))

            # 分离IV和密文
            iv = encrypted_data[:16]
            actual_ciphertext = encrypted_data[16:]

            # 创建解密器
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()

            # 解密
            padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()

            # 去除填充
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            return plaintext.decode('utf-8')

        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        加密文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（如果为None，则在原文件名后加.enc）

        Returns:
            加密后的文件路径
        """
        try:
            if output_path is None:
                output_path = f"{input_path}.enc"

            # 读取文件
            with open(input_path, 'rb') as f:
                plaintext = f.read()

            # 加密
            ciphertext = self.encrypt(plaintext)

            # 写入加密文件
            with open(output_path, 'w') as f:
                f.write(ciphertext)

            logger.info(f"文件已加密: {input_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"文件加密失败: {e}")
            raise

    def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        解密文件

        Args:
            input_path: 加密文件路径
            output_path: 输出文件路径（如果为None，则去除.enc后缀）

        Returns:
            解密后的文件路径
        """
        try:
            if output_path is None:
                if input_path.endswith('.enc'):
                    output_path = input_path[:-4]
                else:
                    output_path = f"{input_path}.dec"

            # 读取加密文件
            with open(input_path, 'r') as f:
                ciphertext = f.read()

            # 解密
            plaintext = self.decrypt(ciphertext)

            # 写入解密文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(plaintext)

            logger.info(f"文件已解密: {input_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"文件解密失败: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """
        使用bcrypt哈希密码（用于存储）

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except ImportError:
            # 如果bcrypt不可用，使用PBKDF2作为后备
            logger.warning("bcrypt不可用，使用PBKDF2作为后备")
            salt = secrets.token_bytes(32)
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            return salt.hex() + ':' + key.hex()

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            hashed: 哈希后的密码

        Returns:
            是否匹配
        """
        try:
            import bcrypt
            if ':' in hashed:
                # PBKDF2格式
                return False
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except ImportError:
            return False
        except Exception:
            return False

    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """
        加密字典中的指定字段

        Args:
            data: 数据字典
            fields: 需要加密的字段列表

        Returns:
            加密后的字典
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    value = str(encrypted_data[field])
                    encrypted_data[field] = self.encrypt(value)
                    encrypted_data[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.error(f"加密字段{field}失败: {e}")

        return encrypted_data

    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """
        解密字典中的指定字段

        Args:
            data: 加密的数据字典
            fields: 需要解密的字段列表

        Returns:
            解密后的字典
        """
        decrypted_data = data.copy()

        for field in fields:
            if field in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                    decrypted_data.pop(f"{field}_encrypted", None)
                except Exception as e:
                    logger.error(f"解密字段{field}失败: {e}")

        return decrypted_data

    def generate_token(self, data: str, expiry: Optional[int] = None) -> str:
        """
        生成加密令牌

        Args:
            data: 要加密的数据
            expiry: 过期时间（秒），None表示不过期

        Returns:
            加密令牌
        """
        import time
        import json

        token_data = {
            'data': data,
            'timestamp': int(time.time()),
            'expiry': expiry
        }

        return self.encrypt(json.dumps(token_data))

    def verify_token(self, token: str) -> Optional[str]:
        """
        验证并解密令牌

        Args:
            token: 加密令牌

        Returns:
            解密后的数据，如果令牌无效或过期则返回None
        """
        import time
        import json

        try:
            decrypted = self.decrypt(token)
            token_data = json.loads(decrypted)

            # 检查过期时间
            if token_data.get('expiry'):
                elapsed = int(time.time()) - token_data['timestamp']
                if elapsed > token_data['expiry']:
                    logger.warning("令牌已过期")
                    return None

            return token_data['data']

        except Exception as e:
            logger.error(f"令牌验证失败: {e}")
            return None


# 创建全局加密管理器实例
encryption_manager = EncryptionManager()


# 便捷函数
def encrypt(plaintext: Union[str, bytes]) -> str:
    """加密数据"""
    return encryption_manager.encrypt(plaintext)


def decrypt(ciphertext: str) -> str:
    """解密数据"""
    return encryption_manager.decrypt(ciphertext)


def hash_password(password: str) -> str:
    """哈希密码"""
    return encryption_manager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return encryption_manager.verify_password(password, hashed)
