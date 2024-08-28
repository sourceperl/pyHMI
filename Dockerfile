### docker setup ###
# sudo apt install docker.io
# sudo usermod -aG docker $USER
# sudo reboot

### run test ###
# docker build -t pytest . && docker run -v $(pwd):/app --rm -it pytest

FROM python:3.8

# update pip at system level
RUN pip install --root-user-action=ignore --upgrade pip

# avoid to run as root
RUN useradd -m user
USER user
WORKDIR /home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# install pytest and requirements for user
RUN pip install --user pytest
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# project mount point
WORKDIR /app
ENTRYPOINT ["./docker-entrypoint.sh"]
