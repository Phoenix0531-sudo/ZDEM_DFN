FROM python:3.11-slim

WORKDIR /app

# Install the package itself (deps resolved from pyproject) — keeps
# runtime metadata (version, entry point) consistent with the wheel.
COPY pyproject.toml README.md ./
COPY zdem_dfn/ ./zdem_dfn/
RUN pip install --no-cache-dir .

# Specimens are mounted at runtime, not baked into the image:
#   docker run --rm -v /path/to/specimens:/data zdem-dfn --dirs /data/spec1
VOLUME ["/data"]
ENTRYPOINT ["python", "-m", "zdem_dfn"]
CMD ["--help"]
