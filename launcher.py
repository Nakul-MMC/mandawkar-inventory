import sys
import os
import webbrowser
from threading import Timer
from app import app, db

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Determine if we are running as a script or frozen exe
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (PyInstaller)
        # The executable is located at sys.executable
        # We want the database to be stored NEXT to the executable, not inside the temp folder
        base_dir = os.path.dirname(sys.executable)
        
        # Create a defined 'data' folder for the database
        data_dir = os.path.join(base_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        db_path = os.path.join(data_dir, 'db.sqlite3')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print(f"Running in Desktop Mode. Database: {db_path}")
    else:
        # Running as normal python script
        print("Running in Development Mode.")

    # Re-init db with new config if needed (though init_app is usually lazy, verification is good)
    # But since app.py already ran init_app, we just changed the config. 
    # SQLAlchemy might have already connected.
    # To be safe, we might need to enforce this config before app import, 
    # but app import is circular. 
    # Instead, let's rely on Flask's request-time connection. 
    # But create_all runs at startup.
    
    # Actually, simpler approach: 
    # In app.py, we only did `db.create_all()` inside `if __name__ == "__main__"` or global?
    # In `app.py`, `with app.app_context(): db.create_all()` is at the top level.
    # This means it runs ON IMPORT. That's a problem if we want to change the DB path here.
    # However, create_all uses the current config. If we import app, it runs immediately.
    # We can't easily change the config AFTER import if create_all has already run against the default DB.
    
    # Correct Fix: We should move the create_all logic in this launcher, 
    # OR trigger it again after changing config.
    
    with app.app_context():
        db.create_all()
        
        # Ensure Admin Exists (In case this is a fresh install in the new 'data' folder)
        from models import User
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Seeded 'admin' user for Desktop App.")

    # Timer to open browser after server starts
    Timer(1.5, open_browser).start()
    
    # Run App
    app.run(host="127.0.0.1", port=5000, debug=False)
