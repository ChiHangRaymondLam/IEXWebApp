# Name: Chi Hang Lam
# Student ID.: 17026690
# 159352 Assignment 1

FROM python:3.8.5
RUN pip install --compile --install-option="--with-openssl" pycurl
RUN pip install pandas
RUN pip install numpy
# RUN apk add --no-cache --virtual .build-dependencies build-base curl-dev \
#     && pip install pycurl \
#     && apk del .build-dependencies

COPY . /src
WORKDIR /src

# Run Assignment 1 in Docker container for testing
#EXPOSE 8080
#CMD python server3.py 8080

# Deploy Assignment 1 container on Heroku
CMD python server3.py $PORT