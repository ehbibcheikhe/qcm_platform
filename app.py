import os
import csv
import io
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session, abort
from flask_login import (LoginManager, login_user, logout_user, login_required,
                          current_user, UserMixin)

from models import db, User, Category, Quiz, Question, Choice, Result, Answer

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'qcm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول أولاً / Veuillez vous connecter'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


TRANSLATIONS = {
    'ar': {
        'app_name': 'منصة تميز', 'home': 'الرئيسية', 'login': 'تسجيل الدخول', 'register': 'إنشاء حساب',
        'logout': 'تسجيل الخروج', 'dashboard': 'لوحتي', 'leaderboard': 'الترتيب العام', 'admin_panel': 'لوحة الإدارة',
        'welcome_title': 'تدرّب على المسابقات وطوّر مستواك', 'welcome_sub': 'مجموعة متنوعة من الاختبارات في مجالات مختلفة، اختبر معلوماتك وقارن نتائجك',
        'all_categories': 'كل التصنيفات', 'questions': 'أسئلة', 'minutes': 'دقيقة', 'difficulty': 'الصعوبة',
        'easy': 'سهل', 'medium': 'متوسط', 'hard': 'صعب', 'start_quiz': 'ابدأ المسابقة', 'best_score': 'أفضل نتيجة',
        'top_players': 'أفضل المشاركين', 'points': 'نقطة', 'no_quizzes': 'لا توجد مسابقات متاحة حاليًا',
        'username': 'اسم المستخدم', 'email': 'البريد الإلكتروني', 'password': 'كلمة المرور',
        'already_account': 'لديك حساب؟', 'no_account': 'ليس لديك حساب؟', 'question': 'سؤال',
        'of': 'من', 'next': 'التالي', 'previous': 'السابق', 'finish': 'إنهاء المسابقة', 'time_left': 'الوقت المتبقي',
        'your_score': 'نتيجتك', 'correct_answers': 'الإجابات الصحيحة', 'wrong_answers': 'الإجابات الخاطئة',
        'time_taken': 'الوقت المستغرق', 'review_answers': 'مراجعة الإجابات', 'back_home': 'العودة للرئيسية',
        'retry_quiz': 'إعادة المحاولة', 'my_history': 'سجل مسابقاتي', 'no_results_yet': 'لم تخض أي مسابقة بعد',
        'date': 'التاريخ', 'quiz': 'المسابقة', 'score': 'النقاط', 'percentage': 'النسبة', 'view': 'عرض',
        'rank': 'الترتيب', 'player': 'المشارك', 'total_points': 'مجموع النقاط', 'manage_categories': 'إدارة التصنيفات',
        'manage_quizzes': 'إدارة المسابقات', 'manage_users': 'إدارة المستخدمين', 'all_results': 'كل النتائج',
        'add': 'إضافة', 'edit': 'تعديل', 'delete': 'حذف', 'save': 'حفظ', 'cancel': 'إلغاء', 'name': 'الاسم',
        'actions': 'إجراءات', 'add_quiz': 'إضافة مسابقة', 'title': 'العنوان', 'description': 'الوصف',
        'category': 'التصنيف', 'duration': 'المدة (دقيقة)', 'published': 'منشور', 'manage_questions': 'إدارة الأسئلة',
        'add_question': 'إضافة سؤال', 'import_csv': 'استيراد من CSV', 'question_text': 'نص السؤال',
        'choices': 'الاختيارات', 'correct_choice': 'الاختيار الصحيح', 'explanation': 'الشرح (اختياري)',
        'download_sample': 'تحميل نموذج CSV', 'choose_file': 'اختر ملف CSV', 'import': 'استيراد',
        'admin': 'مسؤول', 'user': 'مستخدم', 'make_admin': 'جعله مسؤولًا', 'remove_admin': 'إزالة الصلاحية',
        'confirm_delete': 'هل أنت متأكد من الحذف؟', 'stats': 'إحصائيات', 'total_users': 'المستخدمون',
        'total_quizzes': 'المسابقات', 'total_questions': 'الأسئلة', 'total_attempts': 'المحاولات',
        'online_users': 'المستخدمون المتواجدون الآن', 'recent_activity': 'النشاط الأخير', 'no_data': 'لا توجد بيانات',
    },
    'fr': {
        'app_name': 'Plateforme Tamayuz', 'home': 'Accueil', 'login': 'Connexion', 'register': 'S\'inscrire',
        'logout': 'Déconnexion', 'dashboard': 'Mon espace', 'leaderboard': 'Classement', 'admin_panel': 'Administration',
        'welcome_title': 'Entraînez-vous et progressez', 'welcome_sub': 'Une variété de quiz dans différents domaines, testez vos connaissances et comparez vos résultats',
        'all_categories': 'Toutes les catégories', 'questions': 'questions', 'minutes': 'min', 'difficulty': 'Difficulté',
        'easy': 'Facile', 'medium': 'Moyen', 'hard': 'Difficile', 'start_quiz': 'Commencer', 'best_score': 'Meilleur score',
        'top_players': 'Meilleurs joueurs', 'points': 'points', 'no_quizzes': 'Aucun quiz disponible pour le moment',
        'username': 'Nom d\'utilisateur', 'email': 'Email', 'password': 'Mot de passe',
        'already_account': 'Déjà un compte ?', 'no_account': 'Pas de compte ?', 'question': 'Question',
        'of': 'sur', 'next': 'Suivant', 'previous': 'Précédent', 'finish': 'Terminer le quiz', 'time_left': 'Temps restant',
        'your_score': 'Votre score', 'correct_answers': 'Réponses correctes', 'wrong_answers': 'Réponses incorrectes',
        'time_taken': 'Temps écoulé', 'review_answers': 'Revoir les réponses', 'back_home': 'Retour à l\'accueil',
        'retry_quiz': 'Réessayer', 'my_history': 'Historique de mes quiz', 'no_results_yet': 'Aucun quiz passé pour le moment',
        'date': 'Date', 'quiz': 'Quiz', 'score': 'Score', 'percentage': 'Pourcentage', 'view': 'Voir',
        'rank': 'Rang', 'player': 'Joueur', 'total_points': 'Total des points', 'manage_categories': 'Gérer les catégories',
        'manage_quizzes': 'Gérer les quiz', 'manage_users': 'Gérer les utilisateurs', 'all_results': 'Tous les résultats',
        'add': 'Ajouter', 'edit': 'Modifier', 'delete': 'Supprimer', 'save': 'Enregistrer', 'cancel': 'Annuler', 'name': 'Nom',
        'actions': 'Actions', 'add_quiz': 'Ajouter un quiz', 'title': 'Titre', 'description': 'Description',
        'category': 'Catégorie', 'duration': 'Durée (min)', 'published': 'Publié', 'manage_questions': 'Gérer les questions',
        'add_question': 'Ajouter une question', 'import_csv': 'Importer un CSV', 'question_text': 'Texte de la question',
        'choices': 'Choix', 'correct_choice': 'Bonne réponse', 'explanation': 'Explication (optionnel)',
        'download_sample': 'Télécharger un exemple CSV', 'choose_file': 'Choisir un fichier CSV', 'import': 'Importer',
        'admin': 'Admin', 'user': 'Utilisateur', 'make_admin': 'Rendre admin', 'remove_admin': 'Retirer les droits',
        'confirm_delete': 'Confirmer la suppression ?', 'stats': 'Statistiques', 'total_users': 'Utilisateurs',
        'total_quizzes': 'Quiz', 'total_questions': 'Questions', 'total_attempts': 'Tentatives',
        'online_users': 'Utilisateurs en ligne', 'recent_activity': 'Activité récente', 'no_data': 'Aucune donnée',
    }
}


@app.context_processor
def inject_globals():
    lang = session.get('lang', 'ar')
    dir_ = 'rtl' if lang == 'ar' else 'ltr'
    t = TRANSLATIONS.get(lang, TRANSLATIONS['ar'])
    return dict(lang=lang, dir=dir_, t=t, current_user=current_user)


@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in ('ar', 'fr'):
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))


# ---------------------------------------------------------------------------
# Public / user routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    categories = Category.query.all()
    quizzes = Quiz.query.filter_by(is_published=True).order_by(Quiz.created_at.desc()).all()
    cat_filter = request.args.get('category', type=int)
    if cat_filter:
        quizzes = [q for q in quizzes if q.category_id == cat_filter]
    top_users = sorted(User.query.filter_by(is_admin=False).all(),
                        key=lambda u: u.total_points, reverse=True)[:5]
    return render_template('index.html', categories=categories, quizzes=quizzes, top_users=top_users,
                            active_category=cat_filter)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('يرجى تعبئة جميع الحقول / Veuillez remplir tous les champs', 'danger')
            return redirect(url_for('register'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('اسم المستخدم أو البريد مستخدم مسبقًا / Nom d\'utilisateur ou email déjà utilisé', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('تم إنشاء الحساب بنجاح / Compte créé avec succès', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('بيانات الدخول غير صحيحة / Identifiants incorrects', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz_intro(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz_intro.html', quiz=quiz)


@app.route('/quiz/<int:quiz_id>/take')
@login_required
def quiz_take(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if not quiz.questions:
        flash('لا توجد أسئلة في هذه المسابقة / Aucune question dans ce quiz', 'warning')
        return redirect(url_for('index'))
    questions_data = []
    for q in quiz.questions:
        questions_data.append({
            'id': q.id,
            'text': q.text,
            'choices': [{'id': c.id, 'text': c.text} for c in q.choices]
        })
    return render_template('quiz_take.html', quiz=quiz, questions_json=json.dumps(questions_data, ensure_ascii=False))


@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def quiz_submit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    data = request.get_json(force=True)
    answers_payload = data.get('answers', {})  # {question_id: choice_id}
    time_taken = int(data.get('time_taken', 0))

    correct_count = 0
    result = Result(user_id=current_user.id, quiz_id=quiz.id,
                     total_questions=len(quiz.questions), time_taken_seconds=time_taken)
    db.session.add(result)
    db.session.flush()

    for q in quiz.questions:
        choice_id = answers_payload.get(str(q.id))
        is_correct = False
        if choice_id:
            choice = Choice.query.get(int(choice_id))
            is_correct = bool(choice and choice.is_correct)
        if is_correct:
            correct_count += 1
        ans = Answer(result_id=result.id, question_id=q.id,
                      choice_id=int(choice_id) if choice_id else None, is_correct=is_correct)
        db.session.add(ans)

    total = len(quiz.questions)
    percentage = round((correct_count / total) * 100, 1) if total else 0
    result.correct_count = correct_count
    result.percentage = percentage
    result.score = correct_count * 10
    db.session.commit()

    return jsonify({'result_id': result.id})


@app.route('/result/<int:result_id>')
@login_required
def result_detail(result_id):
    result = Result.query.get_or_404(result_id)
    if result.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('quiz_result.html', result=result)


@app.route('/dashboard')
@login_required
def dashboard():
    results = Result.query.filter_by(user_id=current_user.id).order_by(Result.created_at.desc()).all()
    return render_template('dashboard.html', results=results)


@app.route('/leaderboard')
def leaderboard():
    users = sorted(User.query.filter_by(is_admin=False).all(), key=lambda u: u.total_points, reverse=True)
    return render_template('leaderboard.html', users=users)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # عد المستخدمين المتواجدين حالياً (في آخر 5 دقائق)
    from datetime import timedelta
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    online_users = db.session.query(db.func.count(db.distinct(User.id))).join(Result).filter(
        Result.created_at >= five_minutes_ago
    ).scalar() or 0
    
    stats = {
        'users': User.query.filter_by(is_admin=False).count(),
        'quizzes': Quiz.query.count(),
        'questions': Question.query.count(),
        'results': Result.query.count(),
        'online_users': online_users,
    }
    recent_results = Result.query.order_by(Result.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_results=recent_results)


# --- Categories ---
@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_categories():
    if request.method == 'POST':
        cat = Category(name_ar=request.form['name_ar'], name_fr=request.form['name_fr'],
                        icon=request.form.get('icon', 'bi-collection'))
        db.session.add(cat)
        db.session.commit()
        flash('تمت إضافة التصنيف / Catégorie ajoutée', 'success')
        return redirect(url_for('admin_categories'))
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash('تم الحذف / Supprimé', 'success')
    return redirect(url_for('admin_categories'))


# --- Quizzes ---
@app.route('/admin/quizzes')
@login_required
@admin_required
def admin_quizzes():
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('admin/quizzes.html', quizzes=quizzes)


@app.route('/admin/quizzes/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_quiz_new():
    categories = Category.query.all()
    if request.method == 'POST':
        quiz = Quiz(
            title_ar=request.form['title_ar'], title_fr=request.form['title_fr'],
            description_ar=request.form.get('description_ar', ''),
            description_fr=request.form.get('description_fr', ''),
            category_id=int(request.form['category_id']),
            difficulty=request.form.get('difficulty', 'medium'),
            duration_minutes=int(request.form.get('duration_minutes', 10)),
            is_published='is_published' in request.form
        )
        db.session.add(quiz)
        db.session.commit()
        flash('تم إنشاء المسابقة / Quiz créé', 'success')
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz.id))
    return render_template('admin/quiz_form.html', quiz=None, categories=categories)


@app.route('/admin/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_quiz_edit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    categories = Category.query.all()
    if request.method == 'POST':
        quiz.title_ar = request.form['title_ar']
        quiz.title_fr = request.form['title_fr']
        quiz.description_ar = request.form.get('description_ar', '')
        quiz.description_fr = request.form.get('description_fr', '')
        quiz.category_id = int(request.form['category_id'])
        quiz.difficulty = request.form.get('difficulty', 'medium')
        quiz.duration_minutes = int(request.form.get('duration_minutes', 10))
        quiz.is_published = 'is_published' in request.form
        db.session.commit()
        flash('تم التحديث / Mis à jour', 'success')
        return redirect(url_for('admin_quizzes'))
    return render_template('admin/quiz_form.html', quiz=quiz, categories=categories)


@app.route('/admin/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_quiz_delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('تم الحذف / Supprimé', 'success')
    return redirect(url_for('admin_quizzes'))


# --- Questions ---
@app.route('/admin/quizzes/<int:quiz_id>/questions')
@login_required
@admin_required
def admin_quiz_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('admin/questions.html', quiz=quiz)


@app.route('/admin/quizzes/<int:quiz_id>/questions/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_question_new(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        q = Question(quiz_id=quiz.id, text=request.form['text'],
                     explanation=request.form.get('explanation', ''))
        db.session.add(q)
        db.session.flush()
        choice_texts = request.form.getlist('choice_text')
        correct_index = int(request.form.get('correct_index', 0))
        for i, ctext in enumerate(choice_texts):
            if ctext.strip():
                db.session.add(Choice(question_id=q.id, text=ctext.strip(), is_correct=(i == correct_index)))
        db.session.commit()
        flash('تمت إضافة السؤال / Question ajoutée', 'success')
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz.id))
    return render_template('admin/question_form.html', quiz=quiz, question=None)


@app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_question_edit(question_id):
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz
    if request.method == 'POST':
        question.text = request.form['text']
        question.explanation = request.form.get('explanation', '')
        for c in list(question.choices):
            db.session.delete(c)
        db.session.flush()
        choice_texts = request.form.getlist('choice_text')
        correct_index = int(request.form.get('correct_index', 0))
        for i, ctext in enumerate(choice_texts):
            if ctext.strip():
                db.session.add(Choice(question_id=question.id, text=ctext.strip(), is_correct=(i == correct_index)))
        db.session.commit()
        flash('تم التحديث / Mis à jour', 'success')
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz.id))
    return render_template('admin/question_form.html', quiz=quiz, question=question)


@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_question_delete(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('تم الحذف / Supprimé', 'success')
    return redirect(url_for('admin_quiz_questions', quiz_id=quiz_id))


# --- Import CSV ---
@app.route('/admin/quizzes/<int:quiz_id>/import', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_quiz_import(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or file.filename == '':
            flash('يرجى اختيار ملف CSV / Veuillez choisir un fichier CSV', 'danger')
            return redirect(url_for('admin_quiz_import', quiz_id=quiz.id))
        try:
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
            reader = csv.DictReader(stream)
            count = 0
            for row in reader:
                text = (row.get('question') or row.get('question_text') or '').strip()
                if not text:
                    continue
                explanation = (row.get('explanation') or '').strip()
                q = Question(quiz_id=quiz.id, text=text, explanation=explanation)
                db.session.add(q)
                db.session.flush()
                correct_index = int(row.get('correct_index', 0) or 0)
                choice_keys = [k for k in ['choice1', 'choice2', 'choice3', 'choice4', 'choice5', 'choice6']
                               if row.get(k)]
                for i, key in enumerate(choice_keys):
                    ctext = row.get(key, '').strip()
                    if ctext:
                        db.session.add(Choice(question_id=q.id, text=ctext, is_correct=(i == correct_index)))
                count += 1
            db.session.commit()
            flash(f'تم استيراد {count} سؤال بنجاح / {count} questions importées avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في الاستيراد / Erreur d\'importation: {e}', 'danger')
        return redirect(url_for('admin_quiz_questions', quiz_id=quiz.id))
    return render_template('admin/import.html', quiz=quiz)


@app.route('/admin/import-sample-csv')
@login_required
@admin_required
def admin_sample_csv():
    from flask import Response
    sample = ("question,choice1,choice2,choice3,choice4,correct_index,explanation\n"
              '"ما هي عاصمة فرنسا؟","باريس","لندن","روما","مدريد",0,"باريس هي عاصمة فرنسا"\n'
              '"Quelle est la capitale de la France?","Paris","Londres","Rome","Madrid",0,"Paris est la capitale"\n')
    return Response(sample, mimetype='text/csv',
                     headers={'Content-Disposition': 'attachment;filename=sample_questions.csv'})


# --- Users management ---
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('لا يمكنك تعديل صلاحياتك الخاصة / Vous ne pouvez pas modifier vos propres droits', 'warning')
        return redirect(url_for('admin_users'))
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك / Vous ne pouvez pas supprimer votre compte', 'warning')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('تم الحذف / Supprimé', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/results')
@login_required
@admin_required
def admin_results():
    results = Result.query.order_by(Result.created_at.desc()).limit(200).all()
    return render_template('admin/results.html', results=results)


# ---------------------------------------------------------------------------
def create_default_admin():
    if not User.query.filter_by(is_admin=True).first():
        admin = User(username='admin', email='admin@qcm.local', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('==> Default admin created: username=admin / password=admin123')


with app.app_context():
    db.create_all()
    create_default_admin()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
