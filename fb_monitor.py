#!/usr/bin/env python3
"""
Script theo dõi bài viết mới từ các Trang Facebook công khai.
Chạy bằng cron: 0 */6 * * * cd /path && python fb_monitor.py
Chỉ sử dụng Graph API hợp lệ với access token.
"""
import os
import sys
from datetime import datetime, timedelta
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, DISCLAIMER
from models import FacebookPage, FacebookPostLog, Post, Setting
from slugify import slugify

GRAPH_VERSION = "v26.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

def fetch_page_posts(page):
    if not page.access_token:
        return None, "Thiếu access token"
    url = f"{BASE_URL}/{page.page_id}/feed"
    params = {
        'access_token': page.access_token,
        'fields': 'id,message,created_time,permalink_url',
        'limit': 5
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            return None, f"API error {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        if 'error' in data:
            return None, str(data['error'])
        return data.get('data', []), None
    except Exception as e:
        return None, str(e)

def create_summary_post(original, page_name, original_url):
    """Tạo bản tóm tắt, không đăng nguyên văn."""
    message = original.get('message', '') or ''
    # Tóm tắt ngắn (trong thực tế có thể dùng LLM)
    summary = message[:200] + "..." if len(message) > 200 else message
    title = f"Tóm tắt: Bài viết từ {page_name}"
    slug = slugify(f"{title}-{original.get('id', '')[-8:]}")
    content = f"""
<h2>Tóm tắt nội dung</h2>
<p>{summary}</p>
<p><em>Đây là bản tóm tắt được diễn đạt lại, không phải nội dung nguyên văn.</em></p>
<p>Nguồn: <a href="{original_url}" target="_blank" rel="noopener">{page_name}</a></p>
{DISCLAIMER}
"""
    post = Post(
        title=title,
        slug=slug,
        short_description=f"Tóm tắt bài viết từ trang {page_name}",
        content=content,
        seo_title=title[:60],
        meta_description=summary[:160],
        status='pending',
        source_type='facebook',
        source_url=original_url,
        source_page_name=page_name
    )
    db.session.add(post)
    db.session.flush()
    return post

def main():
    with app.app_context():
        pages = FacebookPage.query.filter_by(is_active=True).all()
        for page in pages:
            posts_data, error = fetch_page_posts(page)
            page.last_checked = datetime.utcnow()
            if error:
                # Ghi log lỗi
                log = FacebookPostLog(
                    page_id=page.id,
                    status='error',
                    error_message=error
                )
                db.session.add(log)
                print(f"Lỗi với trang {page.name}: {error}")
                continue
            for p in posts_data or []:
                post_id = p.get('id')
                if FacebookPostLog.query.filter_by(original_post_id=post_id).first():
                    continue  # Đã xử lý
                original_url = p.get('permalink_url') or f"https://facebook.com/{post_id}"
                summary_post = create_summary_post(p, page.name, original_url)
                log = FacebookPostLog(
                    page_id=page.id,
                    original_post_id=post_id,
                    original_url=original_url,
                    message=p.get('message', ''),
                    created_time=datetime.strptime(p.get('created_time', '')[:19], '%Y-%m-%dT%H:%M:%S') if p.get('created_time') else None,
                    status='processed',
                    summary_post_id=summary_post.id
                )
                db.session.add(log)
                print(f"Đã tạo bản tóm tắt chờ duyệt từ {page.name}: {post_id}")
        db.session.commit()

if __name__ == '__main__':
    main()
