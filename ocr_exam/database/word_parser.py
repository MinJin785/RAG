"""
단어 데이터베이스 파싱 모듈
텍스트, CSV, 엑셀 형식의 단어 데이터를 구조화된 형태로 파싱합니다.
"""

import re
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Synonym:
    """동의어 정보"""
    word: str
    meaning: str
    pronunciation: Optional[str] = None


@dataclass
class Word:
    """단어 정보"""
    number: int
    word: str
    pronunciation: str
    pos: str  # 품사 (v, n, a, etc.)
    meaning: str
    synonyms: List[Synonym]

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'number': self.number,
            'word': self.word,
            'pronunciation': self.pronunciation,
            'pos': self.pos,
            'meaning': self.meaning,
            'synonyms': [asdict(s) for s in self.synonyms]
        }


class WordDatabaseParser:
    """단어 데이터베이스 파서"""

    @staticmethod
    def parse_text_file(file_path: str) -> List[Word]:
        """
        텍스트 파일에서 단어 데이터 파싱

        Args:
            file_path: 텍스트 파일 경로

        Returns:
            파싱된 단어 리스트
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return WordDatabaseParser.parse_text(content)

    @staticmethod
    def parse_text(content: str) -> List[Word]:
        """
        텍스트 컨텐츠에서 단어 데이터 파싱

        Args:
            content: 텍스트 컨텐츠

        Returns:
            파싱된 단어 리스트
        """
        words = []

        # 각 단어 항목을 숫자로 시작하는 부분으로 분리
        pattern = r'(\d{2,3})\s+(\S+)\s*\n\[([^\]]+)\]\s*\n\s*([nvap])\s*\n\s*(.+?)\s*\nsyn\s+(.+?)(?=\n\d{2,3}\s+\w+|\Z)'

        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            number = int(match.group(1))
            word = match.group(2)
            pronunciation = match.group(3)
            pos = match.group(4)
            meaning = match.group(5).strip()
            syn_text = match.group(6)

            # 동의어 파싱
            synonyms = WordDatabaseParser._parse_synonyms(syn_text)

            words.append(Word(
                number=number,
                word=word,
                pronunciation=pronunciation,
                pos=pos,
                meaning=meaning,
                synonyms=synonyms
            ))

        return words

    @staticmethod
    def _parse_synonyms(syn_text: str) -> List[Synonym]:
        """
        동의어 텍스트 파싱

        Args:
            syn_text: 동의어 텍스트 (예: "speed up / move faster / hasten")

        Returns:
            동의어 리스트
        """
        synonyms = []

        # 줄바꿈으로 분리 (영어 줄과 한글 줄)
        lines = [line.strip() for line in syn_text.split('\n') if line.strip()]

        if not lines:
            return synonyms

        # 첫 번째 줄: 영어 동의어들
        english_line = lines[0]
        # / 로 구분된 영어 단어들
        english_parts = [part.strip() for part in english_line.split('/')]

        # 두 번째 줄: 한글 뜻들 (있는 경우)
        korean_parts = []
        if len(lines) > 1:
            korean_line = lines[1]
            korean_parts = [part.strip() for part in korean_line.split('/')]

        # 발음 기호 추출 및 제거
        for i, eng_word in enumerate(english_parts):
            # 발음 기호 패턴 찾기
            pronunciation = None
            word_clean = eng_word

            # [발음] 형식 추출
            pron_match = re.search(r'\[([^\]]+)\]', eng_word)
            if pron_match:
                pronunciation = pron_match.group(1)
                word_clean = re.sub(r'\s*\[[^\]]+\]', '', eng_word).strip()

            # 한글 뜻 가져오기
            meaning = korean_parts[i] if i < len(korean_parts) else ''
            # 한글 뜻에서 발음 기호 제거
            meaning = re.sub(r'\s*\[[^\]]+\]', '', meaning).strip()

            if word_clean:
                synonyms.append(Synonym(
                    word=word_clean,
                    meaning=meaning,
                    pronunciation=pronunciation
                ))

        return synonyms

    @staticmethod
    def parse_csv_file(file_path: str) -> List[Word]:
        """
        CSV 파일에서 단어 데이터 파싱

        Args:
            file_path: CSV 파일 경로

        Returns:
            파싱된 단어 리스트
        """
        df = pd.read_csv(file_path)
        return WordDatabaseParser._parse_dataframe(df)

    @staticmethod
    def parse_excel_file(file_path: str) -> List[Word]:
        """
        엑셀 파일에서 단어 데이터 파싱

        Args:
            file_path: 엑셀 파일 경로

        Returns:
            파싱된 단어 리스트
        """
        df = pd.read_excel(file_path)
        return WordDatabaseParser._parse_dataframe(df)

    @staticmethod
    def _parse_dataframe(df: pd.DataFrame) -> List[Word]:
        """
        데이터프레임에서 단어 데이터 파싱

        Args:
            df: 판다스 데이터프레임

        Returns:
            파싱된 단어 리스트
        """
        words = []

        for _, row in df.iterrows():
            synonyms = []

            # 동의어 컬럼들 파싱 (syn1, syn2, ... 또는 synonyms 컬럼)
            if 'synonyms' in row:
                syn_text = str(row['synonyms'])
                synonyms = WordDatabaseParser._parse_synonyms(syn_text)
            else:
                # syn1, syn2, ... 형식 찾기
                for col in df.columns:
                    if col.startswith('syn'):
                        if pd.notna(row[col]):
                            parts = str(row[col]).split('/')
                            if len(parts) >= 2:
                                synonyms.append(Synonym(
                                    word=parts[0].strip(),
                                    meaning=parts[1].strip() if len(parts) > 1 else ''
                                ))

            words.append(Word(
                number=int(row.get('number', 0)),
                word=str(row['word']),
                pronunciation=str(row.get('pronunciation', '')),
                pos=str(row.get('pos', 'v')),
                meaning=str(row.get('meaning', '')),
                synonyms=synonyms
            ))

        return words

    @staticmethod
    def save_to_json(words: List[Word], output_path: str):
        """
        단어 리스트를 JSON 파일로 저장

        Args:
            words: 단어 리스트
            output_path: 출력 JSON 파일 경로
        """
        import json

        data = [word.to_dict() for word in words]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_from_json(json_path: str) -> List[Word]:
        """
        JSON 파일에서 단어 리스트 로드

        Args:
            json_path: JSON 파일 경로

        Returns:
            단어 리스트
        """
        import json

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        words = []
        for item in data:
            synonyms = [Synonym(**s) for s in item['synonyms']]
            words.append(Word(
                number=item['number'],
                word=item['word'],
                pronunciation=item['pronunciation'],
                pos=item['pos'],
                meaning=item['meaning'],
                synonyms=synonyms
            ))

        return words


if __name__ == '__main__':
    # 테스트
    sample_text = """01 accelerate
[ək|seləreɪt]

v
 가속화되다, 속도를 높이다
syn   speed up  /  move faster  /  hasten
           속도를 높이다      더 빠르게 움직이다        재촉하다

02 acquire
[ə|kwaɪə(r)]

v
 습득하다, 얻다
syn   earn   /   gain   /   get
            얻다             얻다          얻다
"""

    parser = WordDatabaseParser()
    words = parser.parse_text(sample_text)

    for word in words:
        print(f"{word.number}. {word.word} ({word.pronunciation})")
        print(f"   {word.pos} - {word.meaning}")
        print(f"   Synonyms: {len(word.synonyms)}")
        for syn in word.synonyms:
            print(f"      - {syn.word}: {syn.meaning}")
        print()
