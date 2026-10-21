#!/usr/bin/env python3
"""
Script tạo bài viết hàng ngày.
Chạy bằng cron: 0 8 * * * cd /path/to/phongthuy_site && /path/to/venv/bin/python generate_daily.py
"""
import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, create_post_from_topic, TOPICS, Setting
from models import TopicHistory, Post

def get_unused_topic():
    used = {h.topic for h in TopicHistory.query.all()}
    available = [t for t in TOPICS if t not in used]
    if not available:
        # Reset hoặc mở rộng danh sách
        print("Hết chủ đề chưa dùng. Cần bổ sung thêm chủ đề.")
        return None
    # Chọn ngẫu nhiên hoặc theo thứ tự
    import random
    return random.choice(available)

def main():
    with app.app_context():
        topic = get_unused_topic()
        if not topic:
            print("Không có chủ đề mới.")
            return
        post = create_post_from_topic(topic)
        auto = Setting.get('auto_publish', 'false') == 'true'
        if auto:
            post.status = 'published'
            post.published_at = datetime.utcnow()
            db.session.commit()
            print(f"Đã tự đăng bài: {post.title}")
        else:
            print(f"Đã tạo bài chờ duyệt: {post.title} (ID: {post.id})")

if __name__ == '__main__':
    main()
