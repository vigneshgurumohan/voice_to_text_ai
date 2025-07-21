from celery import Celery

BROKER_URL = "rediss://default:AebFAAIjcDFiNjZlOThlNjU5NmU0ZjIxODZhOGZiMjliZDU1MDM5NXAxMA@pleasant-fly-59077.upstash.io:6379/0?ssl_cert_reqs=CERT_NONE"
app = Celery("demo", broker=BROKER_URL, backend=BROKER_URL)

@app.task
def add(x, y):
    return x + y 