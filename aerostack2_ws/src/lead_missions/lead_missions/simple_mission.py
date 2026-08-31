#!/usr/bin/env python3
"""
Missão simples  via ROS 2.
"""

import time
import rclpy
import math
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import Bool


class DirectSimMission(Node):
    def __init__(self):
        super().__init__('direct_sim_mission')

        self.drone_ns = 'x500_px4'

        # Publishers ativos na sua simulação
        self.cmd_vel_pub = self.create_publisher(Twist, f'/gz/{self.drone_ns}/cmd_vel', 10)
        self.arm_pub = self.create_publisher(Bool, f'/gz/{self.drone_ns}/arm', 10)

        # Subscriber de Pose
        self.pose_sub = self.create_subscription(
            PoseStamped, f'/{self.drone_ns}/ground_truth/pose', self.pose_cb, 10)

        # Guardar a posição atual em 3D
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0

        # Ponto de retorno (Home)
        self.home_x = 0.0
        self.home_y = 0.0
        self.home_captured = False

        # Coordenada do Marcador ArUco no Gazebo
        self.marker_x = 2.5
        self.marker_y = 1.5
        self.target_alt = 2.0

        self.timer = self.create_timer(0.05, self.control_loop)  # 20 Hz
        self.start_time = time.time()
        self.step = 0

        self.get_logger().info('Iniciando controle direto de voo do x500_px4...')

    def pose_cb(self, msg: PoseStamped):
        self.current_x = msg.pose.position.x
        self.current_y = msg.pose.position.y
        self.current_z = msg.pose.position.z

        # Salva o ponto de origem apenas na primeira vez
        if not self.home_captured:
            self.home_x = self.current_x
            self.home_y = self.current_y
            self.home_captured = True

    def arm_drone(self, state: bool):
        msg = Bool()
        msg.data = state
        self.arm_pub.publish(msg)

    def publish_velocity(self, vx=0.0, vy=0.0, vz=0.0, yaw_rate=0.0):
        twist = Twist()
        twist.linear.x = float(vx)
        twist.linear.y = float(vy)
        twist.linear.z = float(vz)
        twist.angular.z = float(yaw_rate)
        self.cmd_vel_pub.publish(twist)

    def navigate_to(self, target_x, target_y, target_z, max_speed=0.5, tol=0.25) -> bool:
        # 1. Calcula o erro em relação ao alvo
        dx = target_x - self.current_x
        dy = target_y - self.current_y
        dz = target_z - self.current_z
        
        dist_horizontal = math.hypot(dx, dy)
        
        # 2. Converte erro em velocidade proporcional (Kp = 0.8)
        vx = max(min(dx * 0.8, max_speed), -max_speed)
        vy = max(min(dy * 0.8, max_speed), -max_speed)
        vz = max(min(dz * 0.8, max_speed), -max_speed)
        
        self.publish_velocity(vx=vx, vy=vy, vz=vz)
        
        # 3. Retorna True quando estiver perto o suficiente do alvo
        return (dist_horizontal < tol) and (abs(dz) < tol)
    
    def control_loop(self):
        elapsed = time.time() - self.start_time

        if self.step == 0:
            # 0. Armar os motores
            self.arm_drone(True)
            self.get_logger().info('Armando motores e iniciando decolagem...')
            self.step = 1
            self.start_time = time.time()

        elif self.step == 1:
            # 1. Subir até ~2 metros de altitude
            if self.current_z < self.target_alt and elapsed < 6.0:
                self.publish_velocity(vz=0.8)
            else:
                self.publish_velocity(vz=0.0)
                self.get_logger().info(f'Altitude alvo atingida ({self.current_z:.2f} m)! Pairando por 4s...')
                self.step = 2
                self.start_time = time.time()

        elif self.step == 2:
        # [2] Navegar até o marcador ArUco
            chegou = self.navigate_to(self.marker_x, self.marker_y, self.target_alt)
            if chegou or elapsed > 15.0:
                self.publish_velocity(0.0, 0.0, 0.0)
                self.step = 3
                self.start_time = time.time()

        # [3] Pairar / Sobrevoar o marcador
        elif self.step == 3:
            self.navigate_to(self.marker_x, self.marker_y, self.target_alt, max_speed=0.1)
            if elapsed > 4.0:
                self.step = 4
                self.start_time = time.time()

        elif self.step == 4:
        # 4. Retornar ao ponto de origem (Home) mantendo altitude
            chegou_home = self.navigate_to(self.home_x, self.home_y, self.target_alt)
            if chegou_home or elapsed > 15.0:
                self.publish_velocity(0.0, 0.0, 0.0)
                self.step = 5
                self.start_time = time.time()
        # [5] Pousar suavemente e desarmar
        elif self.step == 5:
            if self.current_z > 0.15 and elapsed < 6.0:
                self.publish_velocity(vz=-0.5)
            else:
                self.publish_velocity(vz=0.0)
                self.arm_drone(False)
                self.step = 6
                rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = DirectSimMission()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()