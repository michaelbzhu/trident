from flask import Flask
from flask_cors import CORS
from google.cloud import bigquery
import pdb
import json
app = Flask(__name__)
CORS(app)
client = bigquery.Client()
initial_query = """
    SELECT (address, follow_profile_id)
    FROM lens-public-data.polygon.public_follower
    WHERE follow_profile_id=\'{}\' AND is_finalised_on_chain=TRUE
"""
profile_query = """
    SELECT (profile_id,owned_by)
    FROM lens-public-data.polygon.public_profile
    WHERE owned_by IN ({})
"""
adjacency_query = """
	SELECT (address, follow_profile_id)
    FROM lens-public-data.polygon.public_follower
    WHERE address in ({}) AND follow_profile_id IN ({})
"""
@app.route("/<profile_id>")
def lens_data(profile_id):
	query_job = client.query(initial_query.format(profile_id))
	#print([row[0] for row in query_job])
	addresses = [row[0]['_field_1'] for row in query_job]
	address_query_string = ",".join(["\'{}\'".format(addy) for addy in addresses])
	print("Profile Query: {}".format(profile_query.format(address_query_string)))
	profile_rows = client.query(profile_query.format(address_query_string))
	profileToAddress = {}
	profiles = []
	for row in profile_rows:
		profileToAddress[row[0]['_field_1']] = row[0]['_field_2']
		profiles.append(row[0]['_field_1'])
	profiles = list(set(profiles))
	print("Profiles: ",profiles)
	adjacency_query_strings = address_query_string, ",".join(["\'{}\'".format(prof) for prof in profiles])
	print("Adjacency Query: {}".format(adjacency_query.format(*adjacency_query_strings)))
	adjacencies = client.query(adjacency_query.format(*adjacency_query_strings))
	edges = []
	for row in adjacencies:
		if row[0]['_field_1']!=profileToAddress[row[0]['_field_2']] and row[0]['_field_1']:
			edges.append((row[0]['_field_1'], profileToAddress[row[0]['_field_2']]))


	with open('/Users/rishabhkrishnan/addresses_gotten.json', 'rb') as scores_file:
		scores = json.load(scores_file)

	nodes = [{'address': address, 'value': scores.get(address,0), 'profiles':[k for k,v in profileToAddress.items() if v==address]} for address in addresses ]
	return {'nodes': nodes, 'edges': edges}




    