#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM客户端模块
支持OpenAI API和本地模型（MiniCPM）
"""

import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger

from src.core.config import settings


class LLMClient:
    """LLM客户端基类"""
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """生成文本"""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API客户端"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
        if not self.api_key:
            logger.warning("OpenAI API密钥未设置，将使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            try:
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
                logger.info("OpenAI客户端初始化成功")
            except ImportError:
                logger.error("未安装openai库，请运行: pip install openai")
                self.mock_mode = True
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
        
        Returns:
            str: 生成的文本
        """
        if self.mock_mode:
            return self._mock_generate(prompt)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个科研助手，擅长分析文献和生成创新假设。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                **kwargs
            )
            
            result = response.choices[0].message.content
            logger.debug(f"OpenAI生成成功，长度: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> str:
        """模拟生成（用于测试）"""
        logger.warning("使用模拟模式生成内容")
        
        if "假设" in prompt or "hypothesis" in prompt.lower():
            return """基于文献分析，我们提出以下创新假设：

1. 跨域方法迁移可能带来突破性进展
2. 结合多个领域的优势可以解决现有问题
3. 新的技术路线具有较高的可行性

该假设基于对现有研究的深入分析，具有较强的理论支撑和实践价值。"""
        
        elif "反事实" in prompt or "counterfactual" in prompt.lower():
            return """反事实推理分析：

场景1：如果采用不同的技术路线
- 可能的结果：效率提升30%
- 风险：技术成熟度较低

场景2：如果增加资源投入
- 可能的结果：缩短研发周期
- 风险：成本增加

场景3：如果改变研究方向
- 可能的结果：发现新的应用场景
- 风险：偏离原有目标"""
        
        else:
            return "这是一个基于LLM的分析结果。由于API密钥未设置，当前使用模拟模式。"


class LocalModelClient(LLMClient):
    """本地模型客户端（MiniCPM）"""
    
    def __init__(self):
        """初始化本地模型客户端"""
        self.model_path = settings.LOCAL_MODEL_PATH
        self.max_length = settings.MINICPM_MAX_LENGTH
        self.model = None
        self.tokenizer = None
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"正在加载本地模型: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if settings.DEVICE == "cuda" else torch.float32,
                device_map="auto" if settings.DEVICE == "cuda" else None
            )
            
            if settings.DEVICE == "cpu":
                self.model = self.model.to("cpu")
            
            logger.success("本地模型加载成功")
            
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
            logger.warning("将使用模拟模式")
            self.model = None
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
        
        Returns:
            str: 生成的文本
        """
        if self.model is None:
            return self._mock_generate(prompt)
        
        try:
            # 在线程池中运行模型推理（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._sync_generate,
                prompt,
                max_tokens,
                temperature
            )
            return result
            
        except Exception as e:
            logger.error(f"本地模型生成失败: {e}")
            return self._mock_generate(prompt)
    
    def _sync_generate(
        self,
        prompt: str,
        max_tokens: Optional[int],
        temperature: Optional[float]
    ) -> str:
        """同步生成（在线程池中运行）"""
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        if settings.DEVICE == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens or 512,
            temperature=temperature or 0.7,
            do_sample=True,
            top_p=0.9,
        )
        
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 移除输入部分
        if result.startswith(prompt):
            result = result[len(prompt):].strip()
        
        return result
    
    def _mock_generate(self, prompt: str) -> str:
        """模拟生成"""
        logger.warning("本地模型未加载，使用模拟模式")
        return OpenAIClient()._mock_generate(prompt)


class LLMClientFactory:
    """LLM客户端工厂"""
    
    _instance: Optional[LLMClient] = None
    
    @classmethod
    def get_client(cls) -> LLMClient:
        """
        获取LLM客户端实例（单例模式）
        
        Returns:
            LLMClient: LLM客户端实例
        """
        if cls._instance is None:
            if settings.USE_LOCAL_MODEL:
                logger.info("使用本地模型")
                cls._instance = LocalModelClient()
            else:
                logger.info("使用OpenAI API")
                cls._instance = OpenAIClient()
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置客户端实例"""
        cls._instance = None


# 便捷函数
async def generate_text(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> str:
    """
    生成文本的便捷函数
    
    Args:
        prompt: 提示词
        max_tokens: 最大token数
        temperature: 温度参数
        **kwargs: 其他参数
    
    Returns:
        str: 生成的文本
    """
    client = LLMClientFactory.get_client()
    return await client.generate(prompt, max_tokens, temperature, **kwargs)
