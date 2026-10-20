import rclpy
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator


def main():
    rclpy.init()
    navigator = BasicNavigator()

    navigator.set_parameters([
        Parameter('use_sim_time', Parameter.Type.BOOL, True)
    ])
    navigator.get_logger().info('已强制开启仿真时间 (use_sim_time = True)')

    # 顺序很重要：必须先发初始位姿，再去等 nav2 启动。
    # global_costmap / bt_navigator 的激活依赖 AMCL 广播的 map->odom，
    # 而 map->odom 只有 AMCL 拿到初始位姿之后才会出现。
    # 所以“先等 bt_navigator 再发位姿”会互相等待，直接死锁。
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0

    # setInitialPose() 会立刻发一次，并把 navigator.initial_pose 换成这一份，
    # 后面 waitUntilNav2Active() 重发时用的就是它（而不是默认的全 0 位姿）。
    navigator.get_logger().info('发送初始位姿...')
    navigator.setInitialPose(initial_pose)
    navigator.get_logger().info('已发送初始位姿')

    # 等 amcl active -> 重发位姿直到收到 amcl_pose -> 再等 bt_navigator
    navigator.get_logger().info('等待 Nav2 启动...')
    navigator.waitUntilNav2Active()
    navigator.get_logger().info('Nav2 已启动！')

    try:
        while rclpy.ok():
            rclpy.spin_once(navigator, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
