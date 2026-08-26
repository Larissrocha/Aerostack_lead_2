

---

## Arquitetura do Ambiente

1. **Workspace do Usuário (`aerostack2_ws/src`)**: Contém apenas as pastas e algoritmos específicos. Ele é montado como um volume no seu computador real.
2. **Workspace de Dependências (`dependencias_px4`)**: Isolado internamente dentro do Docker. Ele baixa e compila automaticamente as mensagens oficiais do PX4 (`px4_msgs`, `px4_ros_com`) direto da internet durante o build, mantendo o seu repositório Git limpo.
3. **Firmware de Voo**: O simulador completo do **PX4-Autopilot v1.16** é instalado internamente na pasta do usuário `developer`.

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado no seu computador físico (Ubuntu 22.04 ou superior/Máquina Virtual):

* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [Docker Compose](https://docs.docker.com/compose/install/)

---

### 1. Clonar o Repositório
Clonar repositório:
```bash
git clone <git@github.com:Larissrocha/Aerostack_lead.gitI>
cd Aerostack_lead

```

### 2. Permitir Acesso à Interface Gráfica (X11)

Para que o Gazebo e o RViz consigam abrir janelas na tela do seu computador de fora, execute o comando abaixo no terminal do seu **computador real** (sempre faça isso após ligar ou reiniciar o PC):

```bash
xhost +local:docker

```

### 3. Construir e Iniciar o Container Docker

Para baixar todas as imagens base, configurar o PX4, clonar as mensagens oficiais da internet e compilar o ambiente em segundo plano, rode:

```bash
docker compose up -d --build

```

### 4. Iniciar o Container

Com o container rodando em background, entre no terminal dele como usuário `developer`:

```bash
docker start meu_container_aerostack

docker exec -it -u developer aerostack_lead /bin/bash

docker exec -it -u developer aerostack_lead_2 /bin/bash
```

### 5. Compilação Segura do Workspace (Evitando Travamentos)

Para evitar que o compilador use 100% da sua memória RAM e trave o seu computador físico (especialmente em Máquinas Virtuais), execute a compilação limitando o processo a apenas **1 núcleo por vez**:

```bash
colcon build --symlink-install --parallel-workers 1

```
---

## Rodar a Simulação

Para iniciar o launch da simulação, execute dentro do terminal do **Docker**:

```bash
cd ~/aerostack2_ws
```

Carregue o ambiente do ROS 2
```bash

source install/setup.bash

```
Injete o caminho dos modelos 3D do Gazebo

```bash

export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:/home/developer/aerostack2_ws/src/aerostack2_ws/src/project_landing-tcc_lucca/models
```
Rodar
```bash

cd /home/developer/aerostack2_ws/src/sim_environment
./launch_sim.bash
```
---

## Resumo de Comandos Úteis

| Objetivo | Comando | Onde Executar |
| --- | --- | --- |
|Fecha o tmux e encerra todos os nós em segundo plano|tmux kill-server
|Garante que o processo do Gazebo não ficou fantasma|pkill -f gz
| Liberar tela para o Docker | `xhost +local:docker` | Máquina Física |
| Lançar/Atualizar o Container | `docker compose up -d --build` | Máquina Física (raiz) |
| Entrar no Container | `docker exec -it meu_container_aerostack /bin/bash` | Máquina Física |
| Compilar Código C++ com segurança | `colcon build --symlink-install --parallel-workers 1` | Dentro do Docker |
| Derrubar o container completamente | `docker compose down` | Máquina Física |
|                                    | `docker compose exec -u developer aerostack2 bash `|
||`pkill -9 -f gz `|


---

```

```
