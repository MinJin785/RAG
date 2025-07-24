import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

import google.genai as genai
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

@dataclass
class APIUsage:
    timestamp: datetime
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float

class APIManager:
    def __init__(self):
        self.claude_client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.google_backup_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY_BACKUP"))
        
        self.usage_log: List[APIUsage] = []
        self.current_google_client = self.google_client
        
        # 비용 계산용 토큰 가격 (USD per 1M tokens)
        self.pricing = {
            "claude-sonnet-4": {"input": 15.0, "output": 75.0},
            "gemini-2.5-pro": {"input": 1.25, "output": 5.0}
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def call_claude(self, messages: List[Dict], model: str = "claude-sonnet-4-20250514", 
                         max_tokens: int = 4000, temperature: float = 0.7) -> Dict[str, Any]:
        try:
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            
            # 사용량 기록
            usage = APIUsage(
                timestamp=datetime.now(),
                model=model,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cost_usd=self._calculate_cost("claude-sonnet-4", response.usage.input_tokens, response.usage.output_tokens)
            )
            self.usage_log.append(usage)
            
            return {
                "success": True,
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "cost_usd": usage.cost_usd
            }
            
        except Exception as e:
            self.logger.error(f"Claude API 오류: {e}")
            return {"success": False, "error": str(e)}

    async def call_gemini(self, messages: List[Dict], model: str = "gemini-2.5-pro", 
                         max_tokens: int = 4000, temperature: float = 0.7) -> Dict[str, Any]:
        try:
            # 메시지 포맷 변환 (Claude → Gemini)
            gemini_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
                elif msg["role"] == "assistant":
                    gemini_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})
            
            response = await asyncio.to_thread(
                self.current_google_client.models.generate_content,
                model=model,
                contents=gemini_messages,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            # 토큰 수 추정 (Gemini는 정확한 토큰 수를 제공하지 않음)
            input_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)
            output_tokens = len(response.text.split()) * 1.3
            
            usage = APIUsage(
                timestamp=datetime.now(),
                model=model,
                tokens_in=int(input_tokens),
                tokens_out=int(output_tokens),
                cost_usd=self._calculate_cost("gemini-2.5-pro", int(input_tokens), int(output_tokens))
            )
            self.usage_log.append(usage)
            
            return {
                "success": True,
                "content": response.text,
                "usage": {
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": int(input_tokens + output_tokens)
                },
                "cost_usd": usage.cost_usd
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API 오류 (메인): {e}")
            # 백업 클라이언트로 재시도
            try:
                self.current_google_client = self.google_backup_client
                return await self.call_gemini(messages, model, max_tokens, temperature)
            except Exception as backup_error:
                self.logger.error(f"Gemini API 오류 (백업): {backup_error}")
                return {"success": False, "error": str(backup_error)}

    def _calculate_cost(self, model_family: str, input_tokens: int, output_tokens: int) -> float:
        if model_family in self.pricing:
            input_cost = (input_tokens / 1_000_000) * self.pricing[model_family]["input"]
            output_cost = (output_tokens / 1_000_000) * self.pricing[model_family]["output"]
            return input_cost + output_cost
        return 0.0

    def get_daily_usage(self) -> Dict[str, Any]:
        today = datetime.now().date()
        today_usage = [u for u in self.usage_log if u.timestamp.date() == today]
        
        total_cost = sum(u.cost_usd for u in today_usage)
        total_requests = len(today_usage)
        
        by_model = {}
        for usage in today_usage:
            if usage.model not in by_model:
                by_model[usage.model] = {"requests": 0, "cost": 0.0, "tokens": 0}
            by_model[usage.model]["requests"] += 1
            by_model[usage.model]["cost"] += usage.cost_usd
            by_model[usage.model]["tokens"] += usage.tokens_in + usage.tokens_out
        
        return {
            "date": today.isoformat(),
            "total_cost_usd": round(total_cost, 4),
            "total_requests": total_requests,
            "by_model": by_model
        }

    async def smart_call(self, messages: List[Dict], task_type: str = "general", 
                        max_tokens: int = 4000, temperature: float = 0.7) -> Dict[str, Any]:
        """
        작업 유형에 따라 최적의 모델 선택
        - creative: Claude (창의적 작업)
        - analysis: Gemini (분석 작업)
        - code: Claude (코딩 작업)
        - search: Gemini (검색 관련)
        - general: Claude (기본)
        """
        if task_type in ["creative", "code", "general"]:
            return await self.call_claude(messages, max_tokens=max_tokens, temperature=temperature)
        else:
            return await self.call_gemini(messages, max_tokens=max_tokens, temperature=temperature)