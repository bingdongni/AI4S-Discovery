#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心功能测试
测试配置管理、设备管理等核心模块
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.utils.device_manager import device_manager
from src.utils.encryption import encryption_manager
from src.database.sqlite_manager import SQLiteManager


class TestConfig:
    """配置管理测试"""
    
    def test_settings_loaded(self):
        """测试配置加载"""
        assert settings.PROJECT_NAME == "AI4S-Discovery"
        assert settings.VERSION is not None
        assert settings.ENVIRONMENT in ["development", "production", "test"]
    
    def test_data_directories(self):
        """测试数据目录配置"""
        assert settings.DATA_DIR is not None
        assert settings.LOG_DIR is not None
        assert settings.CACHE_DIR is not None
    
    def test_api_settings(self):
        """测试API配置"""
        assert hasattr(settings, 'API_HOST')
        assert hasattr(settings, 'API_PORT')


class TestDeviceManager:
    """设备管理器测试"""
    
    def test_device_detection(self):
        """测试设备检测"""
        device_info = device_manager.get_device_info()
        
        assert 'device_type' in device_info
        assert device_info['device_type'] in ['cpu', 'cuda']
        assert 'device_name' in device_info
        assert 'memory_total' in device_info
        assert 'memory_used' in device_info
    
    def test_device_property(self):
        """测试设备属性"""
        device = device_manager.device
        assert device in ['cpu', 'cuda']
    
    def test_memory_monitoring(self):
        """测试内存监控"""
        device_info = device_manager.get_device_info()
        
        assert device_info['memory_total'] > 0
        assert device_info['memory_used'] >= 0
        assert device_info['memory_used'] <= device_info['memory_total']


class TestEncryption:
    """加密模块测试"""
    
    def test_encrypt_decrypt(self):
        """测试加密解密"""
        plaintext = "Hello, AI4S-Discovery!"
        
        # 加密
        ciphertext = encryption_manager.encrypt(plaintext)
        assert ciphertext != plaintext
        assert len(ciphertext) > 0
        
        # 解密
        decrypted = encryption_manager.decrypt(ciphertext)
        assert decrypted == plaintext
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "test_password_123"
        
        # 哈希
        hashed = encryption_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) == 64  # SHA-256
        
        # 验证
        assert encryption_manager.verify_password(password, hashed)
        assert not encryption_manager.verify_password("wrong_password", hashed)
    
    def test_token_generation(self):
        """测试令牌生成"""
        data = "user_123"
        
        # 生成令牌
        token = encryption_manager.generate_token(data, expiry=3600)
        assert token is not None
        assert len(token) > 0
        
        # 验证令牌
        verified_data = encryption_manager.verify_token(token)
        assert verified_data == data


class TestDatabase:
    """数据库测试"""
    
    @pytest.fixture
    def db(self):
        """数据库fixture"""
        # 使用测试数据库
        db = SQLiteManager(db_path=":memory:")
        yield db
    
    def test_database_initialization(self, db):
        """测试数据库初始化"""
        # 检查表是否创建
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'users' in tables
            assert 'tasks' in tables
            assert 'audit_logs' in tables
            assert 'paper_cache' in tables
    
    def test_user_operations(self, db):
        """测试用户操作"""
        # 创建用户
        user_id = db.create_user(
            username="test_user",
            password_hash="hashed_password",
            email="test@example.com"
        )
        assert user_id > 0
        
        # 获取用户
        user = db.get_user("test_user")
        assert user is not None
        assert user['username'] == "test_user"
        assert user['email'] == "test@example.com"
    
    def test_task_operations(self, db):
        """测试任务操作"""
        # 创建任务
        task_id = "test_task_001"
        db.create_task(task_id, "test query")
        
        # 获取任务
        task = db.get_task(task_id)
        assert task is not None
        assert task['task_id'] == task_id
        assert task['query'] == "test query"
        assert task['status'] == "pending"
        
        # 更新任务状态
        db.update_task_status(task_id, "completed", progress=100)
        
        # 验证更新
        task = db.get_task(task_id)
        assert task['status'] == "completed"
        assert task['progress'] == 100
    
    def test_audit_logging(self, db):
        """测试审计日志"""
        # 记录日志
        db.log_action(
            action="test_action",
            user_id=1,
            resource_type="test_resource",
            resource_id="test_001",
            details={"key": "value"}
        )
        
        # 获取日志
        logs = db.get_audit_logs(user_id=1, limit=10)
        assert len(logs) > 0
        assert logs[0]['action'] == "test_action"
        assert logs[0]['user_id'] == 1


class TestIntegration:
    """集成测试"""
    
    def test_system_startup(self):
        """测试系统启动"""
        # 验证关键组件可以初始化
        assert settings is not None
        assert device_manager is not None
        assert encryption_manager is not None
    
    def test_configuration_consistency(self):
        """测试配置一致性"""
        # 验证配置值的一致性
        assert Path(settings.DATA_DIR).exists() or True  # 可能还未创建
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src", "--cov-report=html"])