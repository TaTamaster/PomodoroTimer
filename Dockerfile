#PomodoroApp
FROM python:3.12.13-alpine3.22
#Carpeta de trabajo, lugar donde se pone los ejecutables.
WORKDIR /app
#Copia de script en carpeta de trabajo.
COPY pomodoro_app.py /app/
#Instalación dependencias.
RUN pip install --no-cache-dir flask
#Muestra puerto expuesto.
EXPOSE 80
#Ejecución de Script.
CMD [ "python3", "pomodoro_app.py" ]
