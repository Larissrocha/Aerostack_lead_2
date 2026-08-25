# ==============================================================================
# ESTÁGIO 1: INSTALAÇÕES GLOBAIS E DEPENDÊNCIAS DO SISTEMA (COMO ROOT)
# ==============================================================================
# 1. Usamos a imagem base que eles usaram (já vem com dependências do AS2)
FROM aerostack2/nightly-humble:latest

USER root
WORKDIR /root

# 2. Atualizar Gazebo para a versão Harmonic
RUN apt remove ignition* -y && apt autoremove -y
RUN apt-get update && apt-get install -y lsb-release wget gnupg nano git tmux tmuxinator python3-pip python3-rosdep ros-dev-tools
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
RUN apt-get update && apt-get install -y -q gz-harmonic ros-humble-ros-gzharmonic

# 3. Instalar o Micro-XRCE-DDS-Agent (Ponte de comunicação com o PX4)
RUN git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git && \
    cd Micro-XRCE-DDS-Agent && mkdir build && cd build && \
    cmake .. && make && make install && ldconfig /usr/local/lib/

# 4. Ajustar pacotes Python necessários
RUN pip3 install numpy==1.24.4 PySimpleGUI-4-foss

# 5. Criar o usuário 'developer' para não dar erro de permissão gráfica nem de escrita
RUN useradd -m developer && echo "developer:developer" | chpasswd && adduser developer sudo
RUN chown -R developer:developer /home/developer

# ==============================================================================
# ESTÁGIO 2: CONFIGURAÇÃO DO PX4 (COMO ROOT PARA EVITAR PEDIDO DE SENHA NO SUDO)
# ==============================================================================
WORKDIR /home/developer

# 1. Baixa o simulador PX4 oficial direto da comunidade
RUN git clone -b release/1.16 https://github.com/PX4/PX4-Autopilot.git --recursive
WORKDIR /home/developer/PX4-Autopilot

# Instala as dependências usando a flag DEBIAN_FRONTEND para não pedir interação humana
ENV DEBIAN_FRONTEND=noninteractive
RUN ./Tools/setup/ubuntu.sh --no-nuttx

# 2. Cria a pasta de dependências oficiais do PX4 dentro do container
WORKDIR /home/developer/dependencias_px4/src
RUN git clone -b release/1.16 https://github.com/PX4/px4_msgs.git \
    && git clone -b release/1.16 https://github.com/PX4/px4_ros_com.git

# Compila as mensagens do PX4 no workspace isolado
WORKDIR /home/developer/dependencias_px4
RUN /bin/bash -c "source /opt/ros/\${ROS_DISTRO}/setup.bash && colcon build --symlink-install"

# Ajusta a permissão de tudo o que o root criou para pertencer ao developer
RUN chown -R developer:developer /home/developer/PX4-Autopilot \
    && chown -R developer:developer /home/developer/dependencias_px4

# ==============================================================================
# ESTÁGIO 3: CONFIGURAÇÃO DO USUÁRIO E AMBIENTE FINAL (COMO DEVELOPER)
# ==============================================================================
USER developer

# Copia os arquivos de configuração de terminal que trouxemos do tutorial
COPY --chown=developer:developer docker/to_copy/tmux /home/developer/.tmux.conf
COPY --chown=developer:developer docker/to_copy/aliases /home/developer/.bash_aliases

# Define o workspace do seu TCC como a pasta padrão de trabalho
WORKDIR /home/developer/aerostack2_ws

# Configura o .bashrc para carregar absolutamente tudo de forma automática ao abrir o terminal
RUN echo "source /opt/ros/\${ROS_DISTRO}/setup.bash" >> /home/developer/.bashrc \
    && echo "source /home/developer/dependencias_px4/install/setup.bash" >> /home/developer/.bashrc \
    && echo "export GZ_VERSION=harmonic" >> /home/developer/.bashrc \
    && echo "export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:/home/developer/aerostack2_ws/src/models" >> /home/developer/.bashrc