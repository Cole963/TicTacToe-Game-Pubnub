from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import random
import hashlib
import json
import ast
import itertools

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-835b7a0a-b67e-4d40-a4ea-b06843075ea2'
pnconfig.publish_key = 'pub-c-da63fca1-e8a9-4f63-9ac0-eee3a2daff6d'
pnconfig.user_id = "Bob"
pubnub = PubNub(pnconfig)
channel = 'Channel-mqdvd3hi4'
gridArray = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
bobArray = []
aliceArray = []
finalGrid = ""

def my_publish_callback(envelope, status):
	# Check whether request successfully completed or not
	if not status.is_error():
		pass  # Message successfully published to specified channel.
	else:
		pass  # Handle message publish error. Check 'category' property to find out possible issue
		# because of which request did fail.
		# Request can be resent using: [status retry];

class MySubscribeCallback(SubscribeCallback):
	gridArray = []
	def __init__(self):
		#global gridArray
		pass
	def presence(self, pubnub, presence):
		pass  # handle incoming presence data

	def status(self, pubnub, status):
		if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
			pass  # This event happens when radio / connectivity is lost

		elif status.category == PNStatusCategory.PNConnectedCategory:
			# Connect event. You can do stuff like publish, and know you'll get it.
			# Or just use the connected event to confirm you are subscribed for
			# UI / internal notifications, etc
			#pubnub.publish().channel('Channel-mqdvd3hi4').message('Hello').pn_async(my_publish_callback)
			print("Bob Connected\n")
		elif status.category == PNStatusCategory.PNReconnectedCategory:
		    pass
		    # Happens as part of our regular operation. This event happens when
		    # radio / connectivity is lost, then regained.
		elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
			pass
			# Handle message decryption error. Probably client configured to
			# encrypt messages and on live data feed it received plain text.

	def message(self, pubnub, message):
		if "GAME OVER" in message.message:
			bobDict = dict.fromkeys(bobArray, "O")
			aliceDict = dict.fromkeys(aliceArray, "X")
			mergedDict = {**bobDict, **aliceDict}


			print("GAME OVER!!!\n")
			finalGrid = "\t{}\t|\t{}\t|\t{}\t\n\t{}\t|\t{}\t|\t{}\t\n\t{}\t|\t{}\t|\t{}\t\n".format(mergedDict.get("A"), mergedDict.get("B"), mergedDict.get("C"), mergedDict.get("D"), mergedDict.get("E") ,mergedDict.get("F"), mergedDict.get("G"), mergedDict.get("H"), mergedDict.get("I"))
			print(finalGrid)

		else:
			msgJson = ast.literal_eval(message.message)
			if(type(msgJson) is dict and "TxID" in msgJson):
				if(msgJson.get("Transaction")[0] == "Alice"):
					
					TxID = msgJson.get("TxID")
					hashvalue = msgJson.get("Hash")
					grid = msgJson.get("Transaction")[1]
					
					#verify validity of received block
					fr = open("block" + str(TxID - 1) + ".json", "r")
					preblk = fr.read()
					fr.close()

					preblkHash = hashlib.sha256(preblk.encode()).hexdigest()

					# Verified
					if(hashvalue == preblkHash):
						print("block" + str(TxID) + " valid")
						
						# Save the block to json
						fw = open("block" + str(TxID) + ".json", "w+")
						fw.write(message.message)
						fw.close()
						
						# Remove used gridspace from gridArray
						gridArray.remove(grid)
						aliceArray.append(grid)
						aliceArray.sort()

						# Checks if Alice's move wins her the game
						aliceStr = ""
						for i in aliceArray:
							aliceStr += i
						alice = []
						for s in itertools.permutations(aliceStr):
							alice.append(''.join(s))

						# Check if grid is empty, ends the game if it is
						if not gridArray:
							end = "\nGAME OVER!!!"

							pubnub.publish().channel(channel).message(end).pn_async(my_publish_callback)	
								
						else:
							# Bob takes his turn
							hashvalue = hashlib.sha256((message.message).encode()).hexdigest()
							nonce = 0

							# RNG to decide which grid to take
							grid = random.choice(gridArray)
							gridArray.remove(grid)
							bobArray.append(grid)
							bobArray.sort()
							print(str("\n=================\nBob takes the " + grid + " grid\n=================\n"))

							transaction = [pnconfig.user_id, grid]
							
							cond = True
							while(cond):
								blockx = json.dumps({"TxID": TxID+1, "Hash": hashvalue, "Nonce": nonce, "Transaction": transaction}, sort_keys = False, indent = 4, separators = (',', ': '))	

									
								hashout = hashlib.sha256(blockx.encode()).hexdigest()
								if int(hashout, 16) <= int("000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16):
									cond = False

								nonce += 1
							fw = open("block" + str(TxID+1) + ".json", "w+")
							fw.write(blockx)
							fw.close()
							
							pubnub.publish().channel(channel).message(blockx).pn_async(my_publish_callback)	
							
					else:
						print("block" + str(TxID) + " invalid")
						exit()
			else:
				print("GAME OVER!!!\n")
				finalGrid = "\t{}\t|\t{}\t|\t{}\t\n\t{}\t|\t{}\t|\t{}\t\n\t{}\t|\t{}\t|\t{}\t\n".format(msgJson.get("A"), msgJson.get("B"), msgJson.get("C"), msgJson.get("D"), msgJson.get("E") ,msgJson.get("F"), msgJson.get("G"), msgJson.get("H"), msgJson.get("I"))
				print(finalGrid)

			
			
pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels(channel).execute()


