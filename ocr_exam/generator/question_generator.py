"""
시험 문제 생성 엔진
단어 데이터베이스로부터 랜덤하게 5지선다 동의어 문제를 생성합니다.
"""

import random
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

from ocr_exam.database.word_parser import Word, Synonym


@dataclass
class Choice:
    """문제 선택지"""
    label: str  # A, B, C, D, E
    word: str
    meaning: str


@dataclass
class Question:
    """시험 문제"""
    number: int
    target_word: str
    target_pronunciation: str
    target_meaning: str
    choices: List[Choice]
    correct_answer: str  # A, B, C, D, E

    def to_dict(self) -> Dict:
        return {
            'number': self.number,
            'target_word': self.target_word,
            'target_pronunciation': self.target_pronunciation,
            'target_meaning': self.target_meaning,
            'choices': [asdict(c) for c in self.choices],
            'correct_answer': self.correct_answer
        }


@dataclass
class ExamPaper:
    """시험지"""
    exam_id: str
    created_at: str
    questions: List[Question]
    answer_key: Dict[int, str]  # {문제번호: 정답}
    num_questions: int

    def to_dict(self) -> Dict:
        return {
            'exam_id': self.exam_id,
            'created_at': self.created_at,
            'num_questions': self.num_questions,
            'questions': [q.to_dict() for q in self.questions],
            'answer_key': self.answer_key
        }


class QuestionGenerator:
    """문제 생성기"""

    def __init__(self, words: List[Word]):
        """
        Args:
            words: 단어 데이터베이스
        """
        self.words = words
        self.all_synonyms = self._collect_all_synonyms()

    def _collect_all_synonyms(self) -> List[Synonym]:
        """모든 동의어 수집"""
        synonyms = []
        for word in self.words:
            synonyms.extend(word.synonyms)
        return synonyms

    def generate_exam(
        self,
        num_questions: int,
        seed: Optional[int] = None
    ) -> ExamPaper:
        """
        시험지 생성

        Args:
            num_questions: 생성할 문제 개수
            seed: 랜덤 시드 (재현성을 위해)

        Returns:
            생성된 시험지
        """
        if seed is not None:
            random.seed(seed)

        # 문제로 사용할 단어 랜덤 선택
        if num_questions > len(self.words):
            raise ValueError(
                f"요청한 문제 개수({num_questions})가 "
                f"단어 개수({len(self.words)})보다 많습니다."
            )

        selected_words = random.sample(self.words, num_questions)

        # 시험지 ID 생성
        exam_id = self._generate_exam_id()
        created_at = datetime.now().isoformat()

        # 문제 생성
        questions = []
        answer_key = {}

        for i, word in enumerate(selected_words, 1):
            question = self._generate_question(i, word)
            questions.append(question)
            answer_key[i] = question.correct_answer

        return ExamPaper(
            exam_id=exam_id,
            created_at=created_at,
            questions=questions,
            answer_key=answer_key,
            num_questions=num_questions
        )

    def _generate_question(
        self,
        question_number: int,
        target_word: Word
    ) -> Question:
        """
        개별 문제 생성

        Args:
            question_number: 문제 번호
            target_word: 대상 단어

        Returns:
            생성된 문제
        """
        if not target_word.synonyms:
            raise ValueError(f"단어 '{target_word.word}'에 동의어가 없습니다.")

        # 정답 선택 (해당 단어의 동의어 중 하나)
        correct_synonym = random.choice(target_word.synonyms)

        # 오답 생성 (다른 단어들의 동의어에서 선택)
        other_synonyms = [
            syn for word in self.words
            if word.word != target_word.word
            for syn in word.synonyms
        ]

        # 정답과 너무 유사한 오답 제외
        other_synonyms = [
            syn for syn in other_synonyms
            if syn.word != correct_synonym.word
        ]

        if len(other_synonyms) < 4:
            raise ValueError("오답 생성에 필요한 동의어가 부족합니다.")

        wrong_synonyms = random.sample(other_synonyms, 4)

        # 5개 선택지 생성 (정답 1개 + 오답 4개)
        all_choices = [correct_synonym] + wrong_synonyms
        random.shuffle(all_choices)

        # 라벨 할당 (A, B, C, D, E)
        labels = ['A', 'B', 'C', 'D', 'E']
        choices = []
        correct_answer = None

        for label, synonym in zip(labels, all_choices):
            choices.append(Choice(
                label=label,
                word=synonym.word,
                meaning=synonym.meaning
            ))

            # 정답 라벨 찾기
            if synonym.word == correct_synonym.word:
                correct_answer = label

        return Question(
            number=question_number,
            target_word=target_word.word,
            target_pronunciation=target_word.pronunciation,
            target_meaning=target_word.meaning,
            choices=choices,
            correct_answer=correct_answer
        )

    def _generate_exam_id(self) -> str:
        """
        시험지 고유 ID 생성 (8자리 해시코드)

        Returns:
            시험지 ID
        """
        timestamp = datetime.now().isoformat()
        random_str = str(random.random())
        hash_input = f"{timestamp}{random_str}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        return hash_digest[:8].upper()

    def save_exam(self, exam: ExamPaper, output_dir: str):
        """
        시험지를 JSON 파일로 저장

        Args:
            exam: 시험지
            output_dir: 출력 디렉토리
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        # 시험지 전체 저장
        exam_file = os.path.join(output_dir, f"exam_{exam.exam_id}.json")
        with open(exam_file, 'w', encoding='utf-8') as f:
            json.dump(exam.to_dict(), f, ensure_ascii=False, indent=2)

        # 정답지만 별도 저장
        answer_file = os.path.join(output_dir, f"answers_{exam.exam_id}.json")
        with open(answer_file, 'w', encoding='utf-8') as f:
            json.dump({
                'exam_id': exam.exam_id,
                'answer_key': exam.answer_key
            }, f, ensure_ascii=False, indent=2)

        print(f"시험지 저장 완료: {exam_file}")
        print(f"정답지 저장 완료: {answer_file}")

    @staticmethod
    def load_exam(exam_file: str) -> ExamPaper:
        """
        JSON 파일에서 시험지 로드

        Args:
            exam_file: 시험지 JSON 파일 경로

        Returns:
            시험지
        """
        with open(exam_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        questions = []
        for q_data in data['questions']:
            choices = [Choice(**c) for c in q_data['choices']]
            questions.append(Question(
                number=q_data['number'],
                target_word=q_data['target_word'],
                target_pronunciation=q_data['target_pronunciation'],
                target_meaning=q_data['target_meaning'],
                choices=choices,
                correct_answer=q_data['correct_answer']
            ))

        return ExamPaper(
            exam_id=data['exam_id'],
            created_at=data['created_at'],
            questions=questions,
            answer_key=data['answer_key'],
            num_questions=data['num_questions']
        )


if __name__ == '__main__':
    # 테스트
    from ocr_exam.database.word_parser import WordDatabaseParser

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

03 advance
[əd|vӕns]

n
전진, 발전
syn   boost  /  development  /  growth
             증대                  발전                      성장
"""

    parser = WordDatabaseParser()
    words = parser.parse_text(sample_text)

    generator = QuestionGenerator(words)
    exam = generator.generate_exam(num_questions=2)

    print(f"시험지 ID: {exam.exam_id}")
    print(f"문제 개수: {exam.num_questions}")
    print(f"\n정답: {exam.answer_key}")

    for question in exam.questions:
        print(f"\n{question.number}. {question.target_word} ({question.target_pronunciation})")
        print(f"   의미: {question.target_meaning}")
        print(f"   동의어를 고르시오:")
        for choice in question.choices:
            print(f"      {choice.label}) {choice.word} ({choice.meaning})")
        print(f"   정답: {question.correct_answer}")
