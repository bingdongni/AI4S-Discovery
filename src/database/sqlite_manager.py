#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite数据库管理器
负责用户权限、任务进度、审计日志等数据的持久化存储
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
from contextlib import contextmanager

from src.core.config import settings


class SQLiteManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认使用配置中的路径
        """
        self.db_path = db_path or settings.SQLITE_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"SQLite数据库初始化完成: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    query TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    result TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 文献缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT,
                    authors TEXT,
                    abstract TEXT,
                    year INTEGER,
                    citation_count INTEGER,
                    quality_score REAL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 搜索历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT NOT NULL,
                    filters TEXT,
                    result_count INTEGER,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # 报告表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    task_id TEXT,
                    report_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    format TEXT DEFAULT 'markdown',
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_user_id 
                ON tasks(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id 
                ON audit_logs(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_paper_cache_source 
                ON paper_cache(source)
            """)
            
            logger.info("数据库表结构初始化完成")
    
    # ==================== 用户管理 ====================
    
    def create_user(self, username: str, password_hash: str, email: str = None, role: str = 'user') -> int:
        """创建用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, email, role))
            user_id = cursor.lastrowid
            logger.info(f"创建用户: {username} (ID: {user_id})")
            return user_id
    
    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id,))
    
    # ==================== 任务管理 ====================
    
    def create_task(self, task_id: str, query: str, user_id: Optional[int] = None) -> int:
        """创建任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_id, user_id, query)
                VALUES (?, ?, ?)
            """, (task_id, user_id, query))
            task_db_id = cursor.lastrowid
            logger.info(f"创建任务: {task_id}")
            return task_db_id
    
    def update_task_status(self, task_id: str, status: str, progress: int = None, error_message: str = None):
        """更新任务状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == 'completed':
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, progress = ?, error_message = ?, 
                        updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (status, progress or 100, error_message, task_id))
            else:
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, progress = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (status, progress, error_message, task_id))
    
    def update_task_result(self, task_id: str, result: Dict):
        """更新任务结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks 
                SET result = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ?
            """, (json.dumps(result, ensure_ascii=False), task_id))
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                task = dict(row)
                if task.get('result'):
                    task['result'] = json.loads(task['result'])
                return task
            return None
    
    def get_user_tasks(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取用户的任务列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 审计日志 ====================
    
    def log_action(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """记录审计日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs 
                (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(details, ensure_ascii=False) if details else None,
                ip_address,
                user_agent
            ))
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """获取审计日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = [dict(row) for row in cursor.fetchall()]
            
            for log in logs:
                if log.get('details'):
                    log['details'] = json.loads(log['details'])
            
            return logs
    
    # ==================== 文献缓存 ====================
    
    def cache_paper(self, paper: Dict):
        """缓存文献信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO paper_cache 
                (paper_id, source, title, authors, abstract, year, citation_count, quality_score, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                paper.get('paperId') or paper.get('id'),
                paper.get('source', 'unknown'),
                paper.get('title'),
                json.dumps(paper.get('authors', []), ensure_ascii=False),
                paper.get('abstract'),
                paper.get('year'),
                paper.get('citationCount', 0),
                paper.get('quality_score'),
                json.dumps(paper, ensure_ascii=False)
            ))
    
    def get_cached_paper(self, paper_id: str) -> Optional[Dict]:
        """获取缓存的文献"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM paper_cache WHERE paper_id = ?", (paper_id,))
            row = cursor.fetchone()
            if row:
                paper = dict(row)
                if paper.get('metadata'):
                    paper['metadata'] = json.loads(paper['metadata'])
                if paper.get('authors'):
                    paper['authors'] = json.loads(paper['authors'])
                return paper
            return None
    
    # ==================== 搜索历史 ====================
    
    def save_search_history(
        self,
        query: str,
        result_count: int,
        execution_time: float,
        user_id: Optional[int] = None,
        filters: Dict = None
    ):
        """保存搜索历史"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history 
                (user_id, query, filters, result_count, execution_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                query,
                json.dumps(filters, ensure_ascii=False) if filters else None,
                result_count,
                execution_time
            ))
    
    def get_search_history(self, user_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """获取搜索历史"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM search_history 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM search_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            history = [dict(row) for row in cursor.fetchall()]
            
            for item in history:
                if item.get('filters'):
                    item['filters'] = json.loads(item['filters'])
            
            return history
    
    # ==================== 报告管理 ====================
    
    def save_report(
        self,
        report_id: str,
        report_type: str,
        title: str,
        content: str,
        user_id: Optional[int] = None,
        task_id: Optional[str] = None,
        format: str = 'markdown',
        file_path: str = None
    ) -> int:
        """保存报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports 
                (report_id, user_id, task_id, report_type, title, content, format, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_id, user_id, task_id, report_type, title, content, format, file_path))
            report_db_id = cursor.lastrowid
            logger.info(f"保存报告: {report_id}")
            return report_db_id
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """获取报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_reports(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取用户的报告列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reports 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户统计
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            active_users = cursor.fetchone()['count']
            
            # 任务统计
            cursor.execute("SELECT COUNT(*) as count FROM tasks")
            total_tasks = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'completed'")
            completed_tasks = cursor.fetchone()['count']
            
            # 文献统计
            cursor.execute("SELECT COUNT(*) as count FROM paper_cache")
            cached_papers = cursor.fetchone()['count']
            
            # 报告统计
            cursor.execute("SELECT COUNT(*) as count FROM reports")
            total_reports = cursor.fetchone()['count']
            
            return {
                'active_users': active_users,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'cached_papers': cached_papers,
                'total_reports': total_reports,
                'completion_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
            }


# 创建全局数据库管理器实例
db_manager = SQLiteManager()