from logging import Logger

from slack_bolt import Ack, Respond

from archer.agent import invoke_agent


def command_callback(ack: Ack, respond: Respond, request: dict, logger: Logger):
	"""
	Callback for handling a / command
	"""
	try:
		prompt = request["text"]
		if not prompt:
			# Acknowledge and send an immediate response for empty prompts
			ack("Looks like you didn't provide a prompt. Try again.")
			return
		else:
			# Acknowledge without a message
			ack()
			user_id = request["user_id"]
			response_text = invoke_agent(user_id, prompt)
			# Respond to the user
			respond(response_text)
	except Exception as e:
		logger.exception(f"Error in command_callback for command: {request['text']} from user: {request['user_id']}, error: {e}")
		# Notify the user about the error
		respond("Looks like something went wrong. Please try again.")

