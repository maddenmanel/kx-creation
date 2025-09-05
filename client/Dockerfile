FROM python:3.10

# Solve opencv dependency issue
COPY sources.list /etc/apt/sources.list
RUN apt-get -y update
RUN apt-get install -y libzbar-dev libgl1-mesa-glx libjemalloc-dev
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy the relevant files
WORKDIR /app
COPY requirements.txt .

# Install requirements
RUN pip3 install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the relevant files
COPY . .

WORKDIR /app