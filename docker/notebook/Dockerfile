# Start from the base jupyterhub image.
ARG BASE_CONTAINER=jupyter/base-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Christopher Woods <Christopher.Woods@bristol.ac.uk>, Lester Hedges <lester.hedges@gmail.com>"

# Variables holding links to download dependencies
ENV AMBER_DOWNLOAD=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/_4HhZazLxgkcRLxZbmGPuGV0ciotx3V7kDeqh8fgy7Y/n/hugs/b/notebook/o/amber.tar.bz2
ENV GROMACS_DOWNLOAD=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/HmW0HXTrRsvOPz9uHucA0hDsGdyNmnoe1jfcdoHiZJk/n/hugs/b/notebook/o/gromacs.tar.bz2
ENV PLUMED_DOWNLOAD=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/peJ15kXeAtNpRbgNvAcjpyx04qLKd4GsbEzuL5VNbSM/n/hugs/b/notebook/o/plumed.tar.bz2

# Not used here, but maybe somewhere else?
ENV KCOMBU_DOWNLOAD=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/lRplAwerQbpz3PFPhVtkc7O_Tj9RENtj4KS8MW54OGA/n/hugs/b/notebook/o/kcombu-src-20190208.tar.gz

USER root
WORKDIR /home

# Fix symbolic link for libtinfo to avoid annoying Bash warning.
RUN rm /opt/conda/lib/libtinfo.so && \
    ln -sf /opt/conda/lib/libtinfo.so /opt/conda/lib/libtinfo.so.6

# Pull in the required packages.
RUN apt-get update && \
    apt-get -yq --no-install-recommends install git nano vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure environment.
ENV SIRE_SILENT_PHONEHOME=1 \
    SIRE=/opt/conda \
    AMBERHOME=/home/amber \
    PATH=/home/gromacs/bin:/home/plumed/bin:$PATH \
    LD_LIBRARY_PATH=/home/plumed/lib:/opt/conda/lib:$LD_LIBRARY_PATH \
    PLUMED_KERNEL=/home/plumed/lib/libplumedKernel.so

# Download and install AmberTools into /home using wget.
RUN wget $AMBER_DOWNLOAD -O amber.tar.bz2 && \
    tar -jxvf amber.tar.bz2 && \
    rm amber.tar.bz2

# Download and install GROMACS into /home using wget.
RUN wget $GROMACS_DOWNLOAD -O gromacs.tar.bz2 && \
    tar -jxvf gromacs.tar.bz2 && \
    rm gromacs.tar.bz2

# Download and install PLUMED into /home using wget.
RUN wget $PLUMED_DOWNLOAD -O plumed.tar.bz2 && \
    tar -jxvf plumed.tar.bz2 && \
    rm plumed.tar.bz2

# Pin the version of Conda so that we don't get unexpected
# changes in Python.
RUN echo "python 3.7.*" >> /opt/conda/conda-meta/pinned

# Do all conda work as $NB_USER.
USER $NB_USER
WORKDIR $HOME

# Install BioSimSpace via Conda and dependencies for PLUMED.
RUN conda install -y -c conda-forge -c omnia -c michellab/label/dev biosimspace && \
    conda install -y -c conda-forge libgfortran=3 nodejs openmpi-mpicxx openssh patch

RUN pip install --upgrade pip && \
    pip install jupyterhub-tmpauthenticator

# Install and enable nglview.
RUN jupyter-nbextension install nglview --py --sys-prefix && \
    jupyter-nbextension enable nglview --py --sys-prefix && \
    jupyter serverextension enable jupyterlab && \
    jupyter-labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install nglview-js-widgets

# Clean up after conda, including clearing the cache.
RUN conda clean -tipsy && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf $HOME/.cache $HOME/.jupyter $HOME/.local/share/jupyter

# Clone source and workshop repositories.
RUN git clone https://github.com/michellab/biosimspace && \
    mkdir workshops && \
    git clone https://github.com/CCPBioSim/python_and_data_workshop workshops/python && \
    git clone https://github.com/CCPBioSim/biosimspace-workshop workshops/introduction && \
    git clone https://github.com/CCPBioSim/biosimspace-advanced-simulation workshops/advanced

# Link the right directories into the right places.
RUN rmdir work && \
    ln -s $HOME/biosimspace/demo $HOME/demo

# Add any BioSimSpace patches.
ADD patches .patches

# Patch the BioSimSpace install so that we restrict GROMACS to use a single
# MPI thread and four OpenMP thread per MPI thread.
RUN patch /opt/conda/lib/python3.7/site-packages/BioSimSpace/Process/_gromacs.py .patches/_gromacs.py.patch

# Copy the example nodes into the Python library.
RUN mkdir /opt/conda/lib/python3.7/site-packages/BioSimSpace/Node/_nodes && \
    cp $HOME/demo/*.py /opt/conda/lib/python3.7/site-packages/BioSimSpace/Node/_nodes/

# Change the executable name so that BioSimSpace notebook usage statistics
# can be tracked separately.
RUN sed -i 's/= "BioSimSpace"/= "BioSimSpace (notebook)"/g' /opt/conda/lib/python3.7/site-packages/Sire/__init__.py

# Add in our custom notebook config.
USER root

# Copy acrross JupyterHub configuration.
COPY jupyterhub_config.py /etc/jupyter/

# Add in the 'update_biosimspace' command to make things easy.
COPY update_biosimspace /usr/bin

# Run update_biosimspace in case there have been any updates that haven't been
# pushed to Conda.
RUN /usr/bin/update_biosimspace

# End as the User to make sure that we don't
# accidentally run the container as root.
USER $NB_USER
