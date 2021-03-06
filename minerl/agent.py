import gym
import minerl
import matplotlib.pyplot as plt
from search_grid import *

# Experiment parameters
max_time_steps = 3000
num_episodes = 10
good_seeds = [1013, 1015, 1016]
seed = good_seeds[0]

env = gym.make("MineRLNavigateDense-v0")

for ep in range(num_episodes):

	done = False
	net_reward = 0
	action = env.action_space.noop()
	reward_measues = []
	compass_measures = []

	# Episode stages
	adjusting = False
	init_stage = True
	running_stage = False
	close_to_goal = False
	approach_goal = False
	search_goal = False

	# Search grid representation
	search_actions = []
	search_counter = 0
	init_grid_size = 3
	grid_size_increment = 2
	max_grid_size = 300

	# Generate search grid
	search_actions = search_grid(init_grid_size, max_grid_size, grid_size_increment)

	print_msg = True        # used to stop printing console messages
	angle_threshold = 150   # indicates that the agent just passed by the goal
	adjust_period = 100     # compass angle adjustment period
	time_counter = 0        # a generic timer for counting duration in time steps
	cam_turn_factor = 0.03  # proportion of the compass angle, used to turn the camera towards it

	# env.seed(seed)
	obs = env.reset()

	for time_step in range(max_time_steps):
		_ = env.render()

		# Wait until the compass has adjusted
		if adjusting:
			if print_msg:
				print("Adjusting...")
				print_msg = False			

			action = env.action_space.noop()
			adjusting = time_counter < adjust_period

		# Stage 1: turn towards goal
		if init_stage and not adjusting:
			
			if print_msg:
				print("\nStage 1: turn towards goal")
				print_msg = False

			action['camera'] = [0, cam_turn_factor*obs['compassAngle']]

			if time_counter > adjust_period:
				init_stage = False
				running_stage = True
				time_counter = 0
				print_msg = True

		# Stage 2: run until close to goal
		if running_stage and not adjusting:
			
			if print_msg:
				print("\nStage 2: run towards goal")
				print_msg = False

			# Run towards goal
			action['forward'] = 1
			action['jump'] = 1
			action['camera'] = [0, cam_turn_factor*obs['compassAngle']]

			# Stop when the agent surpasses the goal
			if abs(obs['compassAngle']) > angle_threshold:
				action['forward'] = 0
				action['jump'] = 0

				running_stage = False
				close_to_goal = True
				time_counter = 0
				print_msg = True

		# Stage 3: agent surpassed goal, turn towards it
		if close_to_goal and not adjusting:
			
			if print_msg:
				print("\nStage 3: turn towards goal")
				print_msg = False

			action['camera'] = [0, cam_turn_factor*obs['compassAngle']]

			if time_counter > adjust_period:
				close_to_goal = False
				approach_goal = True
				adjusting = True
				time_counter = 0
				print_msg = True

		# Stage 4: approach goal
		if approach_goal and not adjusting:

			if print_msg:
				print("\nStage 4: reach goal")
				print_msg = False
			
			# Stop and move to next stage when agent surpasses goal
			if abs(obs['compassAngle']) > angle_threshold:
				action['forward'] = 0
				approach_goal = False
				search_goal = True
				time_counter = 0
				print_msg = True
			else:
				action['forward'] = 1
				adjusting = True
				time_counter = 0
				print_msg = True

		# Stage 5: search for goal
		if search_goal:
			if print_msg:
				print("Stage 5: searching...")
				print_msg = False

			adjust_period = 12
			action = env.action_space.noop()

			if time_counter > adjust_period:
				action = search_actions[search_counter]
				time_counter = 0

				# Move search counter to next action on the grid
				if search_counter + 1 < len(search_actions):
					search_counter += 1
				else:
					action = env.action_space.noop()


		# Take action, update, record measurements
		obs, reward, done, info = env.step(action)
		net_reward += reward
		time_counter += 1
		reward_measues.append(net_reward)
		compass_measures.append(obs['compassAngle'])

		# Check for termination
		if done:
			print("Done!")
			break

env.close()



print("Net reward: " + str((net_reward)))

# Plot measurements
plt.figure(1)
plt.plot(reward_measues, '-b')
plt.title('Reward over the episode')
plt.xlabel('time step')
plt.ylabel('reward')

plt.figure(2)
plt.plot(compass_measures, '-b')
plt.title('Compass angle over the episode')
plt.xlabel('time step')
plt.ylabel('compass angle')

plt.show()
