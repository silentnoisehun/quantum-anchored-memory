FROM python:3.10-slim as python

RUN pip install qiskit qiskit-ibm-runtime numpy matplotlib

RUN apt-get update && apt-get install -y curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app
COPY . .

WORKDIR /app/rust
RUN cargo build --release

WORKDIR /app
CMD ["python3", "qam_benchmark.py", "--token", "${IBM_QUANTUM_TOKEN}", "--backend", "ibm_heron"]
