import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "sadarah_training_secure_production_key"

# إعدادات اتصال Supabase (تُؤخذ من متغيرات البيئة في Vercel أو تُكتب هنا مؤقتاً)
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'ضع_رابط_Supabase_هنا')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'ضع_مفتاح_anon_key_هنا')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعدادات التخزين السحابي Cloudinary للوسائط والواجبات
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'ضع_cloud_name_هنا'),
  api_key = os.environ.get('CLOUDINARY_API_KEY', 'ضع_api_key_هنا'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET', 'ضع_api_secret_هنا')
)

@app.route('/')
def index():
    # جلب الدورات من جدول courses في Supabase
    try:
        response = supabase.table('courses').select('*').execute()
        courses = response.data
    except Exception as e:
        courses = []
    return render_template('index.html', courses=courses)

@app.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course_details(course_id):
    # جلب تفاصيل الدورة المحددة
    try:
        course_res = supabase.table('courses').select('*').eq('id', course_id).execute()
        course = course_res.data[0] if course_res.data else None
    except:
        course = None

    if not course:
        return "الدورة غير موجودة", 404
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'register':
            student_name = request.form.get('student_name')
            student_phone = request.form.get('student_phone')
            # حفظ طلب التسجيل في جدول registrations في Supabase
            supabase.table('registrations').insert({
                'course_id': course_id,
                'student_name': student_name,
                'student_phone': student_phone
            }).execute()
            flash('تم إرسال طلب تسجيلك بنجاح! سنتواصل معك عبر واتساب.', 'success')
            
        elif form_type == 'assignment':
            student_name = request.form.get('student_name')
            file = request.files.get('assignment_file')
            if file:
                # رفع واجب الطالب (PDF أو Word) إلى Cloudinary والحصول على رابطه السحابي
                upload_res = cloudinary.uploader.upload(file, resource_type="auto")
                file_url = upload_res.get('secure_url')
                
                # حفظ بيانات الواجب في جدول assignments في Supabase
                supabase.table('assignments').insert({
                    'course_id': course_id,
                    'student_name': student_name,
                    'file_url': file_url
                }).execute()
                flash('تم رفع الواجب وإرساله للمدرب بنجاح!', 'success')
                
        return redirect(url_for('course_details', course_id=course_id))

    return render_template('course_details.html', course=course)

# لوحة التحكم الإدارية (التحكم الكامل 100%)
@app.route('/admin-sadarah-panel')
def admin_panel():
    try:
        courses = supabase.table('courses').select('*').execute().data
        registrations = supabase.table('registrations').select('*').execute().data
        assignments = supabase.table('assignments').select('*').execute().data
    except:
        courses, registrations, assignments = [], [], []

    return render_template('admin.html', courses=courses, registrations=registrations, assignments=assignments)

@app.route('/admin/add_course', methods=['POST'])
def add_course():
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    
    media_file = request.files.get('media_file')
    media_url = ""
    if media_file:
        # رفع وسائط الدورة (فيديو، صورة، PDF) للسحابة
        upload_res = cloudinary.uploader.upload(media_file, resource_type="auto")
        media_url = upload_res.get('secure_url')
    
    # إدخال الدورة الجديدة في جدول courses في Supabase
    supabase.table('courses').insert({
        'title': title,
        'description': description,
        'price': price,
        'media_url': media_url
    }).execute()
    
    flash('تم إضافة ونشر الدورة بنجاح!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_course/<int:course_id>')
def delete_course(course_id):
    supabase.table('courses').delete().eq('id', course_id).execute()
    flash('تم حذف الدورة بنجاح.', 'info')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
