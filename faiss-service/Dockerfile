From plippe/faiss-web-service

COPY requirements.txt /opt/faiss-web-service/requirements.txt
RUN conda install -y -c conda-forge --file /opt/faiss-web-service/requirements.txt

COPY bin /opt/faiss-web-service/bin
COPY src /opt/faiss-web-service/src

WORKDIR /opt/faiss-web-service

ENTRYPOINT ["/opt/faiss-web-service/bin/faiss_web_service.sh"]