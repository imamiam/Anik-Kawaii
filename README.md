Created on my personal laptop, pushed for lab use

LAPTOP
if __name__ == "__main__":
    run_simple("127.0.0.1", 5048, app, use_reloader=True)

  gunicorn --bind 127.0.0.1:5048 app:app


 LAB
  if __name__ == "__main__":
    run_simple("172.17.100.15", 5048, app, use_reloader=True)

  gunicorn --bind 172.17.100.15:5048 app:app
