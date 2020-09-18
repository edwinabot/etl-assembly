FROM python:3.8

WORKDIR /usr/src/app

COPY . .

RUN python -m pip install --upgrade pip

RUN python -m pip install pipenv

RUN pipenv lock -r > requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "beta.py" ]
