
# Aerostack LEAD 2 - Ambiente de Simulação

Ambiente de simulação para desenvolvimento e validação de algoritmos de controle de voo e missões autônomas utilizando **ROS 2 Humble**, **PX4 SITL**, **Gazebo** e **Aerostack2**.

---

## Arquitetura do Ambiente

1. **Workspace do Usuário (`aerostack2_ws/src`)**: Montado como volume compartilhado entre o seu computador físico e o container. Qualquer alteração feita no seu código host reflete diretamente dentro do Docker em tempo real.
2. **Workspace de Dependências (`dependencias_px4`)**: Isolado internamente no container. Baixa e compila automaticamente as mensagens oficiais do PX4 (`px4_msgs`, `px4_ros_com`), mantendo o repositório Git limpo.
3. **Firmware de Voo**: Simulador **PX4-Autopilot v1.16** compilado internamente na pasta `/home/developer/PX4-Autopilot`.
4. **Ponte de Comunicação**: O **Micro-XRCE-DDS Agent** gerencia a tradução de baixa latência entre o protocolo uORB do PX4 e os tópicos nativos do ROS 2.

---

## Pré-requisitos

Antes de iniciar, certifique-se de ter instalado no seu computador físico (Ubuntu 22.04+):

* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [Docker Compose](https://docs.docker.com/compose/install/)

---

## Instalação e Configuração

### 1. Clonar o Repositório
No terminal do seu **computador real**:
```bash
git clone git@github.com:Larissrocha/Aerostack_lead_2.git
cd Aerostack_lead_2

```

### 2. Permitir Acesso à Interface Gráfica (X11)

Para que o Gazebo e o RViz consigam abrir janelas gráficas no monitor do seu host, execute no seu **computador real** (necessário após ligar ou reiniciar a máquina):

```bash
xhost +local:root
xhost +local:developer

```

### 3. Construir e Iniciar o Container Docker

Para baixar a imagem base, compilar o MicroXRCEAgent, o PX4 SITL e o workspace de dependências:

```bash
docker compose up -d --build

```

### 4. Acessar o Terminal do Container

Entre no container como o usuário padrão `developer`:

```bash
docker exec -it -u developer aerostack_lead_2 /bin/bash

```

---

## Compilação do Workspace

Na primeira execução (ou após criar/modificar pacotes C++ e mensagens ROS 2), execute a compilação dentro do **Docker**:

```bash
cd /home/developer/aerostack2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --parallel-workers 1
source install/setup.bash

```

> **Nota de Performance:** A flag `--parallel-workers 1` limita o processo de compilação a 1 núcleo por vez para evitar esgotamento de memória RAM da máquina host/VM.

---

## Executar a Simulação

Com o workspace compilado e as permissões de vídeo liberadas, inicie o ambiente de simulação dentro do terminal do **Docker**:

```bash
cd /home/developer/aerostack2_ws/src/sim_environment
./launch_sim.bash

```

O script automatiza via `tmuxinator` a inicialização dos componentes fundamentais:

* **Gazebo**: Motor de física e renderização do mundo 3D.
* **Drone Bridges**: Pontes de sensores e câmeras para o ROS 2.
* **PX4 SITL**: Piloto automático em modo simulação.
* **MicroXRCEAgent**: Ponte de dados ROS 2 $\leftrightarrow$ PX4.

---

## Executar Missões em Paralelo

Para interagir com o drone enquanto a simulação está rodando:

1. Abra uma nova aba no terminal da sua **máquina física**:
```bash
docker exec -it -u developer aerostack_lead_2 /bin/bash

```


2. Carregue o ambiente e execute seu script de missão:
```bash
cd /home/developer/aerostack2_ws
source install/setup.bash
ros2 run lead_missions simple_mission

```
---

## Estrutura do Projeto e Organização de Pastas

Abaixo está o detalhamento de cada diretório e componente do repositório:

```text
Aerostack_lead_2/
├── docker/
│   └── Dockerfile                   # Receita de build do container com ROS 2, PX4 SITL e Micro-XRCE-Agent
├── docker-compose.yml               # Configurações de volumes, portas e permissões gráficas do Docker
├── README.md                        # Documentação técnica do ambiente
└── aerostack2_ws/
    └── src/
        ├── sim_environment/          # Pacote de orquestração do cenário de simulação
        │   ├── config/              # Parâmetros de mundo, drones e sensores (.yaml)
        │   ├── models/              # Modelos 3D e descrições físicas SDF/Jinja específicos do projeto
        │   ├── tmuxinator/          # Configuração de sessões e inicialização em abas do terminal
        │   ├── utils/               # Scripts auxiliares de leitura de parâmetros e spawn
        │   └── launch_sim.bash      # Script principal de inicialização da simulação
        │
        ├── lead_missions/            # Pacote customizado do usuário para criação de missões
        │   ├── lead_missions/
        │   │   ├── base_mission.py  # Classe base com gerenciador de contexto (arm, takeoff, hover, land)
        │   │   └── simple_mission.py# Script executável de missão sequencial
        │   ├── package.xml          # Declaração de dependências ROS 2 (rclpy, as2_msgs, std_srvs)
        │   └── setup.py             # Registro de entry points e executáveis de terminal
        │
        └── aerostack2/               # Framework base do Aerostack2 (Core, Bridges e Modelos)
            ├── as2_core/            # Bibliotecas C++ e utilitários centrais de arquitetura
            ├── as2_msgs/            # Definições de interfaces nativas (msgs, srvs e actions)
            ├── as2_python_api/      # Módulo Python com classes de controle e telemetria de alto nível
            └── as2_simulation_assets/
                └── as2_gazebo_assets/
                    ├── CMakeLists.txt # Regras de compilação das pontes em C++
                    ├── launch/        # Launchfiles Python para o Gazebo e pontes de sensores
                    ├── models/        # Modelos de drones e sensores suportados (ex: x500_px4, quadrotor_base)
                    ├── src/           # Código-fonte C++ das pontes (gps_bridge, ground_truth, etc.)
                    └── worlds/        # Arquivos de descrição de mundo e física padrão (.sdf.jinja)

```

### Detalhamento dos Componentes Principais

* **`docker/` e `docker-compose.yml**`: Isolam todo o ecossistema de software de voo (ROS 2 Humble, compilador PX4 e dependências) sem poluir o sistema operacional da máquina física.
* **`sim_environment/`**: Concentra as definições físicas do mundo, modelos de sensores e o orquestrador `launch_sim.bash`, que inicializa simultaneamente a física do Gazebo, o PX4 SITL e as pontes de comunicação.


* **`lead_missions/`**: Área limpa de desenvolvimento do usuário. Contém os nós em Python responsáveis por interagir com os tópicos e ações dos comportamentos do drone.
* **`aerostack2/`**: Estrutura contendo o núcleo de comunicação, dicionários de mensagens (`as2_msgs`), utilitários Python (`as2_python_api`) e os assets e bridges de simulação para o Gazebo (`as2_gazebo_assets`).



```

```

---

## Resumo de Comandos Úteis

| Objetivo | Comando | Onde Executar |
| --- | --- | --- |
| **Liberar display para o Docker** | `xhost +local:root && xhost +local:developer` | Máquina Física |
| **Subir / Recriar Container** | `docker compose up -d --build` | Máquina Física (Raiz) |
| **Entrar no Container** | `docker exec -it -u developer aerostack_lead_2 /bin/bash` | Máquina Física |
| **Derrubar Container** | `docker compose down` | Máquina Física |
| **Compilar Workspace** | `colcon build --symlink-install --parallel-workers 1` | Dentro do Docker |
| **Encerrar Sessão Tmux** | `tmux kill-server` | Dentro do Docker |
| **Forçar Parada do Simulador** | `killall -9 gz-sim-server gz-sim-gui px4 MicroXRCEAgent` | Dentro do Docker |

```

```
