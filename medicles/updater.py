from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from medicles import services

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(services.update_db, 'interval', minutes=1)
    print("Updater starts")
    scheduler.start()
