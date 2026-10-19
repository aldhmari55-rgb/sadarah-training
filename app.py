import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    courses = []
    if supabase:
        response = supabase.table('courses').select('*').execute()
        courses = response.data
    return render_template('index.html', courses=courses)

@app.route('/course/<int:course_id>')
def course_details(course_id):
    if not supabase:
        return "Supabase not configured", 500
    course_res = supabase.table('courses').select('*').eq('id', course_id).execute()
    if not course_res.data:
        return "الدورة غير موجودة", 404
    course = course_res.data[0]
    
    registrations_res = supabase.table('registrations').select('*').eq('course_id', course_id).execute()
    assignments_res = supabase.table('assignments').select('*').eq('course_id', course_id).execute()
    
    return render_template('course_details.html', 
                           course=course, 
                           registrations=registrations_res.data, 
                           assignments=assignments_res.data)

@app.route('/register', methods=['POST'])
def register():
    if not supabase:
        return "Supabase not configured", 500
    course_id = request.form.get('course_id')
    student_name = request.form.get('student_name')
    phone = request.form.get('phone')
    
    supabase.table('registrations').insert({
        'course_id': course_id,
        'student_name': student_name,
        'phone': phone
    }).execute()
    
    return redirect(url_for('course_details', course_id=course_id))

@app.route('/submit_assignment', methods=['POST'])
def submit_assignment():
    if not supabase:
        return "Supabase not configured", 500
    course_id = request.form.get('course_id')
    student_name = request.form.get('student_name')
    file_url = request.form.get('file_url')  # رابط الملف أو الواجب
    
    supabase.table('assignments').insert({
        'course_id': course_id,
        'student_name': student_name,
        'file_url': file_url
    }).execute()
    
    return redirect(url_for('course_details', course_id=course_id))

@app.route('/admin')
def admin():
    courses = []
    registrations = []
    assignments = []
    if supabase:
        courses = supabase.table('courses').select('*').execute().data
        registrations = supabase.table('registrations').select('*').execute().data
        assignments = supabase.table('assignments').select('*').execute().data
    return render_template('admin.html', courses=courses, registrations=registrations, assignments=assignments)

@app.route('/admin/add_course', methods=['POST'])
def add_course():
    if not supabase:
        return "Supabase not configured", 500
    title = request.form.get('title')
    description = request.form.get('description')
    image_url = request.form.get('image_url')
    video_url = request.form.get('video_url')
    pdf_url = request.form.get('pdf_url')
    
    supabase.table('courses').insert({
        'title': title,
        'description': description,
        'image_url': image_url,
        'video_url': video_url,
        'pdf_url': pdf_url
    }).execute()
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
