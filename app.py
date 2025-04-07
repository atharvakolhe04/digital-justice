import os
import subprocess
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run both scripts in background
    subprocess.Popen(['python', 'sos_alerts_location.py'])

    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
