#PomodoroApp
FROM python:3.12.13-alpine3.22
#Carpeta de trabajo, lugar donde se pone los ejecutables.
WORKDIR /app

COPY pomodoro_app.py /app/

RUN pip install --no-cache-dir flask

EXPOSE 80

CMD [ "python3", "pomodoro_app.py" ]
