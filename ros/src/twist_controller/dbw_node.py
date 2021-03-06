#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool, Int32
from styx_msgs.msg import Lane, Waypoint
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd
from geometry_msgs.msg import TwistStamped, PoseStamped

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)
        
        self.controller = Controller(wheel_base=wheel_base,
                                     steer_ratio=steer_ratio)
        
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cb)
        rospy.Subscriber('/current_velocity', TwistStamped, self.velocity_cb)
        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/final_waypoints', Lane, self.finalwaypt_cb)
        rospy.Subscriber('/traffic_light_ahead', Bool, self.trafficLightsAhead_cb)
        rospy.Subscriber('/nav_type', Int32, self.navtype_cb)

        self.current_vel = None
        self.linear_vel = None
        self.angular_vel = None
        self.dbw_enabled = None
        self.throttle = self.steering = self.brake = 0
        self.pose = None
        self.finalwaypts = None
        self.isCloseToTrafficLight = False
        self.navtype = None

        self.loop()

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        while not rospy.is_shutdown():
            if not None in (self.current_vel, self.linear_vel, self.angular_vel):
                self.throttle, self.brake, self.steering = \
                    self.controller.control(self.current_vel, self.dbw_enabled, \
                    self.linear_vel, self.angular_vel, self.finalwaypts, self.pose, \
                    self.isCloseToTrafficLight, self.navtype)
            
            if self.dbw_enabled:
                self.publish(self.throttle, self.brake, self.steering)
            rate.sleep()

    def dbw_enabled_cb(self, msg):
        self.dbw_enabled = msg
    
    def pose_cb(self, msg):
        self.pose = msg

    def finalwaypt_cb(self, msg):
        self.finalwaypts = msg
    
    def trafficLightsAhead_cb(self, msg):
        self.isCloseToTrafficLight = msg.data

    def twist_cb(self, msg):
        self.linear_vel = msg.twist.linear.x
        self.angular_vel = msg.twist.angular.z
    
    def velocity_cb(self, msg):
        self.current_vel = msg.twist.linear.x

    def navtype_cb(self, msg):
        self.navtype = msg.data

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
