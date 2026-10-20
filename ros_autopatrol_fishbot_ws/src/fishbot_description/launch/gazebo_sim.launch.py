import launch
import launch_ros
import os
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 获取默认路径
    robot_name_in_model = "fishbot"
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    default_model_path = urdf_tutorial_path + '/urdf/fishbot/fishbot.urdf.xacro'
    default_world_path = urdf_tutorial_path + '/world/custom_room.sdf'
    cafe_table_models_path = os.path.expanduser('~/.gazebo/models')
    cafe_table_root_path = os.path.join(cafe_table_models_path, 'cafe_table')
    cafe_table_textures_path = os.path.join(
        cafe_table_root_path, 'materials', 'textures')
    gz_resource_path = os.pathsep.join(filter(None, [
        cafe_table_models_path,
        cafe_table_root_path,
        cafe_table_textures_path,
        os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
    ]))
    set_gz_resource_path = launch.actions.SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path,
    )
    # 为 Launch 声明参数
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
    # 获取文件内容生成新的参数
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
        value_type=str)

    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }]
    )

    # 将 Gazebo 仿真时间和传感器数据单向桥接到 ROS 2。
    # 运动控制、里程计、TF 和关节状态由 ros2_control / robot_state_publisher 提供。
    # 相机和点云使用 lazy bridge：只有 ROS 侧存在订阅者时才转换大数据。
    ros_gz_bridge_node = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='bridge_node',
        parameters=[{
            'bridge_names': [
                'clock', 'scan', 'scan_points', 'imu', 'camera',
                'camera_info', 'depth_image', 'camera_points',
            ],
            'bridges': {
                'clock': {
                    'ros_topic_name': '/clock',
                    'gz_topic_name': '/clock',
                    'ros_type_name': 'rosgraph_msgs/msg/Clock',
                    'gz_type_name': 'gz.msgs.Clock',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'CLOCK',
                    'lazy': False,
                },
                'scan': {
                    'ros_topic_name': '/scan',
                    'gz_topic_name': '/scan',
                    'ros_type_name': 'sensor_msgs/msg/LaserScan',
                    'gz_type_name': 'gz.msgs.LaserScan',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': False,
                },
                'scan_points': {
                    'ros_topic_name': '/scan/points',
                    'gz_topic_name': '/scan/points',
                    'ros_type_name': 'sensor_msgs/msg/PointCloud2',
                    'gz_type_name': 'gz.msgs.PointCloudPacked',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': True,
                },
                'imu': {
                    'ros_topic_name': '/imu',
                    'gz_topic_name': '/imu',
                    'ros_type_name': 'sensor_msgs/msg/Imu',
                    'gz_type_name': 'gz.msgs.IMU',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': False,
                },
                'camera': {
                    'ros_topic_name': '/camera/image',
                    'gz_topic_name': '/camera/image',
                    'ros_type_name': 'sensor_msgs/msg/Image',
                    'gz_type_name': 'gz.msgs.Image',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': True,
                },
                'camera_info': {
                    'ros_topic_name': '/camera/camera_info',
                    'gz_topic_name': '/camera/camera_info',
                    'ros_type_name': 'sensor_msgs/msg/CameraInfo',
                    'gz_type_name': 'gz.msgs.CameraInfo',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': True,
                },
                'depth_image': {
                    'ros_topic_name': '/camera/depth_image',
                    'gz_topic_name': '/camera/depth_image',
                    'ros_type_name': 'sensor_msgs/msg/Image',
                    'gz_type_name': 'gz.msgs.Image',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': True,
                },
                'camera_points': {
                    'ros_topic_name': '/camera/points',
                    'gz_topic_name': '/camera/points',
                    'ros_type_name': 'sensor_msgs/msg/PointCloud2',
                    'gz_type_name': 'gz.msgs.PointCloudPacked',
                    'direction': 'GZ_TO_ROS',
                    'qos_profile': 'SENSOR_DATA',
                    'lazy': True,
                },
            },
        }],
        arguments=['--ros-args', '--log-level', 'info'],
        name='fishbot_gz_bridge',
        output='screen',
    )

    # 包含 ros_gz_sim 的启动文件，传入 world 文件
    launch_gazebo = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource([get_package_share_directory(
            'ros_gz_sim'), '/launch', '/gz_sim.launch.py']),
        launch_arguments=[('gz_args', f'-r {default_world_path}')]
    )
    # 请求 Gazebo 加载机器人，改用 ros_gz_sim 的 create 节点
    spawn_entity_node = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', '/robot_description',
                   '-name', robot_name_in_model, ])

    # 加载并激活 fishbot_joint_state_broadcaster 控制器
    load_joint_state_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
            'fishbot_joint_state_broadcaster'],
        output='screen'
    )

    # 加载并激活 fishbot_effort_controller 控制器

    #load_fishbot_effort_controller = launch.actions.ExecuteProcess(
    #    cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','fishbot_effort_controller'],
    #   output='screen')

    load_fishbot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','fishbot_diff_drive_controller'],
        output='screen')

    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        set_gz_resource_path,
        robot_state_publisher_node,
        ros_gz_bridge_node,
        launch_gazebo,
        spawn_entity_node,
        # 事件动作，当加载机器人结束后执行
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=spawn_entity_node,
                on_exit=[load_joint_state_controller],)
            ),
        # 事件动作，load_fishbot_diff_drive_controller
        launch.actions.RegisterEventHandler(
        event_handler=launch.event_handlers.OnProcessExit(
            target_action=load_joint_state_controller,
            on_exit=[load_fishbot_diff_drive_controller],)
            ),
    ])
