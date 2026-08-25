#!/usr/bin/env python3
"""
Missão simples para testar a conexão básica Aerostack2 <-> PX4.

Decola, paira, pousa. NÃO usa árvore de comportamento, NÃO usa
detecção de ArUco ou LiDAR -- serve só para confirmar que a camada
Aerostack2 <-> PX4 está respondendo a comandos básicos de voo.

Como rodar (dentro do container, com a simulação já aberta):
    cd ~/aerostack2_ws/src/aerostack2_ws/src/project_landing-tcc_lucca
    python3 missao_simples.py
"""

from lead_missions.base_mission import SimpleMission

DRONE_NAMESPACE = 'x500_px4'
ALTURA_DECOLAGEM = 10.0  # metros
TEMPO_PAIRADO = 15.0     # segundos parado no ar antes de pousar
POSICAO_ORIGEM = (0.0, 0.0, ALTURA_DECOLAGEM)


def main():
    with SimpleMission(DRONE_NAMESPACE) as mission:
        mission.takeoff(ALTURA_DECOLAGEM)
        mission.hover(TEMPO_PAIRADO)
        # mission.go_home(speed=1.0)
        mission.land()


if __name__ == '__main__':
    main()