#!/usr/bin/env python3
"""
mission_base.py

Classe base reutilizável para missões do TCC.

Encapsula a sequência básica de conexão/arm/offboard/decolagem/pouso
que toda missão precisa, como um context manager. Missões específicas
do TCC (detecção de zona de pouso, etc.) devem importar SimpleMission
e usar 'with', em vez de duplicar essa lógica.

Uso básico:
    from mission_base import SimpleMission

    with SimpleMission('x500_px4') as mission:
        mission.takeoff(2.0)
        mission.hover(3.0)
        # ... lógica específica da missão aqui ...
        mission.land()
"""

from time import sleep
import time
import numpy as np
import rclpy
from as2_python_api.drone_interface import DroneInterface
from geometry_msgs.msg import PointStamped



class SimpleMission:
    """
    Wrapper de missão básica sobre DroneInterface.

    Garante, via context manager, que o drone sempre desarma e
    desconecta corretamente, mesmo se a missão lançar uma exceção
    no meio do caminho.
    """

    def __init__(self, drone_namespace: str, use_sim_time: bool = True,
                 verbose: bool = True):
        self.drone_namespace = drone_namespace
        self.use_sim_time = use_sim_time
        self.verbose = verbose
        self.drone: DroneInterface = None

    def __enter__(self) -> 'SimpleMission':
        self._log(f'Inicializando ROS2 e conectando ao drone "{self.drone_namespace}"...')
        rclpy.init()
        self.drone = DroneInterface(
            drone_id=self.drone_namespace,
            use_sim_time=self.use_sim_time,
            verbose=self.verbose,
        )
        # Captura a posicao inicial (antes de decolar), pra poder voltar depois
        sleep(1.0)  # da um tempo pro DroneInterface receber a primeira pose
        self.home_position = self._get_current_position()
        self._log(f'Posicao inicial (home) capturada: {self.home_position}')
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is not None:
            self._log(f'Missão interrompida por exceção: {exc_value}')

        self._log('Garantindo desarme antes de encerrar...')
        try:
            self.drone.disarm()
        except Exception as e:
            self._log(f'Aviso: desarme retornou erro (provavelmente já '
                      f'estava desarmado): {e}')

        self._log('Encerrando conexão com o drone...')
        self.drone.shutdown()
        rclpy.shutdown()
        self._log('Missão finalizada.')

        # Não suprime a exceção original (se houver) -- deixa propagar
        # depois da limpeza, pra você ver o traceback de verdade.
        return False

    def arm(self) -> None:
        """Arma os motores."""
        self._log('Armando motores...')
        self.drone.arm()
        sleep(1.0)

    def offboard(self) -> None:
        """Ativa modo offboard (controle via software)."""
        self._log('Ativando modo offboard...')
        self.drone.offboard()
        sleep(1.0)

    def takeoff(self, height: float, speed: float = 0.5) -> None:
        """
        Sequência completa de decolagem: arma, ativa offboard, decola.

        Chama arm() e offboard() automaticamente, então não precisa
        chamar eles antes -- só usar takeoff() direto.
        """
        self.arm()
        self.offboard()
        self._log(f'Decolando até {height} m...')
        self.drone.takeoff(height=height, speed=speed)
        self._log('Decolagem concluída!')

    def hover(self, seconds: float) -> None:
        """Paira (fica parado no ar) pelo tempo especificado."""
        self._log(f'Pairando por {seconds} s...')
        sleep(seconds)

    def land(self, speed: float = 0.3) -> None:
        """Pousa o drone."""
        self._log('Pousando...')
        self.drone.land(speed=speed)
        self._log('Pouso concluído!')
        sleep(2.0)  # aguarda confirmação de pouso

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f'[{self.__class__.__name__}] {message}')

    # def go_to(self, x: float, y: float, z: float, speed: float = 0.5) -> None:
    #     """Move o drone ate a posicao (x, y, z) especificada, em linha reta."""
    #     self._log(f'Indo para posicao ({x:.2f}, {y:.2f}, {z:.2f})...')
    #     self.drone.go_to.go_to_point([x, y, z], speed=speed)
    #     self._log('Chegou na posicao de destino!')

    # def go_to(self, x: float, y: float, z: float, speed: float = 0.5,
    #           tolerance: float = 0.3, timeout: float = 30.0) -> None:
    #     """Move o drone ate (x, y, z), esperando ativamente ate chegar perto o suficiente."""
    #     self._log(f'Indo para posicao ({x:.2f}, {y:.2f}, {z:.2f})...')
    #     success = self.drone.go_to.go_to_point([x, y, z], speed=speed)
    #     if not success:
    #         self._log('AVISO: comando de movimento foi rejeitado!')
    #         return

    #     start = time.time()
    #     target = np.array([x, y, z])
    #     chegou = False
    #     while time.time() - start < timeout:
    #         current = np.array(self.drone.position)
    #         distancia = np.linalg.norm(current - target)
    #         if distancia <= tolerance:
    #             chegou = True
    #             break
    #         sleep(0.5)

    #     if chegou:
    #         self._log('Chegou na posicao de destino!')
    #     else:
    #         self._log(
    #             f'AVISO: nao chegou perto o suficiente em {timeout}s '
    #             f'(ficou em {self.drone.position}, alvo era {target.tolist()}).'
    #         )

    def go_to(self, x: float, y: float, z: float, speed: float = 0.5,
              tolerance: float = 0.3, timeout: float = 30.0) -> None:
        self._log(f'Indo para posicao ({x:.2f}, {y:.2f}, {z:.2f})...')
        success = self.drone.go_to.go_to_point([x, y, z], speed=speed)
        if not success:
            self._log('AVISO: comando de movimento foi rejeitado!')
            return

        start = time.time()
        target = np.array([x, y, z])
        chegou = False
        last_log = 0.0
        while time.time() - start < timeout:
            current = np.array(self.drone.position)
            distancia = np.linalg.norm(current - target)
            if distancia <= tolerance:
                chegou = True
                break

            # log periodico de diagnostico, a cada 2s
            elapsed = time.time() - start
            if elapsed - last_log >= 2.0:
                self._log(f'  ... posicao atual: {current.tolist()}, distancia ao alvo: {distancia:.2f}m')
                last_log = elapsed

            sleep(0.5)

        if chegou:
            self._log('Chegou na posicao de destino!')
        else:
            self._log(
                f'AVISO: nao chegou perto o suficiente em {timeout}s '
                f'(ficou em {self.drone.position}, alvo era {target.tolist()}).'
            )

    def _get_current_position(self) -> tuple:
            """Le a posicao atual do drone. Ajustar conforme atributo real do DroneInterface."""
            pos = self.drone.position  # <-- confirma se esse e o nome certo com o comando acima
            return (pos[0], pos[1], pos[2])

    def go_home(self, altitude: float = None, speed: float = 0.5) -> None:
        """Volta para a posicao (x,y) de onde a missao comecou, mantendo altitude atual (ou a especificada)."""
        x, y, _ = self.home_position
        z = altitude if altitude is not None else self.drone.position[2]
        self.go_to(x, y, z, speed=speed)
    
    #  def wait_for_landing_candidate(self, timeout: float = 30.0):
    #     """
    #     Espera receber um candidato de pouso no topico de percepcao.
    #     Retorna (x, y, z) ou None se estourar o timeout.
    #     """
    #     self._log(f'Esperando candidato de pouso (timeout {timeout}s)...')
    #     result = {'point': None}

    #     def callback(msg: PointStamped):
    #         result['point'] = (msg.point.x, msg.point.y, msg.point.z)

    #     sub = self.drone.create_subscription(
    #         PointStamped, '/perception/landing_candidates/best', callback, 10)

    #     start = time.time()
    #     while result['point'] is None and (time.time() - start) < timeout:
    #         rclpy.spin_once(self.drone, timeout_sec=0.5)

    #     self.drone.destroy_subscription(sub)

    #     if result['point'] is None:
    #         self._log('Nenhum candidato encontrado dentro do timeout!')
    #         return None

    #     self._log(f'Candidato recebido: {result["point"]}')
    #     return result['point']

    def wait_for_landing_candidate(self, timeout: float = 30.0):
        """
        Espera receber um candidato de pouso no topico de percepcao.
        Retorna (x, y, z) ou None se estourar o timeout.
        """
        self._log(f'Esperando candidato de pouso (timeout {timeout}s)...')
        result = {'point': None}

        def callback(msg: PointStamped):
            result['point'] = (msg.point.x, msg.point.y, msg.point.z)

        sub = self.drone.create_subscription(
            PointStamped, '/perception/landing_candidates/best', callback, 10)

        start = time.time()
        while result['point'] is None and (time.time() - start) < timeout:
            time.sleep(0.2)  # NAO chama spin_once aqui -- o auto_spin do
                              # DroneInterface ja processa a subscription sozinho

        self.drone.destroy_subscription(sub)

        if result['point'] is None:
            self._log('Nenhum candidato encontrado dentro do timeout!')
            return None

        self._log(f'Candidato recebido: {result["point"]}')
        return result['point']