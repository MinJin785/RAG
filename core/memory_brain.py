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

@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: np.ndarray
    timestamp: datetime
    importance: float = 0.5

class MemoryBrain:
    def __init__(self, data_path: str = "data/memory_db"):
        self.data_path = data_path
        self.db_path = os.path.join(data_path, "memory.db")
        self.index_path = os.path.join(data_path, "faiss_index.bin")
        self.metadata_path = os.path.join(data_path, "metadata.pkl")
        
        # 디렉토리 생성
        os.makedirs(data_path, exist_ok=True)
        
        # 임베딩 모델 초기화
        self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_dim = 384
        
        # FAISS 인덱스 초기화
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.memory_metadata: List[Dict] = []
        
        # SQLite 연결
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._load_existing_data()

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                embedding_id INTEGER,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                context_used TEXT
            )
        ''')
        
        self.conn.commit()
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count)')
            self.conn.commit()
        except:
            pass

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

    async def add_memory(self, content: str, metadata: Dict[str, Any] = None, 
                        importance: float = 0.5) -> str:
        """새로운 기억 추가"""
        try:
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            if metadata is None:
                metadata = {}
            
            # 임베딩 생성
            embedding = await asyncio.to_thread(
                self.embedding_model.encode, 
                content, 
                convert_to_numpy=True
            )
            embedding = embedding.astype(np.float32)
            
            # FAISS에 추가
            embedding_id = self.index.ntotal
            self.index.add(embedding.reshape(1, -1))
            
            # 메타데이터 저장
            meta_entry = {
                "id": memory_id,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
                "importance": importance,
                "embedding_id": embedding_id
            }
            self.memory_metadata.append(meta_entry)
            
            # SQLite에 저장
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO memories (id, content, metadata, timestamp, importance, embedding_id, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id, content, json.dumps(metadata, ensure_ascii=False),
                datetime.now().isoformat(), importance, embedding_id, 0, datetime.now().isoformat()
            ))
            self.conn.commit()
            
            # 주기적 저장
            if self.index.ntotal % 100 == 0:
                await self._save_data()
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"메모리 추가 오류: {e}")
            return ""

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
            new_index = faiss.IndexFlatIP(self.embedding_dim)
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
            "embedding_dimension": self.embedding_dim
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

    def __del__(self):
        """소멸자"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass