FROM continuumio/miniconda

COPY dash.yml /tmp/dash.yml
RUN conda env create -f /tmp/dash.yml && conda clean -a -y