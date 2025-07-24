import os
import sqlite3
import pickle
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: np.ndarray
    timestamp: datetime
    importance: float = 0.5

class MemoryBrain:
    def __init__(self, db_path: str = "data/memory_db/memory.db", max_size_gb: float = None):
        """초기화 - 용량 제한 지원"""
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.max_size_gb = max_size_gb  # None = 무제한 (AI민진용)
        self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.dimension = 384
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 데이터베이스 연결
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # 스키마 업데이트 (기존 DB 호환성)
        self._migrate_database_schema()
        
        # 테이블 생성
        self._create_tables()
        
        # FAISS 인덱스 초기화
        self.index = faiss.IndexFlatIP(self.dimension)
        self.embedding_ids = []
        
        # 기존 메모리 로드
        asyncio.create_task(self._load_existing_memories())
        
        # 스마트 메모리 관리 설정
        self.importance_threshold = 0.3  # 중요도 임계값
        self.contradiction_threshold = 0.85  # 상충 감지 임계값

    def _migrate_database_schema(self):
        """기존 데이터베이스 스키마 업데이트"""
        try:
            cursor = self.conn.cursor()
            
            # 기존 테이블 구조 확인
            cursor.execute("PRAGMA table_info(memories)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # access_count 컬럼이 없으면 추가
            if 'access_count' not in columns:
                cursor.execute('ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0')
                self.logger.info("access_count 컬럼 추가됨")
            
            # last_accessed 컬럼이 없으면 추가
            if 'last_accessed' not in columns:
                cursor.execute('ALTER TABLE memories ADD COLUMN last_accessed TEXT')
                self.logger.info("last_accessed 컬럼 추가됨")
            
            # 인덱스 생성 (이미 있으면 무시됨)
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)')
            except:
                pass  # 인덱스가 이미 있는 경우
            
            self.conn.commit()
            self.logger.info("데이터베이스 스키마 마이그레이션 완료")
            
        except Exception as e:
            self.logger.error(f"데이터베이스 마이그레이션 오류: {e}")

    def _create_tables(self):
        """테이블 생성"""
        cursor = self.conn.cursor()
        
        # memories 테이블 (기본 구조만, 새 컬럼은 마이그레이션에서 처리)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                embedding_id INTEGER,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT,
                importance REAL DEFAULT 0.5
            )
        ''')
        
        # conversations 테이블 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT
            )
        ''')
        
        self.conn.commit()

    def _load_existing_data(self):
        """기존 데이터 로드"""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
            
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    self.memory_metadata = pickle.load(f)
                    
            self.logger.info(f"기존 메모리 로드 완료: {self.index.ntotal}개 항목")
            
        except Exception as e:
            self.logger.error(f"기존 데이터 로드 오류: {e}")

    async def add_memory(self, content: str, metadata: Dict[str, Any], importance: float = None) -> bool:
        """메모리 추가 - 스마트 중요도 계산 및 상충 검사"""
        try:
            # 자동 중요도 계산 (수동 설정이 없는 경우)
            if importance is None:
                importance = await self.calculate_importance_score(content, metadata)
            
            # 상충되는 메모리 검사 및 정리
            contradictory_memories = await self.detect_contradictory_memories(content, metadata)
            if contradictory_memories:
                self.logger.info(f"상충 메모리 {len(contradictory_memories)}개 발견, 정리 중...")
                
                cursor = self.conn.cursor()
                for contra in contradictory_memories:
                    # 새 메모리가 더 중요한 경우에만 기존 메모리 삭제
                    if importance > contra["importance"] + 0.1:  # 0.1 마진
                        cursor.execute('DELETE FROM memories WHERE id = ?', (contra["memory_id"],))
                        self.logger.info(f"상충 메모리 삭제: {contra['content'][:50]}...")
                
                self.conn.commit()
            
            # 임베딩 생성
            embedding = self.embedding_model.encode([content])
            
            # 데이터베이스에 저장
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO memories 
                (content, metadata, timestamp, importance, embedding_id, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                content,
                json.dumps(metadata, ensure_ascii=False),
                datetime.now().isoformat(),
                importance,
                len(self.embedding_ids),  # 새로운 embedding_id
                0,  # 초기 접근 횟수
                datetime.now().isoformat()  # 생성 시간을 마지막 접근으로
            ))
            
            # FAISS 인덱스에 추가
            self.index.add(embedding.astype(np.float32))
            self.embedding_ids.append(cursor.lastrowid)
            
            self.conn.commit()
            
            # 용량 체크 및 자동 정리
            if self.max_size_gb:
                current_size = self._get_database_size_gb()
                if current_size > self.max_size_gb * 0.95:  # 95% 초과시 정리
                    cleanup_result = await self.auto_cleanup_low_importance_memories(force_cleanup=True)
                    if cleanup_result["cleaned"] > 0:
                        self.logger.info(f"용량 초과로 인한 자동 정리: {cleanup_result['cleaned']}개 메모리 삭제")
            
            return True
            
        except Exception as e:
            self.logger.error(f"메모리 추가 오류: {e}")
            return False

    async def search_memories(self, query: str, top_k: int = 10, 
                            min_score: float = 0.3) -> List[Dict[str, Any]]:
        """유사도 기반 메모리 검색"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # 쿼리 임베딩
            query_embedding = await asyncio.to_thread(
                self.embedding_model.encode, 
                query, 
                convert_to_numpy=True
            )
            query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
            
            # FAISS 검색
            scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            results = []
            cursor = self.conn.cursor()
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score < min_score:
                    continue
                
                if idx < len(self.memory_metadata):
                    meta = self.memory_metadata[idx].copy()
                    meta["similarity_score"] = float(score)
                    meta["rank"] = i + 1
                    
                    # 접근 횟수 업데이트
                    cursor.execute('''
                        UPDATE memories 
                        SET access_count = access_count + 1, last_accessed = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), meta["id"]))
                    
                    results.append(meta)
            
            self.conn.commit()
            
            # 중요도와 유사도를 결합한 점수로 재정렬
            results.sort(key=lambda x: x["similarity_score"] * x["importance"], reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"메모리 검색 오류: {e}")
            return []

    async def get_context_for_query(self, query: str, max_context: int = 5000) -> str:
        """쿼리에 대한 관련 컨텍스트 생성"""
        memories = await self.search_memories(query, top_k=8)
        
        context_parts = []
        total_length = 0
        
        for memory in memories:
            content = memory["content"]
            if total_length + len(content) > max_context:
                break
            
            context_parts.append(f"[기억 {memory['rank']}] {content}")
            total_length += len(content)
        
        return "\n\n".join(context_parts)

    async def save_conversation(self, user_message: str, ai_response: str, 
                              context_used: str = "") -> str:
        """대화 저장"""
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (id, user_message, ai_response, timestamp, context_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (conv_id, user_message, ai_response, datetime.now().isoformat(), context_used))
        self.conn.commit()
        
        # 중요한 대화는 메모리로도 저장
        if len(user_message) > 50 or "중요" in user_message:
            await self.add_memory(
                f"사용자 질문: {user_message}\nAI 답변: {ai_response[:500]}",
                {"type": "conversation", "conv_id": conv_id},
                importance=0.7
            )
        
        return conv_id

    async def cleanup_old_memories(self, days_old: int = 30, min_importance: float = 0.3):
        """오래된 중요하지 않은 메모리 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cursor = self.conn.cursor()
            
            # 정리할 메모리 ID 찾기
            cursor.execute('''
                SELECT id, embedding_id FROM memories 
                WHERE timestamp < ? AND importance < ? AND access_count < 2
            ''', (cutoff_date.isoformat(), min_importance))
            
            to_delete = cursor.fetchall()
            
            if to_delete:
                # SQLite에서 삭제
                for memory_id, embedding_id in to_delete:
                    cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                
                self.conn.commit()
                self.logger.info(f"{len(to_delete)}개의 오래된 메모리 정리 완료")
                
                # FAISS 인덱스 재구성
                await self._rebuild_faiss_index()
            
        except Exception as e:
            self.logger.error(f"메모리 정리 오류: {e}")

    async def _rebuild_faiss_index(self):
        """FAISS 인덱스 재구성"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, content FROM memories ORDER BY timestamp')
            memories = cursor.fetchall()
            
            # 새 인덱스 생성
            new_index = faiss.IndexFlatIP(self.dimension)
            new_metadata = []
            
            for i, (memory_id, content) in enumerate(memories):
                # 임베딩 재생성
                embedding = await asyncio.to_thread(
                    self.embedding_model.encode, 
                    content, 
                    convert_to_numpy=True
                )
                embedding = embedding.astype(np.float32)
                new_index.add(embedding.reshape(1, -1))
                
                # 메타데이터 업데이트
                cursor.execute('''
                    SELECT metadata, timestamp, importance FROM memories WHERE id = ?
                ''', (memory_id,))
                result = cursor.fetchone()
                
                if result:
                    metadata, timestamp, importance = result
                    new_metadata.append({
                        "id": memory_id,
                        "content": content,
                        "metadata": json.loads(metadata),
                        "timestamp": timestamp,
                        "importance": importance,
                        "embedding_id": i
                    })
                
                # embedding_id 업데이트
                cursor.execute('''
                    UPDATE memories SET embedding_id = ? WHERE id = ?
                ''', (i, memory_id))
            
            self.conn.commit()
            
            # 인덱스 교체
            self.index = new_index
            self.memory_metadata = new_metadata
            
            await self._save_data()
            self.logger.info("FAISS 인덱스 재구성 완료")
            
        except Exception as e:
            self.logger.error(f"FAISS 인덱스 재구성 오류: {e}")

    async def _save_data(self):
        """FAISS 인덱스와 메타데이터 저장"""
        try:
            os.makedirs(self.data_path, exist_ok=True)
            
            faiss.write_index(self.index, self.index_path)
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.memory_metadata, f)
                
        except Exception as e:
            self.logger.error(f"데이터 저장 오류: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(importance) FROM memories")
        avg_importance = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM memories WHERE importance > 0.7")
        high_importance = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(access_count) FROM memories")
        avg_access = cursor.fetchone()[0] or 0
        
        # 메모리 DB 크기
        db_size = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
        
        return {
            "total_memories": total_memories,
            "total_conversations": total_conversations,
            "high_importance_memories": high_importance,
            "faiss_vectors": self.index.ntotal,
            "average_importance": round(avg_importance, 3),
            "average_access_count": round(avg_access, 2),
            "memory_db_size_mb": round(db_size, 2),
            "embedding_dimension": self.dimension
        }

    async def optimize_memory_system(self):
        """메모리 시스템 최적화"""
        try:
            # 1. 오래된 메모리 정리
            await self.cleanup_old_memories(days_old=30, min_importance=0.3)
            
            # 2. 통계 업데이트
            stats = await self.get_memory_stats()
            
            # 3. 인덱스 최적화 (500MB 이상일 때)
            if stats["memory_db_size_mb"] > 500:
                await self._rebuild_faiss_index()
            
            self.logger.info("메모리 시스템 최적화 완료")
            return stats
            
        except Exception as e:
            self.logger.error(f"메모리 시스템 최적화 오류: {e}")
            return {}

    async def get_historical_context(self, query: str = "", days_back: int = 365, max_memories: int = 50) -> str:
        """1년치 대화 기록에서 관련 컨텍스트 추출"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            cursor = self.conn.cursor()
            
            if query:
                # 쿼리가 있으면 유사도 기반 검색
                memories = await self.search_memories(query, top_k=max_memories, min_score=0.2)
                # 날짜 필터링 추가
                filtered_memories = [
                    m for m in memories 
                    if datetime.fromisoformat(m.get("timestamp", "1900-01-01")) >= cutoff_date
                ]
            else:
                # 쿼리가 없으면 최근 중요한 대화들
                cursor.execute('''
                    SELECT content, metadata, timestamp, importance FROM memories 
                    WHERE timestamp >= ? AND (importance > 0.6 OR JSON_EXTRACT(metadata, '$.type') = 'conversation')
                    ORDER BY importance DESC, timestamp DESC 
                    LIMIT ?
                ''', (cutoff_date.isoformat(), max_memories))
                
                results = cursor.fetchall()
                filtered_memories = [
                    {
                        "content": row[0],
                        "metadata": json.loads(row[1]),
                        "timestamp": row[2],
                        "importance": row[3]
                    }
                    for row in results
                ]
            
            # 시간순으로 정렬하여 맥락 생성
            sorted_memories = sorted(filtered_memories, key=lambda x: x.get("timestamp", ""))
            
            context_parts = []
            total_length = 0
            max_context = 10000  # 10KB 제한
            
            for memory in sorted_memories:
                content = memory["content"]
                timestamp = memory.get("timestamp", "")
                importance = memory.get("importance", 0.5)
                
                # 날짜 포맷팅
                try:
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    date_str = "날짜불명"
                
                formatted_content = f"[{date_str} | 중요도:{importance:.1f}] {content}"
                
                if total_length + len(formatted_content) > max_context:
                    break
                
                context_parts.append(formatted_content)
                total_length += len(formatted_content)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"1년치 컨텍스트 로드 오류: {e}")
            return ""

    async def get_conversation_timeline(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """최근 N일간의 대화 타임라인 생성"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_message, ai_response, timestamp FROM conversations 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''', (cutoff_date.isoformat(),))
            
            conversations = []
            for row in cursor.fetchall():
                user_msg, ai_resp, timestamp = row
                try:
                    dt = datetime.fromisoformat(timestamp)
                    conversations.append({
                        "user_message": user_msg,
                        "ai_response": ai_resp,
                        "timestamp": timestamp,
                        "formatted_date": dt.strftime("%m-%d %H:%M"),
                        "days_ago": (datetime.now() - dt).days
                    })
                except:
                    continue
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"대화 타임라인 생성 오류: {e}")
            return []

    async def smart_context_restore(self, user_query: str = "") -> Dict[str, Any]:
        """스마트 컨텍스트 복원 (1년치 대화 지원)"""
        try:
            # 1. 최근 30일 대화 타임라인
            recent_timeline = await self.get_conversation_timeline(days_back=30)
            
            # 2. 쿼리 관련 1년치 기억
            if user_query:
                relevant_context = await self.get_historical_context(user_query, days_back=365, max_memories=20)
            else:
                relevant_context = await self.get_historical_context(days_back=365, max_memories=10)
            
            # 3. 통계 정보
            stats = await self.get_memory_stats()
            
            return {
                "recent_conversations": recent_timeline[:10],  # 최근 10개
                "historical_context": relevant_context,
                "total_conversations": stats.get("total_conversations", 0),
                "total_memories": stats.get("total_memories", 0),
                "oldest_memory_days": await self._get_oldest_memory_age(),
                "context_summary": f"총 {stats.get('total_conversations', 0)}개 대화, {stats.get('total_memories', 0)}개 기억 보유"
            }
            
        except Exception as e:
            self.logger.error(f"스마트 컨텍스트 복원 오류: {e}")
            return {"recent_conversations": [], "historical_context": "", "context_summary": "컨텍스트 로드 실패"}

    async def _get_oldest_memory_age(self) -> int:
        """가장 오래된 기억의 나이(일) 계산"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT MIN(timestamp) FROM memories")
            result = cursor.fetchone()
            
            if result and result[0]:
                oldest_date = datetime.fromisoformat(result[0])
                return (datetime.now() - oldest_date).days
            return 0
            
        except:
            return 0

    async def detect_contradictory_memories(self, new_content: str, new_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """새로운 메모리와 상충되는 기존 메모리 감지"""
        try:
            # 새 내용의 임베딩 생성
            new_embedding = self.embedding_model.encode([new_content])
            
            # 유사한 메모리 검색 (높은 유사도)
            similar_memories = await self.search_memories(new_content, top_k=20, min_score=0.7)
            
            contradictory = []
            
            for memory in similar_memories:
                # 시간 차이 확인 (3개월 이상 된 메모리만 검사)
                try:
                    memory_time = datetime.fromisoformat(memory.get("timestamp", ""))
                    time_diff = (datetime.now() - memory_time).days
                    
                    if time_diff < 90:  # 3개월 미만은 건드리지 않음
                        continue
                        
                    # 의미론적 유사도는 높지만 내용이 반대인 경우 감지
                    if self._is_contradictory_content(new_content, memory["content"]):
                        contradictory.append({
                            "memory_id": memory.get("id"),
                            "content": memory["content"],
                            "similarity": memory.get("similarity", 0),
                            "age_days": time_diff,
                            "importance": memory.get("importance", 0.5)
                        })
                        
                except Exception as e:
                    continue
            
            return contradictory
            
        except Exception as e:
            self.logger.error(f"상충 메모리 감지 오류: {e}")
            return []

    def _is_contradictory_content(self, new_content: str, old_content: str) -> bool:
        """두 내용이 상충되는지 판단 (간단한 휴리스틱)"""
        # 반대 의미 키워드 쌍들
        contradiction_pairs = [
            ("좋다", "나쁘다"), ("선호", "비선호"), ("사용", "사용안함"),
            ("필요", "불필요"), ("중요", "중요하지않"), ("해야", "하지말아야"),
            ("계획", "취소"), ("진행", "중단"), ("추가", "제거"),
            ("구현", "삭제"), ("활성화", "비활성화"), ("켜기", "끄기")
        ]
        
        new_lower = new_content.lower()
        old_lower = old_content.lower()
        
        for positive, negative in contradiction_pairs:
            if positive in new_lower and negative in old_lower:
                return True
            if negative in new_lower and positive in old_lower:
                return True
                
        return False

    async def calculate_importance_score(self, content: str, metadata: Dict[str, Any]) -> float:
        """내용의 중요도 점수 자동 계산"""
        try:
            importance = 0.5  # 기본 점수
            
            # 1. 키워드 기반 중요도
            high_importance_keywords = [
                "중요", "필수", "핵심", "주요", "필요", "계획", "목표", 
                "프로젝트", "시스템", "구현", "개발", "설정", "설치"
            ]
            
            low_importance_keywords = [
                "그냥", "별로", "안중요", "무관", "취소", "삭제", "임시"
            ]
            
            content_lower = content.lower()
            
            for keyword in high_importance_keywords:
                if keyword in content_lower:
                    importance += 0.1
                    
            for keyword in low_importance_keywords:
                if keyword in content_lower:
                    importance -= 0.1
            
            # 2. 메타데이터 기반 중요도
            if metadata.get("type") == "core_system":
                importance += 0.3
            elif metadata.get("type") == "task_related":
                importance += 0.2
            elif metadata.get("type") == "conversation":
                importance += 0.1
                
            # 3. 내용 길이 기반 (상세할수록 중요)
            if len(content) > 200:
                importance += 0.1
            elif len(content) < 50:
                importance -= 0.1
            
            # 4. 질문이나 명령어가 포함된 경우
            if any(marker in content_lower for marker in ["?", "어떻게", "왜", "해줘", "만들어"]):
                importance += 0.1
            
            # 5. 범위 제한
            return max(0.0, min(1.0, importance))
            
        except Exception as e:
            self.logger.error(f"중요도 계산 오류: {e}")
            return 0.5

    async def auto_cleanup_low_importance_memories(self, force_cleanup: bool = False) -> Dict[str, Any]:
        """낮은 중요도 메모리 자동 정리"""
        try:
            # 용량 체크
            if self.max_size_gb and not force_cleanup:
                current_size = self._get_database_size_gb()
                if current_size < self.max_size_gb * 0.8:  # 80% 미만이면 정리 안함
                    return {"cleaned": 0, "reason": "capacity_ok"}
            
            cursor = self.conn.cursor()
            
            # 정리 대상 조건
            cutoff_date = datetime.now() - timedelta(days=180)  # 6개월 이상
            
            # 낮은 중요도 + 낮은 접근 횟수 + 오래된 메모리
            cursor.execute('''
                SELECT id, content, importance, access_count, timestamp 
                FROM memories 
                WHERE importance < ? 
                AND access_count < 3 
                AND timestamp < ?
                AND JSON_EXTRACT(metadata, '$.type') NOT IN ('core_system', 'system_improvement')
                ORDER BY importance ASC, access_count ASC
                LIMIT 100
            ''', (self.importance_threshold, cutoff_date.isoformat()))
            
            to_delete = cursor.fetchall()
            
            if not to_delete:
                return {"cleaned": 0, "reason": "nothing_to_clean"}
            
            # 삭제 실행
            deleted_count = 0
            for memory in to_delete:
                memory_id = memory[0]
                
                # SQLite에서 삭제
                cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                deleted_count += 1
            
            self.conn.commit()
            
            # FAISS 인덱스 재구성
            await self._rebuild_faiss_index()
            
            self.logger.info(f"낮은 중요도 메모리 {deleted_count}개 정리 완료")
            
            return {
                "cleaned": deleted_count,
                "reason": "auto_cleanup",
                "criteria": f"importance < {self.importance_threshold}, access < 3, age > 180days"
            }
            
        except Exception as e:
            self.logger.error(f"자동 메모리 정리 오류: {e}")
            return {"cleaned": 0, "reason": f"error: {e}"}

    def _get_database_size_gb(self) -> float:
        """데이터베이스 크기 (GB) 반환"""
        try:
            size_bytes = os.path.getsize(self.db_path)
            return size_bytes / (1024 ** 3)
        except:
            return 0.0

    async def smart_memory_maintenance(self) -> Dict[str, Any]:
        """스마트 메모리 유지보수 실행"""
        try:
            maintenance_report = {
                "start_time": datetime.now().isoformat(),
                "actions": [],
                "stats_before": await self.get_memory_stats(),
                "stats_after": None
            }
            
            # 1. 용량 기반 정리
            if self.max_size_gb:
                current_size = self._get_database_size_gb()
                if current_size > self.max_size_gb * 0.9:  # 90% 초과시
                    cleanup_result = await self.auto_cleanup_low_importance_memories(force_cleanup=True)
                    maintenance_report["actions"].append({
                        "action": "capacity_cleanup",
                        "result": cleanup_result
                    })
            
            # 2. 상충 메모리 정리 (월 1회)
            last_contradiction_check = getattr(self, '_last_contradiction_check', None)
            if (not last_contradiction_check or 
                (datetime.now() - last_contradiction_check).days >= 30):
                
                contradiction_result = await self._cleanup_contradictions()
                maintenance_report["actions"].append({
                    "action": "contradiction_cleanup", 
                    "result": contradiction_result
                })
                self._last_contradiction_check = datetime.now()
            
            # 3. 인덱스 최적화
            await self._rebuild_faiss_index()
            maintenance_report["actions"].append({
                "action": "index_optimization",
                "result": "completed"
            })
            
            # 최종 통계
            maintenance_report["stats_after"] = await self.get_memory_stats()
            maintenance_report["end_time"] = datetime.now().isoformat()
            
            return maintenance_report
            
        except Exception as e:
            self.logger.error(f"스마트 메모리 유지보수 오류: {e}")
            return {"error": str(e)}

    async def _cleanup_contradictions(self) -> Dict[str, Any]:
        """상충되는 메모리들 정리"""
        try:
            cursor = self.conn.cursor()
            
            # 최근 6개월 메모리들을 기준으로 상충 검사
            recent_cutoff = datetime.now() - timedelta(days=180)
            cursor.execute('''
                SELECT id, content, metadata, timestamp, importance 
                FROM memories 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (recent_cutoff.isoformat(),))
            
            recent_memories = cursor.fetchall()
            contradictions_found = 0
            
            for memory in recent_memories:
                memory_content = memory[1]
                
                # 이 메모리와 상충되는 오래된 메모리 찾기
                contradictory = await self.detect_contradictory_memories(
                    memory_content, 
                    json.loads(memory[2])
                )
                
                # 상충되는 메모리들 중 중요도가 낮은 것들 삭제
                for contra in contradictory:
                    if contra["importance"] < memory[4]:  # 새 메모리가 더 중요하면
                        cursor.execute('DELETE FROM memories WHERE id = ?', (contra["memory_id"],))
                        contradictions_found += 1
            
            self.conn.commit()
            
            return {
                "contradictions_resolved": contradictions_found,
                "status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"상충 정리 오류: {e}")
            return {"contradictions_resolved": 0, "error": str(e)}

    def __del__(self):
        """소멸자"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass

    async def initialize_desktop_mega_memory_system(self):
        """데스크탑 192GB RAM + 8TB 저장소 활용 메가 메모리 시스템 초기화"""
        try:
            # 데스크탑 하드웨어 스펙 최적화 설정
            desktop_memory_config = {
                "hardware_specs": {
                    "total_ram": "192GB DDR5",
                    "usable_ram_for_memory": "150GB",  # 시스템용 42GB 예약
                    "ssd_storage": "Samsung SSD 9100 PRO 4TB",
                    "hdd_storage": "4TB HDD x 2 = 8TB",
                    "total_storage": "12TB",
                    "gpu_memory": "AMD RX 6600 8GB"
                },
                "memory_optimization": {
                    "ram_cache_size": "100GB",        # 100GB RAM 캐시
                    "ssd_cache_size": "2TB",          # 2TB SSD 캐시  
                    "hdd_archive_size": "6TB",        # 6TB HDD 아카이브
                    "gpu_acceleration": True,         # GPU 가속 활용
                    "parallel_processing": 8,         # 8코어 병렬 처리
                    "compression_ratio": 0.3          # 70% 압축률
                }
            }
            
            # 메가 메모리 아키텍처 설계
            mega_memory_architecture = {
                "tier1_hot_memory": {
                    "storage": "RAM",
                    "capacity": "50GB",
                    "purpose": "최근 1개월 대화 + 핵심 기억",
                    "access_speed": "나노초",
                    "retention": "실시간"
                },
                "tier2_warm_memory": {
                    "storage": "SSD_Cache", 
                    "capacity": "1TB",
                    "purpose": "최근 1년 대화 + 중요 기억",
                    "access_speed": "마이크로초",
                    "retention": "빠른 액세스"
                },
                "tier3_cold_memory": {
                    "storage": "SSD_Archive",
                    "capacity": "3TB", 
                    "purpose": "전체 기간 압축 저장",
                    "access_speed": "밀리초",
                    "retention": "장기 보관"
                },
                "tier4_deep_archive": {
                    "storage": "HDD_Archive",
                    "capacity": "6TB",
                    "purpose": "완전 백업 + 히스토리",
                    "access_speed": "초단위",
                    "retention": "영구 보존"
                }
            }
            
            # 설정 파일 저장
            config_file = self.project_root / "desktop_mega_memory_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "desktop_memory_config": desktop_memory_config,
                    "mega_memory_architecture": mega_memory_architecture,
                    "version": "2.0_desktop_mega",
                    "created": datetime.now().isoformat(),
                    "capabilities": [
                        "192GB RAM 활용",
                        "12TB 저장소 최적화",
                        "4단계 메모리 계층",
                        "지능형 데이터 이동",
                        "무제한 기억 용량",
                        "실시간 압축/해제",
                        "GPU 가속 검색",
                        "병렬 처리 최적화"
                    ]
                }, f, ensure_ascii=False, indent=2)
            
            # 메가 메모리 시스템 초기화
            await self._initialize_tiered_memory_system(mega_memory_architecture)
            
            self.logger.info("데스크탑 메가 메모리 시스템 (192GB + 12TB) 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"메가 메모리 시스템 초기화 오류: {e}")
            return False

    async def _initialize_tiered_memory_system(self, architecture: Dict[str, Any]):
        """4단계 계층형 메모리 시스템 초기화"""
        try:
            # 1단계: HOT Memory (RAM) - 50GB
            self.hot_memory = {
                "data": {},
                "capacity_gb": 50,
                "current_usage_gb": 0,
                "access_count": 0,
                "hit_rate": 0.0
            }
            
            # 2단계: WARM Memory (SSD Cache) - 1TB 
            self.warm_memory = {
                "cache_path": self.project_root / "data" / "ssd_cache",
                "capacity_gb": 1024,
                "current_usage_gb": 0,
                "access_count": 0,
                "hit_rate": 0.0
            }
            
            # 3단계: COLD Memory (SSD Archive) - 3TB
            self.cold_memory = {
                "archive_path": self.project_root / "data" / "ssd_archive", 
                "capacity_gb": 3072,
                "current_usage_gb": 0,
                "compression_enabled": True,
                "compression_ratio": 0.3
            }
            
            # 4단계: DEEP Archive (HDD) - 6TB
            self.deep_archive = {
                "archive_path": self.project_root / "data" / "hdd_archive",
                "capacity_gb": 6144,
                "current_usage_gb": 0,
                "full_backup": True,
                "retention_policy": "infinite"
            }
            
            # 디렉토리 생성
            for memory_tier in [self.warm_memory, self.cold_memory, self.deep_archive]:
                if "path" in str(memory_tier):
                    path = memory_tier.get("cache_path") or memory_tier.get("archive_path")
                    if path:
                        os.makedirs(path, exist_ok=True)
            
            self.logger.info("4단계 계층형 메모리 시스템 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"계층형 메모리 초기화 오류: {e}")

    async def mega_add_memory(self, content: str, metadata: Dict[str, Any], importance: float = None) -> bool:
        """메가 메모리 시스템에 기억 추가 (192GB RAM + 12TB 최적화)"""
        try:
            # 자동 중요도 계산
            if importance is None:
                importance = await self.calculate_importance_score(content, metadata)
            
            # 메모리 객체 생성
            memory_obj = {
                "id": f"mega_mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                "content": content,
                "metadata": metadata,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "access_count": 0,
                "last_accessed": datetime.now().isoformat(),
                "storage_tier": "pending"
            }
            
            # 스마트 티어 할당 (중요도와 크기 기반)
            assigned_tier = await self._assign_memory_tier(memory_obj)
            memory_obj["storage_tier"] = assigned_tier
            
            # 할당된 티어에 저장
            success = await self._store_in_tier(memory_obj, assigned_tier)
            
            if success:
                # 기본 SQLite에도 메타데이터 저장 (호환성)
                await self.add_memory(content, metadata, importance)
                
                # 메모리 사용량 모니터링 및 자동 정리
                await self._monitor_and_optimize_memory_usage()
                
                self.logger.info(f"메가 메모리 저장 완료: {assigned_tier} 티어")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"메가 메모리 추가 오류: {e}")
            return False

    async def _assign_memory_tier(self, memory_obj: Dict[str, Any]) -> str:
        """스마트 메모리 티어 할당 (중요도, 크기, 접근 패턴 기반)"""
        importance = memory_obj["importance"]
        content_size = len(memory_obj["content"])
        memory_type = memory_obj["metadata"].get("type", "general")
        
        # HOT Memory (RAM) - 고중요도 + 최근 + 자주 접근
        if (importance > 0.8 and content_size < 50000 and 
            memory_type in ["core_system", "recent_conversation", "urgent_task"]):
            return "hot_memory"
        
        # WARM Memory (SSD Cache) - 중요도 + 최근 1년
        elif (importance > 0.5 and content_size < 500000 and
              memory_type in ["conversation", "task_related", "important_info"]):
            return "warm_memory"
        
        # COLD Memory (SSD Archive) - 압축 저장 가능
        elif importance > 0.3 and content_size < 2000000:
            return "cold_memory"
        
        # DEEP Archive (HDD) - 모든 기억 영구 보관
        else:
            return "deep_archive"

    async def _store_in_tier(self, memory_obj: Dict[str, Any], tier: str) -> bool:
        """지정된 티어에 메모리 저장"""
        try:
            if tier == "hot_memory":
                return await self._store_hot_memory(memory_obj)
            elif tier == "warm_memory":
                return await self._store_warm_memory(memory_obj)
            elif tier == "cold_memory":
                return await self._store_cold_memory(memory_obj)
            elif tier == "deep_archive":
                return await self._store_deep_archive(memory_obj)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"티어 저장 오류 ({tier}): {e}")
            return False

    async def _store_hot_memory(self, memory_obj: Dict[str, Any]) -> bool:
        """HOT Memory (RAM) 저장 - 50GB 활용"""
        try:
            memory_id = memory_obj["id"]
            
            # 용량 체크
            estimated_size_mb = len(json.dumps(memory_obj, ensure_ascii=False)) / (1024 * 1024)
            
            if self.hot_memory["current_usage_gb"] + estimated_size_mb/1024 > self.hot_memory["capacity_gb"]:
                # 용량 초과시 LRU 방식으로 정리
                await self._cleanup_hot_memory()
            
            # RAM에 직접 저장
            self.hot_memory["data"][memory_id] = memory_obj
            self.hot_memory["current_usage_gb"] += estimated_size_mb/1024
            self.hot_memory["access_count"] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"HOT 메모리 저장 오류: {e}")
            return False

    async def _store_warm_memory(self, memory_obj: Dict[str, Any]) -> bool:
        """WARM Memory (SSD Cache) 저장 - 1TB 활용"""
        try:
            memory_id = memory_obj["id"]
            cache_file = self.warm_memory["cache_path"] / f"{memory_id}.json"
            
            # SSD에 JSON 파일로 저장
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(memory_obj, f, ensure_ascii=False, indent=2)
            
            # 사용량 업데이트
            file_size_mb = cache_file.stat().st_size / (1024 * 1024)
            self.warm_memory["current_usage_gb"] += file_size_mb/1024
            
            return True
            
        except Exception as e:
            self.logger.error(f"WARM 메모리 저장 오류: {e}")
            return False

    async def _store_cold_memory(self, memory_obj: Dict[str, Any]) -> bool:
        """COLD Memory (SSD Archive) 저장 - 3TB + 압축"""
        try:
            import gzip
            
            memory_id = memory_obj["id"]
            archive_file = self.cold_memory["archive_path"] / f"{memory_id}.json.gz"
            
            # 압축하여 저장
            json_data = json.dumps(memory_obj, ensure_ascii=False).encode('utf-8')
            with gzip.open(archive_file, 'wb') as f:
                f.write(json_data)
            
            # 압축률 계산 및 사용량 업데이트
            compressed_size_mb = archive_file.stat().st_size / (1024 * 1024)
            self.cold_memory["current_usage_gb"] += compressed_size_mb/1024
            
            return True
            
        except Exception as e:
            self.logger.error(f"COLD 메모리 저장 오류: {e}")
            return False

    async def _store_deep_archive(self, memory_obj: Dict[str, Any]) -> bool:
        """DEEP Archive (HDD) 저장 - 6TB 영구 보관"""
        try:
            import gzip
            
            memory_id = memory_obj["id"]
            archive_file = self.deep_archive["archive_path"] / f"{memory_id}.archive.gz"
            
            # 최대 압축으로 저장
            json_data = json.dumps(memory_obj, ensure_ascii=False).encode('utf-8')
            with gzip.open(archive_file, 'wb', compresslevel=9) as f:
                f.write(json_data)
            
            # 사용량 업데이트
            compressed_size_mb = archive_file.stat().st_size / (1024 * 1024)
            self.deep_archive["current_usage_gb"] += compressed_size_mb/1024
            
            return True
            
        except Exception as e:
            self.logger.error(f"DEEP 아카이브 저장 오류: {e}")
            return False

    async def mega_search_memories(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """메가 메모리 시스템에서 검색 (4단계 티어 통합 검색)"""
        try:
            all_results = []
            
            # 1단계: HOT Memory 검색 (RAM) - 가장 빠름
            hot_results = await self._search_hot_memory(query, max_results//4)
            all_results.extend(hot_results)
            
            # 2단계: WARM Memory 검색 (SSD Cache) - 빠름
            warm_results = await self._search_warm_memory(query, max_results//4)
            all_results.extend(warm_results)
            
            # 3단계: COLD Memory 검색 (SSD Archive) - 보통
            if len(all_results) < max_results//2:
                cold_results = await self._search_cold_memory(query, max_results//4)
                all_results.extend(cold_results)
            
            # 4단계: DEEP Archive 검색 (HDD) - 느림, 필요시에만
            if len(all_results) < max_results * 0.75:
                deep_results = await self._search_deep_archive(query, max_results//4)
                all_results.extend(deep_results)
            
            # 결과 통합 및 정렬 (중요도 + 관련도 + 최신순)
            sorted_results = sorted(all_results, 
                                  key=lambda x: (x.get("importance", 0) * x.get("relevance_score", 0)), 
                                  reverse=True)
            
            return sorted_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"메가 메모리 검색 오류: {e}")
            return []

    async def _search_hot_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """HOT Memory (RAM) 검색"""
        results = []
        try:
            for memory_id, memory_obj in self.hot_memory["data"].items():
                if query.lower() in memory_obj["content"].lower():
                    # 간단한 관련도 점수 계산
                    relevance_score = memory_obj["content"].lower().count(query.lower()) / len(memory_obj["content"])
                    memory_obj["relevance_score"] = min(1.0, relevance_score * 100)
                    memory_obj["search_tier"] = "hot_memory"
                    results.append(memory_obj)
            
            return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"HOT 메모리 검색 오류: {e}")
            return []

    async def _search_warm_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """WARM Memory (SSD Cache) 검색"""
        results = []
        try:
            cache_path = self.warm_memory["cache_path"]
            if cache_path.exists():
                for cache_file in cache_path.glob("*.json"):
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            memory_obj = json.load(f)
                        
                        if query.lower() in memory_obj["content"].lower():
                            relevance_score = memory_obj["content"].lower().count(query.lower()) / len(memory_obj["content"])
                            memory_obj["relevance_score"] = min(1.0, relevance_score * 100)
                            memory_obj["search_tier"] = "warm_memory"
                            results.append(memory_obj)
                    except:
                        continue
            
            return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"WARM 메모리 검색 오류: {e}")
            return []

    async def _search_cold_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """COLD Memory (SSD Archive) 검색 - 압축 해제"""
        results = []
        try:
            import gzip
            
            archive_path = self.cold_memory["archive_path"]
            if archive_path.exists():
                for archive_file in archive_path.glob("*.json.gz"):
                    try:
                        with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                            memory_obj = json.load(f)
                        
                        if query.lower() in memory_obj["content"].lower():
                            relevance_score = memory_obj["content"].lower().count(query.lower()) / len(memory_obj["content"])
                            memory_obj["relevance_score"] = min(1.0, relevance_score * 100)
                            memory_obj["search_tier"] = "cold_memory"
                            results.append(memory_obj)
                    except:
                        continue
            
            return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"COLD 메모리 검색 오류: {e}")
            return []

    async def _search_deep_archive(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """DEEP Archive (HDD) 검색 - 최대 압축 해제"""
        results = []
        try:
            import gzip
            
            archive_path = self.deep_archive["archive_path"]
            if archive_path.exists():
                for archive_file in archive_path.glob("*.archive.gz"):
                    try:
                        with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                            memory_obj = json.load(f)
                        
                        if query.lower() in memory_obj["content"].lower():
                            relevance_score = memory_obj["content"].lower().count(query.lower()) / len(memory_obj["content"])
                            memory_obj["relevance_score"] = min(1.0, relevance_score * 100)
                            memory_obj["search_tier"] = "deep_archive"
                            results.append(memory_obj)
                    except:
                        continue
            
            return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"DEEP 아카이브 검색 오류: {e}")
            return []

    async def get_mega_memory_stats(self) -> Dict[str, Any]:
        """메가 메모리 시스템 통계"""
        try:
            return {
                "total_capacity": {
                    "hot_memory_gb": self.hot_memory["capacity_gb"],
                    "warm_memory_gb": self.warm_memory["capacity_gb"], 
                    "cold_memory_gb": self.cold_memory["capacity_gb"],
                    "deep_archive_gb": self.deep_archive["capacity_gb"],
                    "total_gb": (self.hot_memory["capacity_gb"] + 
                               self.warm_memory["capacity_gb"] + 
                               self.cold_memory["capacity_gb"] + 
                               self.deep_archive["capacity_gb"])
                },
                "current_usage": {
                    "hot_memory_gb": self.hot_memory["current_usage_gb"],
                    "warm_memory_gb": self.warm_memory["current_usage_gb"],
                    "cold_memory_gb": self.cold_memory["current_usage_gb"], 
                    "deep_archive_gb": self.deep_archive["current_usage_gb"]
                },
                "performance": {
                    "hot_memory_hit_rate": self.hot_memory["hit_rate"],
                    "warm_memory_hit_rate": self.warm_memory["hit_rate"],
                    "total_objects": len(self.hot_memory["data"])
                },
                "system_status": "operational",
                "optimization_level": "192GB_RAM_12TB_Storage"
            }
            
        except Exception as e:
            self.logger.error(f"메가 메모리 통계 오류: {e}")
            return {"error": str(e)}