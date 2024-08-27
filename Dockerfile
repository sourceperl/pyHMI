# sudo apt install docker.io
# sudo usermod -aG docker $USER
# sudo reboot

# build: docker build -t pytest .
#   run: docker run -v $(pwd):/app --rm -it pytest

FROM python:3.8

WORKDIR /app

RUN pip install -U pip
RUN pip install pytest

CMD ["bash"]
