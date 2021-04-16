# We're going to need a couple of libraries to make this a touch easier
import requests
import json
import clubhousemovevars

###########################################################################
# 
# MAKE CHANGES HERE - set your project ID and your API token
# It's a hassle to catch every author for each ticket and comment
# So we just set it all to the same person
# Make sure ticket_requester and comment_author is set to the right user ID
# 
###########################################################################

pivotal_project_id = clubhousemovevars.pivotal_project_id
clubhouse_token = clubhousemovevars.clubhouse_token
token = clubhousemovevars.token
ticket_requester = clubhousemovevars.ticket_requester
clubhouse_project_id = clubhousemovevars.clubhouse_project_id
comment_author = clubhousemovevars.comment_author


###########################################################################
# 
# That's your changes done!!
# 
###########################################################################

# Easiest way to do this is to tag anything you want to bring with you with "move" and just get those stories
pivotal_url = 'https://www.pivotaltracker.com/services/v5/projects/'+ pivotal_project_id +'/stories?with_label=move'
pivotal_headers = {"X-TrackerToken": token}
clubhouse_epic_url = "https://api.clubhouse.io/api/v3/epics"
clubhouse_story_url = "https://api.clubhouse.io/api/v3/stories"
clubhouse_headers = {"Content-Type": 'application/json', "Clubhouse-Token": clubhouse_token}

# Actually make the request
r = requests.get(pivotal_url, headers=pivotal_headers)

# Decode the json
tickets = json.loads(r.text)


# We need to go through all the tickets and get the labels first to create epics to assign these later

for ticket in tickets:
	
	for label in ticket['labels']:
		if label['name'] != "move":
			existing_epics = requests.get(clubhouse_epic_url, headers=clubhouse_headers)
			existing_epics = json.loads(existing_epics.text)
			found = any(x['name'] == label['name'] for x in existing_epics)
			if found == False:
				new_epic_data = '{"name":"' + label['name'] + '"}' 

				new_epic = requests.post(clubhouse_epic_url, headers=clubhouse_headers, data = new_epic_data)
				print("Created an epic: " + label['name'])
				

# This is where the fun begins.
# We've got the tickets, so let's create all the epics in Clubhouse

for ticket in tickets:
	try:
		epic_id = None
		description = "No description provided"
		# Get all the labels so we can put it in the right epic
		for label in ticket['labels']:
			# If the label is anything except 'move'
			if label['name'] != "move":
				
				existing_epics = requests.get(clubhouse_epic_url, headers=clubhouse_headers)
				existing_epics = json.loads(existing_epics.text)

				# Get the ID of the epic we're handling from the existing epics and check if it exists in Clubhouse. If not, create the epic
				for epic in existing_epics:
					if epic['name'] == label['name']:
						epic_id = epic['id']
		
		# Set up the ticket object
		estimate = 1

		name = ticket['name']
		if 'description' in ticket:
			description = ticket['description']
		if 'estimate' in ticket:
			estimate = ticket['estimate']
		new_ticket_data = {
			"name": name, 
			"description":description, 
			"project_id":clubhouse_project_id,
			"epic_id":epic_id, 
			"requested_by_id":ticket_requester,
			"estimate":estimate
		}
		new_ticket_data = json.dumps(new_ticket_data, 4)

		# Create the ticket
		story = requests.post(clubhouse_story_url, headers=clubhouse_headers, data = new_ticket_data)
		story = json.loads(story.text)
		
		# Grab the ID of the newly created ticket so we can add comments to it
		story_id = story['id']

		# Fetch the comments for the ticket
		pivotal_comments_url = 'https://www.pivotaltracker.com/services/v5/projects/'+ str(pivotal_project_id) +'/stories/' + str(ticket['id']) + '/comments?fields=file_attachment_ids,text'
		comments = requests.get(pivotal_comments_url, headers=pivotal_headers)
		comments = json.loads(comments.text)

		# Create each comment
		for comment in comments:
			# Null our comment content so we add do it
			text = ''

			# If we have text content add that to the body
			if 'text' in comment:
				text = text + comment['text']

			# If we have any files, generate a link to them and add that too
			if 'file_attachment_ids' in comment:
				for file in comment['file_attachment_ids']:
					pivotal_files_url = ' https://www.pivotaltracker.com/file_attachments/' + str(file) + '/download?inline=true'
					text = text + pivotal_files_url
					
			# Set up the comment object
			new_comment_data = {
				"text": text, 
				"author_id":comment_author
			}
			new_comment_data = json.dumps(new_comment_data, 4)

			#Create the comment
			clubhouse_comment_url = "https://api.clubhouse.io/api/v3/stories/" + str(story_id) + "/comments"
			new_comment = requests.post(clubhouse_comment_url, headers=clubhouse_headers, data = new_comment_data)

		print("Created a ticket: " + name + " that had " + str(len(comments)) + " comments.")
	except:
		print("There was a problem with ticket called " + name)
	continue


			

















