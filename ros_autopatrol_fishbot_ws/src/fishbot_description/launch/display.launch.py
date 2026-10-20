import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 获取默认路径
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    default_model_path = urdf_tutorial_path + '/urdf/fishbot/fishbot.urdf.xacro'
    default_rviz_config_path = urdf_tutorial_path + '/config/rviz/display_model.rviz'
    # 为 Launch 声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
    use_sim_time_arg = launch.actions.DeclareLaunchArgument(
        name='use_sim_time', default_value='true',
        description='是否使用 Gazebo 仿真时间')
    use_joint_state_publisher_arg = launch.actions.DeclareLaunchArgument(
        name='use_joint_state_publisher', default_value='false',
        description='是否启动独立 joint_state_publisher；与 ros2_control 同时使用时应保持关闭')
    use_robot_state_publisher_arg = launch.actions.DeclareLaunchArgument(
        name='use_robot_state_publisher', default_value='false',
        description='是否启动独立 robot_state_publisher；Gazebo 已启动时应保持关闭')
    # 获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
        value_type=str)
    # 状态发布节点
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        condition=launch.conditions.IfCondition(
            launch.substitutions.LaunchConfiguration('use_robot_state_publisher')),
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
        }]
    )
    # 关节状态发布节点
    joint_state_publisher_node = launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        condition=launch.conditions.IfCondition(
            launch.substitutions.LaunchConfiguration('use_joint_state_publisher')),
        parameters=[{
            'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
        }],
    )
    # RViz 节点
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', default_rviz_config_path],
        parameters=[{
            'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
        }],
    )
    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        use_sim_time_arg,
        use_joint_state_publisher_arg,
        use_robot_state_publisher_arg,
        joint_state_publisher_node,
        robot_state_publisher_node,
        rviz_node
    ])
