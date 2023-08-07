from apscheduler.schedulers.background import BackgroundScheduler
# from app.features.crypto import ping

job_defaults = {
    'coalesce': False,
    'max_instances': 20
}

sched = BackgroundScheduler(job_defaults=job_defaults)
# sched.add_job(ping, 'interval', seconds=3)
