"""
PDF를 배경화면용 고해상도 이미지로 변환 (poppler 불필요!)
PyMuPDF 사용
"""

import fitz  # PyMuPDF
import os
from PIL import Image

# PDF 파일 찾기
pdf_dir = "ocr_exam/data/exams"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

if not pdf_files:
    print("❌ PDF 파일을 찾을 수 없습니다!")
    exit(1)

# 가장 최근 PDF 파일 사용
pdf_file = sorted(pdf_files)[-1]
pdf_path = os.path.join(pdf_dir, pdf_file)

print("=" * 70)
print("PDF를 배경화면용 이미지로 변환 중...")
print("=" * 70)
print(f"\n📄 PDF 파일: {pdf_path}")

# 출력 디렉토리
output_dir = "ocr_exam/data/exams/wallpapers"
os.makedirs(output_dir, exist_ok=True)

# PDF 열기
doc = fitz.open(pdf_path)

print(f"📑 총 {len(doc)} 페이지\n")

# 각 페이지를 이미지로 변환
for page_num in range(len(doc)):
    page = doc[page_num]

    # 고해상도 설정 (300 DPI)
    zoom = 3  # zoom=3 이면 약 300 DPI
    mat = fitz.Matrix(zoom, zoom)

    # 이미지로 렌더링
    pix = page.get_pixmap(matrix=mat)

    # PNG로 저장
    output_filename = f"wallpaper_page_{page_num + 1}.png"
    output_path = os.path.join(output_dir, output_filename)

    pix.save(output_path)

    # 파일 크기 확인
    file_size = os.path.getsize(output_path) / 1024  # KB

    print(f"✅ 페이지 {page_num + 1}: {output_path}")
    print(f"   크기: {pix.width} x {pix.height} 픽셀")
    print(f"   파일 크기: {file_size:.1f} KB\n")

doc.close()

print("=" * 70)
print("변환 완료!")
print("=" * 70)
print(f"\n📁 저장 위치: {os.path.abspath(output_dir)}")
print("\n💡 배경화면 설정 방법:")
print("   1. 위 폴더를 탐색기로 열기")
print("   2. PNG 파일 우클릭")
print("   3. '배경 화면으로 설정' 클릭")

# 탐색기로 폴더 자동으로 열기
print("\n🎨 폴더를 자동으로 엽니다...")
os.system(f'explorer "{os.path.abspath(output_dir)}"')
