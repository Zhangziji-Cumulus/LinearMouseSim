import unittest

from core.steering_algorithm import SteeringAlgorithm


class SteeringDirectionTest(unittest.TestCase):
    def test_default_left_move_produces_negative_angle(self):
        algorithm = SteeringAlgorithm(
            sensitivity=1.0,
            deadzone=0,
            max_angle=90,
            return_speed=0.0,
            smoothing_factor=1.0,
        )

        left_angle = algorithm.update(-10, is_moving=True)
        self.assertLess(left_angle, 0)

        algorithm.reset()
        right_angle = algorithm.update(10, is_moving=True)
        self.assertGreater(right_angle, 0)


if __name__ == '__main__':
    unittest.main()
