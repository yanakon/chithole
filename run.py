import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from waitress import serve

# สร้างแอป Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# กำหนดเส้นทางฐานข้อมูลแบบ relative path
basedir = os.path.abspath(os.path.dirname(__file__))  # เส้นทางของไฟล์ปัจจุบัน
db_path = os.path.join(basedir, 'instance', 'beer-database.db')  # ตั้งฐานข้อมูลในโฟลเดอร์ 'instance'

# กำหนดค่า SQLAlchemy URI สำหรับฐานข้อมูล SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # ใช้ path ที่กำหนดในตัวแปร db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# กำหนด db และ migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# โมเดลสำหรับข้อมูลเบียร์
class Beer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bands = db.Column(db.String(50), nullable=False)
    beer = db.Column(db.String(50), nullable=False)
    abv = db.Column(db.Float, nullable=False)
    tap_number = db.Column(db.Integer, unique=True, nullable=True)  # เพิ่มคอลัมน์ tap_number
    is_visible = db.Column(db.Boolean, default=True)  # เพิ่มคอลัมน์ is_visible


# ฟังก์ชันซ่อนแสดงเบียร์
@app.route('/toggle-visibility/<int:id>', methods=['POST'])
def toggle_visibility(id):
    beer = Beer.query.get(id)
    if beer:
        beer.is_visible = not beer.is_visible
        db.session.commit()

        # ส่งข้อความแจ้งเตือน
        if beer.is_visible:
            flash(f"ทำการแสดง {beer.beer} แล้ว", 'success')  # ข้อความเมื่อแสดง
        else:
            flash(f"ทำการซ่อน {beer.beer} แล้ว", 'danger')  # ข้อความเมื่อซ่อน
    return redirect(url_for('admin'))


# ฟังก์ชันจัดการเบียร์
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        beer_ids = request.form.getlist('beer_ids[]')  # รับ ID เบียร์จากฟอร์ม
        updated_beers = []  # สร้างลิสต์เพื่อเก็บเบียร์ที่มีการอัปเดต

        for beer_id in beer_ids:  # ลบการอัปเดต beer_tab
            beer = Beer.query.get(beer_id)  # ดึงข้อมูลเบียร์จาก ID
            if beer:  # ตรวจสอบว่าเบียร์มีอยู่จริง
                updated_beers.append(f"Beer updated: {beer.beer}")  # แค่เก็บข้อความว่าได้อัปเดตเบียร์

        if updated_beers:
            try:
                db.session.commit()  # บันทึกการเปลี่ยนแปลงทั้งหมด
                for message in updated_beers:
                    flash(message, 'success')  # แสดงข้อความแจ้งเตือนแต่ละอัน
            except IntegrityError as e:
                db.session.rollback()  # ยกเลิกการเปลี่ยนแปลงถ้ามีปัญหา
                flash(f"Error updating beer: {str(e)}", 'danger')

        return redirect(url_for('admin'))  # รีเฟรชหน้าจัดการเบียร์
    
    # ดึงข้อมูลทั้งหมดของเบียร์และเรียงตาม tap_number
    beers = Beer.query.order_by(Beer.tap_number).all()
    return render_template('admin.html', beers=beers)


# เพิ่ม route สำหรับการดึงข้อมูลเบียร์ในรูปแบบ HTML
@app.route('/get-beers', methods=['GET'])
def get_beers():
    beers = Beer.query.all()  # ดึงข้อมูลเบียร์ทั้งหมด
    return render_template('beer_table_rows.html', beers=beers)


# Route สำหรับแสดงเบียร์ 16 แท็บ
@app.route('/beer-menu')
def beer_menu():
    beers = Beer.query.order_by(Beer.tap_number).all()  # ดึงเบียร์ทั้งหมด
    return render_template('beer_menu.html', beers=beers, start=1, end=16)


# Route สำหรับแสดงเบียร์ตามแท็บ 1-6
@app.route('/beer-menu-1-6')
def beer_menu_1_6():
    beers_1_6 = Beer.query.filter(Beer.tap_number.between(1, 6)).order_by(Beer.tap_number).all()
    return render_template('beer_menu.html', beers=beers_1_6, start=1, end=6)


# Route สำหรับแสดงเบียร์ตามแท็บ 7-11
@app.route('/beer-menu-7-11')
def beer_menu_7_11():
    beers_7_11 = Beer.query.filter(Beer.tap_number.between(7, 11)).order_by(Beer.tap_number).all()
    return render_template('beer_menu.html', beers=beers_7_11, start=7, end=11)


# Route สำหรับแสดงเบียร์ตามแท็บ 12-16
@app.route('/beer-menu-12-16')
def beer_menu_12_16():
    beers_12_16 = Beer.query.filter(Beer.tap_number.between(12, 16)).order_by(Beer.tap_number).all()
    return render_template('beer_menu.html', beers=beers_12_16, start=12, end=16)


# หน้าแรกแสดงข้อมูลเบียร์
@app.route('/')
def index():
    beers = Beer.query.all()  # ดึงข้อมูลเบียร์ทั้งหมดจากฐานข้อมูล
    return render_template('admin.html', beers=beers)


# หน้าเพิ่มเบียร์
@app.route('/add-beer', methods=['GET', 'POST'])
def add_beer():
    if request.method == 'POST':
        data = request.form
        new_beer = Beer(
            bands=data['bands'],
            beer=data['beer'],
            abv=data['abv']
        )
        db.session.add(new_beer)
        db.session.commit()

        # ส่งข้อความแจ้งเตือนเมื่อเพิ่มเบียร์สำเร็จ
        flash('เพิ่มเบียร์ใหม่เรียบร้อยแล้ว', 'success')

        return redirect(url_for('index'))  # กลับไปที่หน้าแสดงข้อมูลเบียร์
    
    return render_template('add_beer.html')


# หน้าแก้ไขเบียร์
@app.route('/edit-beer/<int:id>', methods=['GET', 'POST'])
def edit_beer(id):
    beer = Beer.query.get_or_404(id)

    if request.method == 'POST':
        data = request.form
        beer.bands = data['bands']
        beer.beer = data['beer']
        beer.abv = data['abv']
        tap_number = data['tap_number']

        # กำหนดให้ tap_number เป็น None หากไม่ได้กรอกหมายเลขแท็บ
        if tap_number == '':
            beer.tap_number = None
        else:
            try:
                tap_number = int(tap_number)

                if tap_number < 1 or tap_number > 16:
                    flash("หมายเลขแท็บต้องอยู่ระหว่าง 1 ถึง 16", "danger")
                    return redirect(url_for('edit_beer', id=beer.id))

                # ตรวจสอบว่า tap_number ซ้ำกับเบียร์อื่นหรือไม่
                existing_beer = Beer.query.filter_by(tap_number=tap_number).first()
                if existing_beer and existing_beer.id != beer.id:
                    flash(f"แท็บหมายเลข {tap_number} ถูกไปใช้แล้ว กรุณาเปลี่ยนแท็บ", "danger")
                    return redirect(url_for('edit_beer', id=beer.id))  # Redirect ไปยังหน้า edit_beer

                # อัปเดต tap_number ให้กับเบียร์
                beer.tap_number = tap_number

            except ValueError:
                flash("หมายเลขแท็บต้องเป็นตัวเลข", "danger")
                return redirect(url_for('edit_beer', id=beer.id))  # Redirect ไปยังหน้า edit_beer

        try:
            db.session.commit()  # บันทึกการเปลี่ยนแปลง
            flash("อัปเดตเบียร์สำเร็จ", "success")
            return redirect(url_for('index'))
        except IntegrityError as e:
            db.session.rollback()  # ยกเลิกการเปลี่ยนแปลงหากเกิดข้อผิดพลาด
            flash("เกิดข้อผิดพลาดในการอัปเดตเบียร์", "danger")

    return render_template('edit_beer.html', beer=beer)


# ลบเบียร์
@app.route('/delete-beer/<int:id>', methods=['GET'])
def delete_beer(id):
    beer = Beer.query.get_or_404(id)
    db.session.delete(beer)
    db.session.commit()
    return redirect(url_for('index'))  # กลับไปที่หน้าแสดงข้อมูลเบียร์


# รันแอปด้วย waitress
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)  # ใช้ waitress รันแอปบน port 5000
