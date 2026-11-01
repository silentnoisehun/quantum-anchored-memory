FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cargo build --release --manifest-path rust/Cargo.toml

# Reads IBM_QUANTUM_TOKEN from container environment if set, otherwise runs
# zero-quota local StatevectorSampler verification.
CMD ["python3", "-m", "src.qam_benchmark", "--backend", "ibm_kingston"]
