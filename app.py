import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from slugify import slugify
import requests
from models import db, User, Category, Post, TopicHistory, FacebookPage, FacebookPostLog, Comment, Setting

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
# Use absolute path or /tmp for SQLite on Render (ephemeral)
db_path = os.environ.get('DATABASE_URL', 'sqlite:///phongthuy.db')
if db_path.startswith('sqlite:///') and not db_path.startswith('sqlite:////'):
    # Make relative SQLite absolute under /tmp for Render
    db_path = 'sqlite:////tmp/phongthuy.db'
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_categories():
    try:
        return dict(categories=Category.query.all(), year=datetime.now().year)
    except:
        return dict(categories=[], year=datetime.now().year)

# Categories mặc định
DEFAULT_CATEGORIES = [
    ("Phong thủy nhà ở", "phong-thuy-nha-o", "Kiến thức phong thủy cho không gian sống"),
    ("Bàn làm việc", "ban-lam-viec", "Bố trí bàn làm việc hợp phong thủy"),
    ("Phòng ngủ", "phong-ngu", "Phong thủy phòng ngủ cho giấc ngủ ngon"),
    ("Cây phong thủy", "cay-phong-thuy", "Các loại cây mang lại may mắn"),
    ("Màu sắc", "mau-sac", "Ý nghĩa màu sắc trong phong thủy"),
    ("Vật phẩm phong thủy", "vat-pham-phong-thuy", "Các vật phẩm phong thủy phổ biến"),
    ("Kiến thức theo tuổi", "kien-thuc-theo-tuoi", "Phong thủy theo tuổi và lịch âm"),
]

TOPICS = [
    "Hướng nhà hợp tuổi theo phong thủy",
    "Cách bố trí phòng khách phong thủy",
    "Màu sắc may mắn cho người tuổi Tý",
    "Cây kim tiền trong phong thủy",
    "Vị trí đặt giường ngủ hợp lý",
    "Phong thủy bàn làm việc cho sự nghiệp",
    "Ý nghĩa các hướng nhà",
    "Cách hóa giải phong thủy xấu đơn giản",
    "Vật phẩm phong thủy cho văn phòng",
    "Lịch âm và ngày tốt trong tháng",
]

DISCLAIMER = """
<p class=\"disclaimer\"><strong>Lưu ý:</strong> Nội dung bài viết dựa trên quan niệm văn hóa và phong thủy truyền thống, mang tính tham khảo. 
Phong thủy không phải là khoa học đã được chứng minh. Không hứa hẹn chắc chắn về tài lộc, sức khỏe hay tình duyên. 
Không thay thế tư vấn y tế, tài chính hoặc chuyên môn. Hãy tự cân nhắc trước khi áp dụng.</p>
"""

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        for name, slug, desc in DEFAULT_CATEGORIES:
            if not Category.query.filter_by(slug=slug).first():
                cat = Category(name=name, slug=slug, description=desc)
                db.session.add(cat)
        if not Setting.query.filter_by(key='auto_publish').first():
            Setting.set('auto_publish', 'false')
            Setting.set('daily_post_hour', '8')
            Setting.set('fb_check_interval_hours', '6')
        db.session.commit()

# Initialize DB on startup (important for Gunicorn/Render)
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print(f"DB init warning: {e}")

def generate_slug(title):
    return slugify(title, lowercase=True, separator='-')

def create_post_from_topic(topic, category_name=None):
    title = f"{topic} - Quan niệm phong thủy tham khảo"
    slug = generate_slug(title)
    if Post.query.filter_by(slug=slug).first():
        slug = f"{slug}-{datetime.now().strftime('%Y%m%d')}"
    short_desc = f"Tìm hiểu về {topic.lower()} theo quan niệm phong thủy truyền thống. Bài viết mang tính tham khảo văn hóa."
    content = f"""
<h2>Giới thiệu</h2>
<p>{topic} là một trong những chủ đề được nhiều người quan tâm trong phong thủy nhà ở và cuộc sống hàng ngày. 
Theo quan niệm văn hóa truyền thống, việc chú ý đến yếu tố này có thể mang lại cảm giác hài hòa cho không gian sống.</p>

<h2>Những điều cần lưu ý</h2>
<ul>
<li>Xem xét hướng và vị trí phù hợp với không gian thực tế của bạn.</li>
<li>Ưu tiên sự thoải mái và an toàn hơn là theo sát các quy tắc cứng nhắc.</li>
<li>Kết hợp với các yếu tố khoa học như thông gió, ánh sáng tự nhiên.</li>
</ul>

<h2>Gợi ý thực tế</h2>
<p>Bạn có thể bắt đầu bằng cách quan sát không gian hiện tại, điều chỉnh bố trí đồ đạc sao cho gọn gàng, 
tạo cảm giác thông thoáng. Đây là cách tiếp cận đơn giản và dễ thực hiện.</p>

{DISCLAIMER}

<h2>Kết luận</h2>
<p>Hy vọng những thông tin trên giúp bạn có thêm góc nhìn tham khảo về {topic.lower()}. 
Hãy áp dụng một cách linh hoạt và phù hợp với hoàn cảnh thực tế của mình.</p>
"""
    cat = Category.query.filter_by(name=category_name).first() if category_name else Category.query.first()
    image_url = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80"
    post = Post(
        title=title,
        slug=slug,
        short_description=short_desc,
        content=content,
        seo_title=title[:60],
        meta_description=short_desc[:160],
        image_url=image_url,
        status='pending',
        category_id=cat.id if cat else None,
        topic_used=topic,
        source_type='generated'
    )
    db.session.add(post)
    db.session.flush()
    hist = TopicHistory(topic=topic, post_id=post.id)
    db.session.add(hist)
    db.session.commit()
    return post

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(status='published').order_by(Post.published_at.desc()).paginate(page=page, per_page=10)
    featured = Post.query.filter_by(status='published', is_featured=True).limit(3).all()
    categories = Category.query.all()
    return render_template('index.html', posts=posts, featured=featured, categories=categories)

@app.route('/bai-viet/<slug>')
def post_detail(slug):
    post = Post.query.filter_by(slug=slug, status='published').first_or_404()
    comments = Comment.query.filter_by(post_id=post.id, is_approved=True).order_by(Comment.created_at.desc()).all()
    related = Post.query.filter(Post.category_id == post.category_id, Post.id != post.id, Post.status=='published').limit(3).all()
    return render_template('post.html', post=post, comments=comments, related=related)

@app.route('/danh-muc/<slug>')
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(category_id=cat.id, status='published').order_by(Post.published_at.desc()).paginate(page=page, per_page=10)
    return render_template('category.html', category=cat, posts=posts)

@app.route('/tim-kiem')
def search():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    if q:
        posts = Post.query.filter(
            Post.status=='published',
            (Post.title.contains(q) | Post.content.contains(q))
        ).order_by(Post.published_at.desc()).paginate(page=page, per_page=10)
    else:
        posts = None
    return render_template('search.html', posts=posts, query=q)

@app.route('/sitemap.xml')
def sitemap():
    posts = Post.query.filter_by(status='published').all()
    return render_template('sitemap.xml', posts=posts), 200, {'Content-Type': 'application/xml'}

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    name = request.form.get('author_name')
    email = request.form.get('author_email')
    content = request.form.get('content')
    if name and content:
        comment = Comment(post_id=post_id, author_name=name, author_email=email, content=content, is_approved=False)
        db.session.add(comment)
        db.session.commit()
        flash('Bình luận của bạn đã được gửi và đang chờ kiểm duyệt.', 'success')
    return redirect(url_for('post_detail', slug=post.slug))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Đăng nhập thất bại', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    pending = Post.query.filter_by(status='pending').count()
    published = Post.query.filter_by(status='published').count()
    fb_pages = FacebookPage.query.count()
    return render_template('admin/dashboard.html', pending=pending, published=published, fb_pages=fb_pages)

@app.route('/admin/posts')
@login_required
def admin_posts():
    status = request.args.get('status', 'all')
    query = Post.query
    if status != 'all':
        query = query.filter_by(status=status)
    posts = query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts, current_status=status)

@app.route('/admin/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.all()
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.short_description = request.form.get('short_description')
        post.seo_title = request.form.get('seo_title')
        post.meta_description = request.form.get('meta_description')
        post.category_id = request.form.get('category_id', type=int)
        post.is_featured = bool(request.form.get('is_featured'))
        status = request.form.get('status')
        if status == 'published' and not post.published_at:
            post.published_at = datetime.utcnow()
        post.status = status
        db.session.commit()
        flash('Đã cập nhật bài viết', 'success')
        return redirect(url_for('admin_posts'))
    return render_template('admin/edit_post.html', post=post, categories=categories)

@app.route('/admin/post/<int:post_id>/approve')
@login_required
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'published'
    post.published_at = datetime.utcnow()
    db.session.commit()
    flash('Đã duyệt và đăng bài', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        Setting.set('auto_publish', 'true' if request.form.get('auto_publish') else 'false')
        Setting.set('daily_post_hour', request.form.get('daily_post_hour', '8'))
        Setting.set('fb_check_interval_hours', request.form.get('fb_check_interval_hours', '6'))
        flash('Đã lưu cài đặt', 'success')
    auto_publish = Setting.get('auto_publish', 'false') == 'true'
    hour = Setting.get('daily_post_hour', '8')
    fb_interval = Setting.get('fb_check_interval_hours', '6')
    return render_template('admin/settings.html', auto_publish=auto_publish, hour=hour, fb_interval=fb_interval)

@app.route('/admin/facebook')
@login_required
def admin_facebook():
    pages = FacebookPage.query.all()
    return render_template('admin/facebook.html', pages=pages)

@app.route('/admin/facebook/add', methods=['POST'])
@login_required
def add_facebook_page():
    name = request.form.get('name')
    page_id = request.form.get('page_id')
    token = request.form.get('access_token')
    if name and page_id:
        page = FacebookPage(name=name, page_id=page_id, access_token=token)
        db.session.add(page)
        db.session.commit()
        flash('Đã thêm trang Facebook', 'success')
    return redirect(url_for('admin_facebook'))

@app.route('/admin/facebook/<int:page_id>/delete')
@login_required
def delete_facebook_page(page_id):
    page = FacebookPage.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash('Đã xóa trang', 'success')
    return redirect(url_for('admin_facebook'))

@app.route('/admin/comments')
@login_required
def admin_comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments)

@app.route('/admin/comment/<int:comment_id>/approve')
@login_required
def approve_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    c.is_approved = True
    db.session.commit()
    return redirect(url_for('admin_comments'))

@app.errorhandler(500)
def internal_error(error):
    return "Internal Server Error - Vui lòng thử lại sau. Kiểm tra logs trên Render nếu cần.", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
