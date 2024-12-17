from app import app, db  # นำเข้า app และ db จาก app.py

# ใช้ app.app_context() เพื่อเปิด application context
with app.app_context():
    db.create_all()  # คำสั่งนี้จะสร้างฐานข้อมูลและตารางที่จำเป็น
    print("Database created!")
