import os
import sys
import subprocess
import time
import threading

def run_flask_service():
    print("[INFO] Starting Flask AI Microservice on http://127.0.0.1:5001 ...")
    flask_app = os.path.join(os.path.dirname(__file__), 'flask_ai_service', 'app.py')
    subprocess.run([sys.executable, flask_app])

def main():
    print("==================================================")
    print("[ExamVault] PYQ & Test Series Platform Starter")
    print(" Architecture: Django + SQLite + Flask AI Service")
    print("==================================================")

    # 1. Run migrations
    print("\n1. Applying Database Migrations (SQLite)...")
    subprocess.run([sys.executable, 'manage.py', 'makemigrations'])
    subprocess.run([sys.executable, 'manage.py', 'migrate'])

    # 2. Seed initial data
    print("\n2. Checking and Seeding Initial Data...")
    subprocess.run([sys.executable, 'seed_data.py'])

    # 3. Start Flask AI Microservice in background thread
    print("\n3. Launching Flask AI Engine...")
    t = threading.Thread(target=run_flask_service, daemon=True)
    t.start()
    time.sleep(2)

    # 4. Start Django Server
    print("\n4. Starting Django Web Application on http://127.0.0.1:8005 ...")
    print("==================================================")
    print("[CREDENTIALS] Admin:   Username: admin   | Password: admin123")
    print("[CREDENTIALS] Student: Username: student | Password: student123")
    print("==================================================")
    
    subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8005'])

if __name__ == '__main__':
    main()
