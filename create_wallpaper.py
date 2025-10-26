"""
PDF를 배경화면용 통합 이미지로 변환
- 모든 페이지를 1개 이미지로 병합
- 배경화면 비율 옵션 (16:9, 21:9, 원본)
"""

import fitz  # PyMuPDF
import os
from PIL import Image, ImageDraw, ImageFont

def create_wallpaper(pdf_path, output_path, layout='vertical', screen_ratio=None):
    """
    PDF를 배경화면용 이미지로 변환

    Args:
        pdf_path: PDF 파일 경로
        output_path: 출력 이미지 경로
        layout: 'vertical' (세로 병합) 또는 'grid' (격자 배치)
        screen_ratio: '16:9', '21:9', None (원본 비율)
    """
    print(f"\n📄 PDF 변환 중: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []

    # 고해상도로 각 페이지 렌더링
    zoom = 2.5  # 약 250 DPI
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)

        # PIL Image로 변환
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(img)
        print(f"  ✓ 페이지 {page_num + 1}: {pix.width}x{pix.height}")

    doc.close()

    # 레이아웃에 따라 병합
    if layout == 'vertical':
        # 세로로 이어붙이기
        total_width = max(img.width for img in pages)
        total_height = sum(img.height for img in pages)

        result = Image.new('RGB', (total_width, total_height), 'white')

        y_offset = 0
        for img in pages:
            # 중앙 정렬
            x_offset = (total_width - img.width) // 2
            result.paste(img, (x_offset, y_offset))
            y_offset += img.height

    elif layout == 'grid':
        # 격자 배치 (2열)
        cols = 2
        rows = (len(pages) + cols - 1) // cols

        page_width = pages[0].width
        page_height = pages[0].height

        total_width = page_width * cols
        total_height = page_height * rows

        result = Image.new('RGB', (total_width, total_height), 'white')

        for idx, img in enumerate(pages):
            row = idx // cols
            col = idx % cols
            x = col * page_width
            y = row * page_height
            result.paste(img, (x, y))

    # 화면 비율에 맞게 리사이즈 (옵션)
    if screen_ratio:
        if screen_ratio == '16:9':
            target_width = 3840  # 4K
            target_height = 2160
        elif screen_ratio == '21:9':
            target_width = 3440  # UWQHD
            target_height = 1440
        else:
            target_width = result.width
            target_height = result.height

        # 비율 유지하며 리사이즈
        result.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        print(f"\n  📐 리사이즈: {result.width}x{result.height}")

    # 저장
    result.save(output_path, 'PNG', quality=95, optimize=True)
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB

    print(f"\n✅ 완성!")
    print(f"  크기: {result.width}x{result.height} 픽셀")
    print(f"  파일: {file_size:.2f} MB")
    print(f"  경로: {output_path}")

    return output_path


def main():
    print("=" * 70)
    print("배경화면용 통합 이미지 생성기")
    print("=" * 70)

    # PDF 파일 찾기
    pdf_dir = "ocr_exam/data/exams"
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print("❌ PDF 파일을 찾을 수 없습니다!")
        return

    # 가장 최근 PDF
    pdf_file = sorted(pdf_files)[-1]
    pdf_path = os.path.join(pdf_dir, pdf_file)
    exam_id = pdf_file.replace('omr_', '').replace('.pdf', '')

    # 출력 디렉토리
    output_dir = "ocr_exam/data/exams/wallpapers"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n사용할 PDF: {pdf_file}")
    print("\n📋 생성 옵션:")
    print("  1. 세로 병합 (원본 비율)")
    print("  2. 세로 병합 (16:9 비율)")
    print("  3. 세로 병합 (21:9 비율)")
    print("  4. 격자 배치 (2열)")

    # 모든 옵션 생성
    options = [
        ('vertical', None, f'wallpaper_{exam_id}_vertical.png', '세로 병합 (원본)'),
        ('vertical', '16:9', f'wallpaper_{exam_id}_16-9.png', '세로 병합 (16:9)'),
        ('vertical', '21:9', f'wallpaper_{exam_id}_21-9.png', '세로 병합 (21:9)'),
        ('grid', None, f'wallpaper_{exam_id}_grid.png', '격자 배치'),
    ]

    print("\n" + "=" * 70)

    created_files = []
    for layout, ratio, filename, desc in options:
        print(f"\n🎨 {desc} 생성 중...")
        output_path = os.path.join(output_dir, filename)

        try:
            create_wallpaper(pdf_path, output_path, layout, ratio)
            created_files.append(output_path)
        except Exception as e:
            print(f"  ❌ 오류: {e}")

    print("\n" + "=" * 70)
    print(f"✨ 총 {len(created_files)}개 이미지 생성 완료!")
    print("=" * 70)
    print(f"\n📁 저장 위치: {os.path.abspath(output_dir)}")

    # 탐색기 열기
    print("\n🎨 폴더를 엽니다...")
    abs_path = os.path.abspath(output_dir)
    os.system(f'explorer "{abs_path}"')

    print("\n💡 배경화면 설정:")
    print("  1. 생성된 이미지 중 마음에 드는 것 선택")
    print("  2. 우클릭 → '배경 화면으로 설정'")
    print("\n✨ 추천: wallpaper_*_vertical.png (세로 병합, 원본 비율)")


if __name__ == '__main__':
    main()
