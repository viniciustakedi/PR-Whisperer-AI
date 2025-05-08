from process_steps.openai_step import generatePRDescription
from process_steps.git_step import updatePRDescription

description = generatePRDescription()
updatePRDescription(description)