FROM python:3.12-slim
WORKDIR /opt/project
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY dbt ./dbt
RUN useradd --create-home analyst && mkdir data artifacts && chown -R analyst:analyst /opt/project
USER analyst
ENV SAAS_ROOT=/opt/project
CMD ["saas", "demo"]
