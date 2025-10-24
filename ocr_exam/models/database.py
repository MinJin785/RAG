"""
학생 정보 데이터베이스
SQLite를 사용한 학생 정보 및 성적 관리
"""

import sqlite3
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class Student:
    """학생 정보"""
    student_id: str
    name: str
    parent_phone: str
    student_phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'student_id': self.student_id,
            'name': self.name,
            'parent_phone': self.parent_phone,
            'student_phone': self.student_phone,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class GradeRecord:
    """성적 기록"""
    id: Optional[int] = None
    exam_id: str = ''
    student_id: str = ''
    score: float = 0.0
    percentage: float = 0.0
    correct_answers: int = 0
    total_questions: int = 0
    graded_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'student_id': self.student_id,
            'score': self.score,
            'percentage': self.percentage,
            'correct_answers': self.correct_answers,
            'total_questions': self.total_questions,
            'graded_at': self.graded_at
        }


class StudentDatabase:
    """학생 정보 데이터베이스 관리"""

    def __init__(self, db_path: str = "ocr_exam/data/students.db"):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path

        # 디렉토리 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 데이터베이스 초기화
        self._init_database()

    def _init_database(self):
        """데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 학생 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_phone TEXT NOT NULL,
                student_phone TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # 성적 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                score REAL NOT NULL,
                percentage REAL NOT NULL,
                correct_answers INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                graded_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (student_id)
            )
        ''')

        # 인덱스 생성
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grades_student_id
            ON grades (student_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_grades_exam_id
            ON grades (exam_id)
        ''')

        conn.commit()
        conn.close()

    # ===== 학생 관리 =====

    def add_student(self, student: Student) -> bool:
        """
        학생 추가

        Args:
            student: 학생 정보

        Returns:
            성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO students
                (student_id, name, parent_phone, student_phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                student.student_id,
                student.name,
                student.parent_phone,
                student.student_phone,
                now,
                now
            ))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            return False

    def get_student(self, student_id: str) -> Optional[Student]:
        """
        학생 정보 조회

        Args:
            student_id: 학생 고유번호

        Returns:
            학생 정보 (없으면 None)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT student_id, name, parent_phone, student_phone, created_at, updated_at
            FROM students
            WHERE student_id = ?
        ''', (student_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return Student(
                student_id=row[0],
                name=row[1],
                parent_phone=row[2],
                student_phone=row[3],
                created_at=row[4],
                updated_at=row[5]
            )

        return None

    def update_student(self, student: Student) -> bool:
        """
        학생 정보 수정

        Args:
            student: 학생 정보

        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            UPDATE students
            SET name = ?, parent_phone = ?, student_phone = ?, updated_at = ?
            WHERE student_id = ?
        ''', (
            student.name,
            student.parent_phone,
            student.student_phone,
            now,
            student.student_id
        ))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def delete_student(self, student_id: str) -> bool:
        """
        학생 삭제

        Args:
            student_id: 학생 고유번호

        Returns:
            성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return affected > 0

    def list_students(self) -> List[Student]:
        """
        전체 학생 목록 조회

        Returns:
            학생 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT student_id, name, parent_phone, student_phone, created_at, updated_at
            FROM students
            ORDER BY name
        ''')

        rows = cursor.fetchall()
        conn.close()

        students = []
        for row in rows:
            students.append(Student(
                student_id=row[0],
                name=row[1],
                parent_phone=row[2],
                student_phone=row[3],
                created_at=row[4],
                updated_at=row[5]
            ))

        return students

    # ===== 성적 관리 =====

    def add_grade(self, grade: GradeRecord) -> int:
        """
        성적 기록 추가

        Args:
            grade: 성적 기록

        Returns:
            생성된 레코드 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO grades
            (exam_id, student_id, score, percentage, correct_answers, total_questions, graded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            grade.exam_id,
            grade.student_id,
            grade.score,
            grade.percentage,
            grade.correct_answers,
            grade.total_questions,
            grade.graded_at or datetime.now().isoformat()
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def get_student_grades(self, student_id: str) -> List[GradeRecord]:
        """
        학생의 전체 성적 조회

        Args:
            student_id: 학생 고유번호

        Returns:
            성적 기록 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, exam_id, student_id, score, percentage,
                   correct_answers, total_questions, graded_at
            FROM grades
            WHERE student_id = ?
            ORDER BY graded_at DESC
        ''', (student_id,))

        rows = cursor.fetchall()
        conn.close()

        grades = []
        for row in rows:
            grades.append(GradeRecord(
                id=row[0],
                exam_id=row[1],
                student_id=row[2],
                score=row[3],
                percentage=row[4],
                correct_answers=row[5],
                total_questions=row[6],
                graded_at=row[7]
            ))

        return grades

    def get_exam_grades(self, exam_id: str) -> List[GradeRecord]:
        """
        특정 시험의 전체 성적 조회

        Args:
            exam_id: 시험지 ID

        Returns:
            성적 기록 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, exam_id, student_id, score, percentage,
                   correct_answers, total_questions, graded_at
            FROM grades
            WHERE exam_id = ?
            ORDER BY score DESC
        ''', (exam_id,))

        rows = cursor.fetchall()
        conn.close()

        grades = []
        for row in rows:
            grades.append(GradeRecord(
                id=row[0],
                exam_id=row[1],
                student_id=row[2],
                score=row[3],
                percentage=row[4],
                correct_answers=row[5],
                total_questions=row[6],
                graded_at=row[7]
            ))

        return grades


if __name__ == '__main__':
    # 테스트
    db = StudentDatabase("test_students.db")

    # 학생 추가
    student1 = Student(
        student_id="123456",
        name="김철수",
        parent_phone="010-1234-5678",
        student_phone="010-9876-5432"
    )

    db.add_student(student1)
    print("학생 추가 완료")

    # 학생 조회
    found = db.get_student("123456")
    if found:
        print(f"학생 조회: {found.name} ({found.student_id})")

    # 성적 추가
    grade = GradeRecord(
        exam_id="ABC12345",
        student_id="123456",
        score=80.0,
        percentage=80.0,
        correct_answers=8,
        total_questions=10,
        graded_at=datetime.now().isoformat()
    )

    db.add_grade(grade)
    print("성적 추가 완료")

    # 학생 성적 조회
    grades = db.get_student_grades("123456")
    print(f"\n학생 성적 ({len(grades)}건):")
    for g in grades:
        print(f"  시험 {g.exam_id}: {g.score}점 ({g.percentage}%)")
